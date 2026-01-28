#!/usr/bin/env bash
set -e

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <PORT>"
  exit 1
fi

PORT="$1"
PID_FILE="/tmp/vllm_${PORT}.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "[ERROR] PID file not found: $PID_FILE"
  echo "Is vLLM running on port $PORT?"
  exit 1
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
  echo "[WARN] Process $PID is not running"
  rm -f "$PID_FILE"
  exit 0
fi

echo "[INFO] Stopping vLLM (PID=$PID)"
kill "$PID"

# 等待进程退出
for i in {1..5}; do
  if kill -0 "$PID" 2>/dev/null; then
    sleep 1
  else
    echo "[INFO] vLLM stopped"
    rm -f "$PID_FILE"
    exit 0
  fi
done

echo "[WARN] vLLM did not exit gracefully, killing"
kill -9 "$PID"
rm -f "$PID_FILE"