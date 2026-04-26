# LoRA 环境搭建

## 前置要求
- **操作系统**: Linux (推荐 Ubuntu 20.04/22.04，服务器环境)
- [cite_start]**Python**: $\ge 3.10$ [cite: 566]
- [cite_start]**CUDA**: $\ge 12.1$ (适配最新的 PyTorch 和 FlashAttention) [cite: 567]
- [cite_start]**GPU**: 单卡或多卡 RTX 3090/4090 (至少 24GB 显存以支持 Llama-3-8B 的 LoRA 微调) [cite: 568]
- **网络**: 需确保服务器能流畅访问 Hugging Face (用于下载基座模型和开源数据集)

## 安装步骤
建议在你的 Conda 环境或标准的 venv 虚拟环境中进行隔离安装，防止与系统其他依赖冲突。

```bash
# 1. 进入 lora 模块目录
[cite_start]cd lora [cite: 571]

# 2. 创建并激活虚拟环境 (Harness init.sh 标准操作)
[cite_start]python -m venv .venv [cite: 572]
[cite_start]source .venv/bin/activate [cite: 573]

# (可选) 如果你使用 AutoDL 或自建服务器，更推荐使用 Conda:
# conda create -n cryptopulse_lora python=3.10 -y
# conda activate cryptopulse_lora

# 3. 安装核心依赖
# 安装 PyTorch (请根据服务器实际 CUDA 版本调整)
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)

# 4. 安装 LLaMA-Factory 及加速库
[cite_start]pip install -r requirements.txt [cite: 575]
# 包含加速算子 (极大地降低显存占用并提升训练速度)
pip install flash-attn --no-build-isolation
pip install deepspeed