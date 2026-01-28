#!/usr/bin/env bash
set -e

######################################
# Parse arguments
######################################

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <PYTEST_CMD> <TASK_ID> <TEST_ID>"
  echo "Example:"
  echo "  $0 \"tests/samplers/test_logprobs.py\" 0 1"
  exit 1
fi

PYTEST_TARGET="$1"
TASK_ID="$2"
TEST_ID="$3"

######################################
# Config
######################################

PYTEST_LOG="logs/task_${TASK_ID}_unit_test_${TEST_ID}.log"

mkdir -p "$(dirname "$PYTEST_LOG")"

######################################
# Run pytest
######################################

echo "======================================"
echo "Running pytest"
echo "PYTEST_TARGET = $PYTEST_TARGET"
echo "TASK_ID       = $TASK_ID"
echo "TEST_ID       = $TEST_ID"
echo "LOG_DIR       = $LOG_DIR"
echo "======================================"

pytest "$PYTEST_TARGET" \
  > "$PYTEST_LOG" 2>&1

######################################
# Done
######################################

echo "======================================"
echo "Pytest finished successfully."
echo "Pytest log: $PYTEST_LOG"
echo "======================================"