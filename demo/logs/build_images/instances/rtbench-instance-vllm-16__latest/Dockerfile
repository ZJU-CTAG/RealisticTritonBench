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
        --base_commit 2f1e8e8f54032e38998e90427aedf649c0beee39 \
        --head_commit eb8126ef5a7c45c9e24d9d9570243c81eb75e1e7 \
        --pull_number 11698 \
        --specs /workspace/specs.json 

WORKDIR /workspace/vllm-project/vllm

