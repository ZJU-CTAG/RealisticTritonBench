# bin/bash
set -euo pipefail

export HF_ENDPOINT="https://hf-mirror.com"
export HF_TOKEN="YOUR_HF_TOKEN"

download() {
  local model="$1"
  echo "--------------------------------"
  echo "Downloading model: ${model}"
  echo "--------------------------------"
  huggingface-cli download --token "$HF_TOKEN" --resume-download "$model"
  echo
}


download "Qwen/Qwen3-VL-4B-Instruct"
download "BAAI/bge-m3"
download "deepseek-ai/DeepSeek-V2-Lite-Chat"
download "RedHatAI/Qwen2-7B-Instruct-quantized.w8a8"
download "state-spaces/mamba-2.8b-hf"
download "RedHatAI/Phi-3-medium-128k-instruct-quantized.w8a8"
download "Qwen/Qwen2-7B-Instruct-AWQ"
download "meta-llama/Meta-Llama-3-8B"
download "yard1/llama-2-7b-sql-lora-test"
download "LevinZheng/gpt-oss-20b-lora-adapter"
download "openai/gpt-oss-20b"
download "Qwen/Qwen3-30B-A3B-FP8"
download "Qwen/Qwen2.5-7B-Instruct-AWQ"
download "meta-llama/Llama-2-7b-hf"
download "Qwen/Qwen3-VL-7B-Instruct"
download "ibm-granite/granite-4.0-tiny-preview"
download "ibm-ai-platform/Bamba-9B-v2"
download "Qwen/Qwen3-Next-80B-A3B-Instruct"
download "meta-llama/Llama-3.1-8B-Instruct"

