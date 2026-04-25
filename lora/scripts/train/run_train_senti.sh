#!/bin/bash
set -e

PROJECT_ROOT="/root/autodl-tmp/fhx/crypto_lora"
cd "$PROJECT_ROOT"

mkdir -p logs

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/train_sentiment_${TIMESTAMP}.log"

export HF_ENDPOINT=https://hf-mirror.com
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo "==================================================="
echo "开始训练 - 双卡 DDP 模式"
echo "配置:   configs/llama3.1_lora_sentiment.yaml"
echo "日志:   $LOG_FILE"
echo "TB:     自动写入 output_dir/runs/ (即 checkpoints/stage1_ift_1/runs/)"
echo "==================================================="

nohup env CUDA_VISIBLE_DEVICES=2,3 \
    llamafactory-cli train configs/llama3.1_lora_sentiment.yaml \
    > "$LOG_FILE" 2>&1 &

TRAIN_PID=$!
echo "$TRAIN_PID" > logs/train_sentiment.pid

echo "✅ 训练已在后台启动,PID=$TRAIN_PID"
echo ""
echo "监控命令:"
echo "  日志:         tail -f $LOG_FILE"
echo "  GPU:          watch -n 2 nvidia-smi"
echo "  TensorBoard:  bash scripts/monitor/run_tensorboard.sh"
echo "  停止训练:     kill \$(cat logs/train_sentiment.pid)"