#!/bin/bash
# start_vllm.sh

export CUDA_VISIBLE_DEVICES=2,3
export PYTORCH_ALLOC_CONF=expandable_segments:True

# ==== LoRA 开关 (vLLM 0.6+ 推荐用此环境变量启用 bias 支持,视训练配置而定) ====
# export VLLM_ALLOW_LONG_MAX_MODEL_LEN=1   # 如需放开长度限制再开

python -m vllm.entrypoints.openai.api_server \
    --model /root/autodl-tmp/fhx/models/Llama-3.1-8B-Instruct \
    --served-model-name llama3.1-8b-instruct \
    --tensor-parallel-size 2 \
    --enforce-eager \
    --max-model-len 4096 \
    --port 8000 \
    \
    --enable-lora \
    --lora-modules \
        ift-lora=/root/autodl-tmp/fhx/saves/llama3-crypto-ift \
        sentiment-lora=/root/autodl-tmp/fhx/saves/llama3-crypto-sentiment \
    --max-lora-rank 16 \
    --max-loras 2 \
    --max-cpu-loras 4 \
    --max-lora-extra-vocab-size 0