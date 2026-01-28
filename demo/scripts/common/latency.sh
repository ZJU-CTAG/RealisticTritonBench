#!/usr/bin/env bash
set -e

######################################
# Parse arguments
######################################

if [ "$#" -ne 8 ]; then
  echo "Usage: $0 <MODEL> <TP> <PORT> <INPUT_LEN> <OUTPUT_LEN> <NUM_PROMPTS> <TASK_ID> <TEST_ID>"
  echo "Example:"
  echo "  $0 meta-llama/Meta-Llama-3-8B 8 8000 100 100 8 0 3"
  exit 1
fi

MODEL="$1"
TP="$2"
PORT="$3"
INPUT_LEN="$4"
OUTPUT_LEN="$5"
NUM_PROMPTS="$6"
TASK_ID="$7"
TEST_ID="$8"

######################################
# Config
######################################

SERVE_LOG="logs/task_${TASK_ID}_serve_test_${TEST_ID}.log"
LATENCY_LOG="logs/task_${TASK_ID}_latency_test_${TEST_ID}.log"

mkdir -p "$(dirname "$LATENCY_LOG")"
mkdir -p "$(dirname "$SERVE_LOG")"

######################################
# Start vLLM serve
######################################

echo "==> Starting vLLM serve"
echo "    MODEL=$MODEL"
echo "    TP=$TP"
echo "    PORT=$PORT"

nohup vllm serve "$MODEL" \
  --tensor-parallel-size "$TP" \
  --gpu-memory-utilization 0.9 \
  --port "$PORT" \
  > "$SERVE_LOG" 2>&1 &

SERVE_PID=$!

######################################
# Wait for server
######################################

echo "==> Waiting for vLLM server to be ready..."

for i in {1..30}; do
  if curl -s "http://127.0.0.1:${PORT}/v1/models" >/dev/null; then
    echo "==> vLLM server is ready."
    break
  fi
  sleep 2
done

if ! kill -0 "$SERVE_PID" 2>/dev/null; then
  echo "❌ vLLM serve crashed. Check ${SERVE_LOG}"
  exit 1
fi

######################################
# Run latency benchmark
######################################

echo "==> Running latency benchmark..."

vllm bench serve \
    --input_len "${INPUT_LEN}" \
    --output_len "${OUTPUT_LEN}" \
    --num-prompts "${NUM_PROMPTS}" \
  > "$LATENCY_LOG"

######################################
# Cleanup
######################################

echo "==> Stopping vLLM serve..."
kill "$SERVE_PID"

echo "==> Done."
echo "Logs:"
echo "  Serve log:   $SERVE_LOG"
echo "  Latency log: $LATENCY_LOG"