#!/bin/bash

PROJECT_ROOT="/root/autodl-tmp/fhx/crypto_lora"
cd "$PROJECT_ROOT"

echo "==================================================="
echo "启动 TensorBoard"
echo "扫描目录: $PROJECT_ROOT/checkpoints"
echo "(自动识别所有 */runs/ 子目录)"
echo "端口:     6006"
echo "==================================================="
echo ""
echo "访问方式:"
echo "  1. AutoDL 自带端口映射(在实例控制台找 6006 公网 URL)"
echo "  2. 本地 SSH 转发:"
echo "     ssh -L 6006:localhost:6006 -p <SSH端口> root@<实例IP>"
echo "     然后访问 http://localhost:6006"
echo ""

tensorboard --logdir="$PROJECT_ROOT/checkpoints" \
    --host=0.0.0.0 \
    --port=6006