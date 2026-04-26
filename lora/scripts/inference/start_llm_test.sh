#!/bin/bash
# start_vllm.sh

export CUDA_VISIBLE_DEVICES=2,3
# 极其关键的环境变量：允许 PyTorch 动态扩展内存段以减少碎片化
export PYTORCH_ALLOC_CONF=expandable_segments:True 

python -m vllm.entrypoints.openai.api_server \
    --model /root/autodl-tmp/fhx/models/Llama-3.1-8B-Instruct \
    --served-model-name llama3.1-8b-instruct \
    --tensor-parallel-size 2 \
    --enforce-eager \
    --max-model-len 4096 \
    --port 8000