"""
python scripts/evaluation/eva_ift.py \
    --base_model /root/autodl-tmp/fhx/models/Llama-3.1-8B-Instruct \
    --lora_adapter /root/autodl-tmp/fhx/crypto_lora/checkpoints/stage1_ift_1 \
    --test_file data/ift/test_set.json \
    --output_dir evaluation_results/stage1_ift \
    --max_samples 20

LoRA 微调前后对比评估
对比项:
  - Base Model (原始 Llama-3.1-8B-Instruct)
  - LoRA Model (微调后的模型)

评估指标:
  - Perplexity (PPL): 模型对参考答案的困惑度
  - ROUGE-L: 文本重合度
  - BLEU-4: n-gram 精度
  - BERTScore: 语义相似度
  - 关键词命中率: 金融专业度

输出:
  - evaluation_results.json: 所有样本的详细结果
  - evaluation_summary.json: 统计摘要
  - evaluation_report.md: 可读的 markdown 报告
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import List, Dict

import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


# ==================== 评估指标实现 ====================

def compute_perplexity(model, tokenizer, prompt: str, reference: str, device: str) -> float:
    """
    计算模型在参考答案上的 perplexity
    PPL 越低,说明模型越"认同"这个答案
    """
    # 拼接 prompt 和 reference
    full_text = prompt + reference
    
    # 分别 tokenize 以便计算 reference 部分的 loss
    prompt_ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
    full_ids = tokenizer(full_text, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
    
    # 构造 labels: prompt 部分设为 -100 (不计入 loss), reference 部分用真实 token
    labels = full_ids.clone()
    labels[:, :prompt_ids.shape[1]] = -100
    
    with torch.no_grad():
        outputs = model(full_ids, labels=labels)
        loss = outputs.loss.item()
    
    ppl = np.exp(loss)
    return ppl


def compute_rouge_bleu(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """计算 ROUGE-L 和 BLEU-4"""
    from rouge_score import rouge_scorer
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    smoothing = SmoothingFunction().method1
    
    rouge_scores = []
    bleu_scores = []
    
    for pred, ref in zip(predictions, references):
        # ROUGE-L
        rouge = scorer.score(ref, pred)["rougeL"].fmeasure
        rouge_scores.append(rouge)
        
        # BLEU-4
        ref_tokens = ref.split()
        pred_tokens = pred.split()
        if len(pred_tokens) == 0:
            bleu_scores.append(0.0)
        else:
            bleu = sentence_bleu(
                [ref_tokens], pred_tokens,
                weights=(0.25, 0.25, 0.25, 0.25),
                smoothing_function=smoothing,
            )
            bleu_scores.append(bleu)
    
    return {
        "rouge_l": float(np.mean(rouge_scores)),
        "bleu_4": float(np.mean(bleu_scores)),
    }


def compute_bertscore(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """计算 BERTScore (语义相似度)"""
    from bert_score import score as bert_score_fn
    
    P, R, F1 = bert_score_fn(
        predictions, references,
        lang="en",
        model_type="roberta-large",
        verbose=False,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    
    return {
        "bertscore_p": float(P.mean()),
        "bertscore_r": float(R.mean()),
        "bertscore_f1": float(F1.mean()),
    }


def compute_keyword_hit_rate(predictions: List[str]) -> float:
    """
    计算金融/加密关键词命中率
    衡量模型是否在用"专业语言"回答
    """
    FINANCE_KEYWORDS = {
        # 基础金融
        "interest rate", "yield", "volatility", "liquidity", "equity",
        "asset", "derivative", "portfolio", "hedge", "leverage",
        "return", "risk", "dividend", "capital",
        # 加密
        "blockchain", "cryptocurrency", "crypto", "bitcoin", "ethereum",
        "token", "smart contract", "defi", "nft", "stablecoin",
        "mining", "staking", "wallet", "exchange",
        # 市场
        "bull market", "bear market", "market cap", "trading volume",
        # 分析
        "analysis", "valuation", "fundamental", "technical",
    }
    
    hit_counts = []
    for pred in predictions:
        pred_lower = pred.lower()
        count = sum(1 for kw in FINANCE_KEYWORDS if kw in pred_lower)
        hit_counts.append(count)
    
    # 平均每条回答命中的关键词数
    return float(np.mean(hit_counts))


# ==================== 模型加载与推理 ====================

def load_both_models(base_path: str, adapter_path: str):
    """
    同时加载 Base Model 和 LoRA Model 到两张不同的 GPU
    - Base:  cuda:0
    - LoRA:  cuda:1
    """
    print(f"[INFO] 加载 Base Model 到 cuda:0: {base_path}")
    tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_path,
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",
        trust_remote_code=True,
    )
    base_model.eval()
    
    print(f"[INFO] 加载 LoRA 到 cuda:1: {adapter_path}")
    # 再加载一次 base 作为 LoRA 的底座,放到 cuda:1
    lora_base = AutoModelForCausalLM.from_pretrained(
        base_path,
        torch_dtype=torch.bfloat16,
        device_map="cuda:1",
        trust_remote_code=True,
    )
    lora_model = PeftModel.from_pretrained(lora_base, adapter_path)
    lora_model.eval()
    
    return base_model, lora_model, tokenizer


def format_prompt_llama3(instruction: str, input_text: str, tokenizer) -> str:
    """构造 Llama-3 chat 格式的 prompt"""
    user_content = instruction
    if input_text.strip():
        user_content += f"\n\n{input_text}"
    
    messages = [{"role": "user", "content": user_content}]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    return prompt


def generate_response(model, tokenizer, prompt: str, device: str,
                      max_new_tokens: int = 512) -> str:
    """生成回答"""
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,                # 贪婪解码,保证可复现
            temperature=1.0,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # 只保留新生成的部分
    generated = outputs[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(generated, skip_special_tokens=True)
    return response.strip()


# ==================== 主评估流程 ====================

def evaluate_model(model, tokenizer, test_data, device, model_name):
    """只做推理和 PPL 计算,不算 BERTScore"""
    results = []
    ppls = []
    
    print(f"\n[INFO] 开始推理: {model_name}")
    for item in tqdm(test_data, desc=f"Eval {model_name}"):
        instruction = item["instruction"]
        input_text = item.get("input", "")
        reference = item["output"]
        
        prompt = format_prompt_llama3(instruction, input_text, tokenizer)
        
        # 1. 生成回答
        try:
            prediction = generate_response(model, tokenizer, prompt, device)
        except Exception as e:
            print(f"[WARN] 生成失败: {e}")
            prediction = ""
        
        # 2. 计算 perplexity
        try:
            ppl = compute_perplexity(model, tokenizer, prompt, reference, device)
        except Exception as e:
            print(f"[WARN] PPL 计算失败: {e}")
            ppl = float("inf")
        ppls.append(ppl)
        
        results.append({
            "instruction": instruction,
            "input": input_text,
            "reference": reference,
            "prediction": prediction,
            "ppl": ppl,
        })
    
    # 只返回推理结果,不算 BERTScore
    predictions = [r["prediction"] for r in results]
    references = [r["reference"] for r in results]
    valid_ppls = [p for p in ppls if p != float("inf")]
    
    return {
        "results": results,
        "predictions": predictions,
        "references": references,
        "model_name": model_name,
        "perplexity_mean": float(np.mean(valid_ppls)) if valid_ppls else float("inf"),
        "perplexity_median": float(np.median(valid_ppls)) if valid_ppls else float("inf"),
    }


def compute_all_metrics(eval_result):
    """所有大模型释放后,再算 BERTScore 等重指标"""
    print(f"\n[INFO] 计算 {eval_result['model_name']} 的语言指标...")
    
    predictions = eval_result["predictions"]
    references = eval_result["references"]
    
    rouge_bleu = compute_rouge_bleu(predictions, references)
    bertscore = compute_bertscore(predictions, references)
    kw_hit_rate = compute_keyword_hit_rate(predictions)
    
    summary = {
        "model_name": eval_result["model_name"],
        "num_samples": len(eval_result["results"]),
        "perplexity": eval_result["perplexity_mean"],
        "perplexity_median": eval_result["perplexity_median"],
        **rouge_bleu,
        **bertscore,
        "finance_keyword_hits_per_response": kw_hit_rate,
    }
    
    return {"summary": summary, "results": eval_result["results"]}


def generate_report(base_summary: Dict, lora_summary: Dict, output_path: str):
    """生成 markdown 报告"""
    
    def improvement(base_val, lora_val, higher_is_better=True):
        if base_val == 0 or base_val == float("inf"):
            return "N/A"
        delta = lora_val - base_val
        pct = delta / abs(base_val) * 100
        sign = "+" if delta > 0 else ""
        
        if higher_is_better:
            emoji = "✅" if delta > 0 else "❌"
        else:
            emoji = "✅" if delta < 0 else "❌"
        
        return f"{sign}{pct:.2f}% {emoji}"
    
    report = f"""# LoRA 微调前后对比评估报告

