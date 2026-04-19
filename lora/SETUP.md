# LoRA 环境搭建

## 前置要求

- Linux（推荐 Ubuntu 20.04/22.04）
- Python >= 3.10
- CUDA >= 12.1
- 单卡或多卡 RTX 3090 / 4090（至少 24GB 显存）
- 能访问 Hugging Face

## 安装步骤

```bash
cd lora
python -m venv .venv
source .venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
pip install flash-attn --no-build-isolation
pip install deepspeed
```

如果使用 Conda，也可以使用独立 Conda 环境替代 `venv`。

## 环境变量

复制模板后按需填写：

```bash
cp .env.example .env
```

建议至少配置：

```env
BASE_MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
DATA_ROOT=./data
CHECKPOINT_ROOT=./checkpoints
USE_MOCK=true
```

## 运行建议

- 数据准备脚本：`python -m src.data_prep.build_dataset`
- 训练脚本：`bash scripts/run_train_ift.sh`
- 第二阶段训练：`bash scripts/run_train_sentiment.sh`
- 权重合并：`bash scripts/merge_weights.sh`

## 大文件约束

- `data/` 和 `checkpoints/` 不应提交到 git
- 大模型与数据集应通过外部存储或 Hugging Face 管理

