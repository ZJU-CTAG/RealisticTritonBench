
FROM --platform=linux/x86_64 rtbench-base:latest

WORKDIR /workspace

RUN git clone -o origin https://github.com/vllm-project/vllm.git vllm-project/vllm && \
    chmod -R 777 vllm-project/vllm && \
    cd vllm-project/vllm
