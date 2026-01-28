
FROM --platform=linux/x86_64 nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

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
RUN wget 'https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh' -O miniconda.sh && \ 
    bash miniconda.sh -b -p /opt/miniconda3 && \
    rm miniconda.sh
    
# Add conda to PATH
ENV PATH=/opt/miniconda3/bin:$PATH
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Add conda to shell startup scripts like .bashrc (DO NOT REMOVE THIS)
RUN conda init --all && \
    conda config --append channels conda-forge 

COPY condarc /root/.condarc

RUN conda clean -i

WORKDIR /workspace