## 测试集: {base_summary["num_samples"]} 条样本

## 核心指标对比

| 指标 | Base Model | LoRA Model | 提升 | 越高越好? |
|---|---|---|---|---|
| **Perplexity (均值)** | {base_summary["perplexity"]:.4f} | {lora_summary["perplexity"]:.4f} | {improvement(base_summary["perplexity"], lora_summary["perplexity"], higher_is_better=False)} | ❌ 越低越好 |
| **Perplexity (中位数)** | {base_summary["perplexity_median"]:.4f} | {lora_summary["perplexity_median"]:.4f} | {improvement(base_summary["perplexity_median"], lora_summary["perplexity_median"], higher_is_better=False)} | ❌ 越低越好 |
| **ROUGE-L** | {base_summary["rouge_l"]:.4f} | {lora_summary["rouge_l"]:.4f} | {improvement(base_summary["rouge_l"], lora_summary["rouge_l"])} | ✅ 越高越好 |
| **BLEU-4** | {base_summary["bleu_4"]:.4f} | {lora_summary["bleu_4"]:.4f} | {improvement(base_summary["bleu_4"], lora_summary["bleu_4"])} | ✅ 越高越好 |
| **BERTScore F1** | {base_summary["bertscore_f1"]:.4f} | {lora_summary["bertscore_f1"]:.4f} | {improvement(base_summary["bertscore_f1"], lora_summary["bertscore_f1"])} | ✅ 越高越好 |
| **BERTScore Precision** | {base_summary["bertscore_p"]:.4f} | {lora_summary["bertscore_p"]:.4f} | {improvement(base_summary["bertscore_p"], lora_summary["bertscore_p"])} | ✅ 越高越好 |
| **BERTScore Recall** | {base_summary["bertscore_r"]:.4f} | {lora_summary["bertscore_r"]:.4f} | {improvement(base_summary["bertscore_r"], lora_summary["bertscore_r"])} | ✅ 越高越好 |
| **金融关键词/回答** | {base_summary["finance_keyword_hits_per_response"]:.2f} | {lora_summary["finance_keyword_hits_per_response"]:.2f} | {improvement(base_summary["finance_keyword_hits_per_response"], lora_summary["finance_keyword_hits_per_response"])} | ✅ 越高越好 |

