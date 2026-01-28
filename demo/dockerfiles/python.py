
# DOCKERFILE - Python Base Image
_DOCKERFILE_BASE_PY = r"""
FROM --platform={platform} nvidia/cuda:12.0.1-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt update && apt install -y \
wget \
git \
build-essential \
libffi-dev \
libtiff-dev \
python3 \
python3-pip \
python-is-python3 \
jq \
curl \
locales \
locales-all \
tzdata \
&& rm -rf /var/lib/apt/lists/*

# Download and install conda
RUN wget 'https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-{conda_arch}.sh' -O miniconda.sh && \ 
    bash miniconda.sh -b -p /opt/miniconda3 && \
    rm miniconda.sh
# Add conda to PATH
ENV PATH=/opt/miniconda3/bin:$PATH
# Add conda to shell startup scripts like .bashrc (DO NOT REMOVE THIS)
RUN conda init --all && \
    conda config --append channels conda-forge 

COPY condarc /root/.condarc

RUN conda clean -i

WORKDIR /workspace

"""

# DOCKERFILE - REPO IMAGES
_DOCKERFILE_REPO_VLLM_PY = r"""
FROM --platform={platform} {base_image_name}

WORKDIR /workspace

RUN git clone -o origin {origin_url} {repo} && \
    chmod -R 777 {repo} && \
    cd {repo}
"""

_DOCKERFILE_REPO_SGLANG_PY = r"""
FROM --platform={platform} {base_image_name}
"""


# DOCKERFILE - INSTANCE IMAGES
_DOCKERFILE_INSTANCE_PY = r"""# syntax=docker/dockerfile:1.4
FROM --platform={platform} {repo_image_name}

WORKDIR /workspace

ENV PATH=/opt/miniconda3/bin:$PATH
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH


RUN conda create -n testbed python={python_version} 

COPY replace_funcs.py /workspace/replace_funcs.py
COPY specs.json /workspace/specs.json


ARG PIP_CACHE_DIR=/root/.cache/pip

RUN mkdir -p $PIP_CACHE_DIR

# 在同一条 RUN 里调用环境的 Python
RUN cd {repo} && \
    /opt/miniconda3/envs/testbed/bin/python /workspace/replace_funcs.py \
        --repo /workspace/{repo} \
        --base_commit {base_commit} \
        --head_commit {head_commit} \
        --pull_number {pull_number} \
        --specs /workspace/specs.json 

WORKDIR /workspace/{repo}

"""
