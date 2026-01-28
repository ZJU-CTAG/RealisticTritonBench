# syntax=docker/dockerfile:1.4
FROM --platform=linux/x86_64 rtbench-vllm:latest

WORKDIR /workspace

ENV PATH=/opt/miniconda3/bin:$PATH
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH


RUN conda create -n testbed python=3.10 

COPY replace_funcs.py /workspace/replace_funcs.py
COPY specs.json /workspace/specs.json


ARG PIP_CACHE_DIR=/root/.cache/pip

RUN mkdir -p $PIP_CACHE_DIR

# 在同一条 RUN 里调用环境的 Python
RUN cd vllm-project/vllm && \
    /opt/miniconda3/envs/testbed/bin/python /workspace/replace_funcs.py \
        --repo /workspace/vllm-project/vllm \
        --base_commit aabcd2cae305c08c396889be9c6930840b1adead \
        --head_commit 0efb66907b4b25466874ee3b289f240a0c584ea9 \
        --pull_number 16828 \
        --specs /workspace/specs.json 

WORKDIR /workspace/vllm-project/vllm