## 指标解读

- **Perplexity (PPL)**: 模型对参考答案的困惑度。PPL 降低说明 LoRA 模型对金融领域答案更"熟悉"。
- **ROUGE-L**: 衡量回答与参考答案的最长公共子序列。反映文本层面的相似度。
- **BLEU-4**: 基于 4-gram 的翻译评估指标。反映 n-gram 重合度。
- **BERTScore**: 用预训练 BERT 做的语义相似度。对同义改写友好。
- **金融关键词命中**: 回答中出现的金融/加密专业术语数量。反映"专业度"。

## 建议

1. 如果 **ROUGE-L 和 BERTScore 同时提升**,说明 LoRA 在内容层面和语义层面都有改进。
2. 如果 **只有 PPL 降低但 ROUGE 不升**,可能是 LoRA 学到了 tokenizer 偏好但不是真的学到了知识。
3. **关键词命中率**反映专业度,如果大幅上升说明模型学会了"用金融语言回答"。
4. 建议对高 PPL 差距的样本做人工分析,看 LoRA 具体在哪些类型的问题上有优势。
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[INFO] 报告已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, required=True,
                        help="原始基座模型路径")
    parser.add_argument("--lora_adapter", type=str, required=True,
                        help="LoRA adapter 路径")
    parser.add_argument("--test_file", type=str, required=True,
                        help="测试集 JSON 文件 (alpaca 格式)")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="输出目录")
    parser.add_argument("--max_samples", type=int, default=-1,
                        help="最大样本数 (-1 = 全部)")
    # 注意: 移除了 --device 参数, 因为现在固定用 cuda:0 和 cuda:1
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载测试数据
    with open(args.test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    if args.max_samples > 0:
        test_data = test_data[:args.max_samples]
    print(f"[INFO] 测试集大小: {len(test_data)} 条")
    
    # ========== 一次性加载两个模型到两张卡 ==========
    base_model, lora_model, tokenizer = load_both_models(
        args.base_model, args.lora_adapter
    )
    
    # ========== 阶段 1: 推理 + PPL (两个模型并存) ==========
    # 只做推理和 PPL, 不算 BERTScore (避免显存叠加)
    base_raw = evaluate_model(
        base_model, tokenizer, test_data,
        device="cuda:0", model_name="Base"
    )
    
    lora_raw = evaluate_model(
        lora_model, tokenizer, test_data,
        device="cuda:1", model_name="LoRA"
    )
    
    # ========== 释放两个大模型, 给 BERTScore 腾显存 ==========
    print("\n[INFO] 推理完成, 释放大模型显存...")
    del base_model, lora_model
    torch.cuda.empty_cache()
    
    # ========== 阶段 2: 后处理计算 BERTScore/ROUGE/BLEU/关键词 ==========
    # 此时两张卡都空了, BERTScore 可以独占显存
    base_eval = compute_all_metrics(base_raw)
    lora_eval = compute_all_metrics(lora_raw)
    
    # ========== 保存详细结果 ==========
    with open(output_dir / "base_results.json", "w", encoding="utf-8") as f:
        json.dump(base_eval, f, ensure_ascii=False, indent=2)
    with open(output_dir / "lora_results.json", "w", encoding="utf-8") as f:
        json.dump(lora_eval, f, ensure_ascii=False, indent=2)
    
    # ========== 生成摘要和报告 ==========
    summary = {
        "base": base_eval["summary"],
        "lora": lora_eval["summary"],
    }
    with open(output_dir / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    generate_report(
        base_eval["summary"], lora_eval["summary"],
        output_dir / "evaluation_report.md"
    )
    
    # ========== 打印关键指标 ==========
    print("\n" + "=" * 60)
    print("评估完成! 关键指标:")
    print("=" * 60)
    print(f"{'指标':<36} {'Base':<12} {'LoRA':<12} {'变化':<10}")
    print("-" * 70)
    for key in ["perplexity", "rouge_l", "bleu_4", "bertscore_f1",
                "finance_keyword_hits_per_response"]:
        b = base_eval["summary"][key]
        l = lora_eval["summary"][key]
        if key == "perplexity":
            change = f"↓ {(b-l)/b*100:+.1f}%" if b > 0 else "N/A"
        else:
            change = f"↑ {(l-b)/b*100:+.1f}%" if b > 0 else "N/A"
        print(f"{key:<36} {b:<12.4f} {l:<12.4f} {change:<10}")
    
    print(f"\n结果保存到: {output_dir}")


if __name__ == "__main__":
    main()