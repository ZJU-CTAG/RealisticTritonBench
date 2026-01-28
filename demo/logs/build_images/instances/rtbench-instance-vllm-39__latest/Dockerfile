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
        --base_commit 029c71de11bc3bcf84a1b3cf9d91e79ab6949799 \
        --head_commit d456232bd9f74039379bfe8b5f7c5d469a2a8d37 \
        --pull_number 7386 \
        --specs /workspace/specs.json 

WORKDIR /workspace/vllm-project/vllm

