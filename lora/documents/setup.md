# LoRA Setup

## Prerequisites

- **Operating system**: Linux (Ubuntu 20.04/22.04 recommended, server environment)
- **Python**: `>= 3.10` [cite: 566]
- **CUDA**: `>= 12.1` (compatible with recent PyTorch and FlashAttention) [cite: 567]
- **GPU**: single or multi-GPU RTX 3090/4090 (at least 24GB VRAM to support LoRA fine-tuning on Llama-3-8B) [cite: 568]
- **Network**: the server should have stable access to Hugging Face for downloading the base model and open datasets

## Installation

Use an isolated Conda or standard `venv` environment to avoid conflicts with other system dependencies.

```bash
# 1. Enter the lora module directory
cd lora

# 2. Create and activate a virtual environment (standard harness init.sh flow)
python -m venv .venv
source .venv/bin/activate

# Optional: if you use AutoDL or your own server, Conda is also a good choice:
# conda create -n cryptopulse_lora python=3.10 -y
# conda activate cryptopulse_lora

# 3. Install core dependencies
# Install PyTorch (adjust for the actual CUDA version on your server)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Install LLaMA-Factory and acceleration libraries
pip install -r requirements.txt

# Includes acceleration operators that significantly reduce VRAM use and improve training speed
pip install flash-attn --no-build-isolation
pip install deepspeed
```
