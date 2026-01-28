#!/usr/bin/env bash
set -e

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <MODEL> <TP_SIZE> <GPU_MEMORY_UTIL> <PORT> <LOG_PATH>"
  echo ""
  echo "Example:"
  echo "  $0 /path/to/model 8 0.9 9010 ./log/vllm.log"
  exit 1
fi

MODEL="$1"
TP_SIZE="$2"
GPU_MEMORY_UTIL="$3"
PORT="$4"
LOG_PATH="$5"

######################################
# Prepare log directory
######################################
LOG_DIR="$(dirname "$LOG_PATH")"
mkdir -p "$LOG_DIR"

PID_FILE="/tmp/vllm_${PORT}.pid"

######################################
# Launch vLLM
######################################
echo "[INFO] Starting vLLM server"
echo "  MODEL              = $MODEL"
echo "  TP_SIZE            = $TP_SIZE"
echo "  GPU_MEMORY_UTIL    = $GPU_MEMORY_UTIL"
echo "  PORT               = $PORT"
echo "  LOG_PATH           = $LOG_PATH"

nohup vllm serve "$MODEL" \
  --tensor-parallel-size "$TP_SIZE" \
  --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
  --port "$PORT" \
  > "$LOG_PATH" 2>&1 &

PID=$!
echo "$PID" > "$PID_FILE"

echo "[INFO] vLLM started"
echo "  PID      = $PID"
echo "  PID_FILE = $PID_FILE"