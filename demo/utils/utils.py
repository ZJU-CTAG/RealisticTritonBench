import os 
import json
import subprocess

from datasets import load_dataset
from .constants import DATASET_LOCAL_PATH, HF_DATASET_NAME

def _load_dataset(local_path: str = DATASET_LOCAL_PATH):
    if local_path:
        with open(local_path, "r") as f:
            dataset = json.load(f)
    else:
        dataset = load_dataset(HF_DATASET_NAME, revision="main")["train"]
        dataset = dataset.to_list()

    return dataset

def _get_platform():
    """Get the current platform architecture for Docker builds."""
    try:
        arch = subprocess.check_output(["uname", "-m"], text=True).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get system architecture: {e}")
    
    if arch == "x86_64":
        return "linux/x86_64"
    elif arch == "arm64":
        return "linux/arm64/v8"
    else:
        raise ValueError(f"Invalid architecture: {arch}")

def _get_conda_arch() -> str:
    try:
        arch = subprocess.check_output(["uname", "-m"], text=True).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to get system architecture: {e}")

    if arch == "arm64":
        conda_arch = "aarch64"
    else:
        conda_arch = arch
    
    return conda_arch

import subprocess

def kill_all_gpu_processes():
    cmd = (
        "nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits | xargs -r sudo -n kill -9"
    )

    subprocess.run(cmd, shell=True, check=False)

def omit_warning_in_stderr(stderr: str) -> str:
    """Omit specific known warnings from stderr output."""
    filtered_lines = []
    for line in stderr.splitlines():
        if "WARNING: Running pip as the 'root' user" in line:
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)
    