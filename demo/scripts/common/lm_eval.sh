#!/usr/bin/env bash
set -e

######################################
# Usage
######################################

if [ "$#" -ne 8 ]; then
  echo "Usage: $0 <pretrained> <tensor_parallel_size> <max_model_len> <gpu_memory_utilization> <tasks> <num_fewshot> <task_id> <test_id>"
  echo
  echo "Example:"
  echo "  $0 meta-llama/Meta-Llama-3-8B 8 2048 0.90 gsm8k 5 0 2 "
  exit 1
fi

######################################
# Parse arguments
######################################

PRETRAINED="$1"
TP="$2"
MAX_MODEL_LEN="$3"
GPU_MEM_UTIL="$4"
TASKS="$5"
NUM_FEWSHOT="$6"
TASK_ID="$7"
TEST_ID="$8"

######################################
# Config
######################################

BATCH_SIZE="auto"
DEVICE="cuda"

LOG_FILE="logs/task_${TASK_ID}_lm_eval_test_${TEST_ID}.log"

mkdir -p "$(dirname "$LOG_FILE")"

######################################
# Run lm_eval
######################################

echo "==> Running lm_eval"
echo "  Model:        $PRETRAINED"
echo "  TP:           $TP"
echo "  Max len:      $MAX_MODEL_LEN"
echo "  GPU mem util: $GPU_MEM_UTIL"
echo "  Tasks:        $TASKS"
echo "  Few-shot:     $NUM_FEWSHOT"
echo

lm_eval \
  --model vllm \
  --model_args "pretrained=${PRETRAINED},tensor_parallel_size=${TP},max_model_len=${MAX_MODEL_LEN},gpu_memory_utilization=${GPU_MEM_UTIL}" \
  --tasks "$TASKS" \
  --num_fewshot "$NUM_FEWSHOT" \
  --batch_size "$BATCH_SIZE" \
  --device "$DEVICE" \
  --trust_remote_code \
  | tee "$LOG_FILE"

echo
echo "==> lm_eval finished"