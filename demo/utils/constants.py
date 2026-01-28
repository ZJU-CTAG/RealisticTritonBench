from enum import Enum
from pathlib import Path
from typing import TypedDict
from datetime import datetime

from .python import *


# Constants - dataset paths
DATASET_LOCAL_PATH = "/home/jinjunhuang/RTBench/RTBench/problems.json"
HF_DATASET_NAME = ""

# Constants - Vllm Serving
VLLM_SERVING_PORT = 9010

# Constants - Docker Build
HTTP_PROXY = "http://127.0.0.1:9091"
HTTPS_PROXY = "http://127.0.0.1:9091"
NO_PROXY = "localhost,127.0.0.1"
HF_ENDPOINT = "https://hf-mirror.com"
GIT_PROXY_SET_COMMAND = "git config --global http.proxy http://127.0.0.1:9091 && git config --global https.proxy http://127.0.0.1:9091"


# Constants - Evaluation Log Directories
BASE_IMAGE_BUILD_DIR = Path("logs/build_images/base")
REPO_IMAGE_BUILD_DIR = Path("logs/build_images/repo")
INSTANCE_IMAGE_BUILD_DIR = Path("logs/build_images/instances")
RUN_EVALUATION_LOG_DIR = Path("logs/run_evaluation")
RUN_VALIDATION_LOG_DIR = Path("logs/run_validation")


# Constants - Task Instance Class
class RTBenchInstance(TypedDict):
    repo: str
    instance_id: str
    instance_name: str
    task_description: str
    targets: dict
    context: dict
    test_scripts: dict
    gold_patch: dict
    hardware: str
    pull_number: datetime
    created_at: datetime
    base_commit_id: str
    head_commit_id: str
    base_tag: str


class ResolvedStatus(Enum):
    NO = "RESOLVED_NO"
    PARTIAL = "RESOLVED_PARTIAL"
    FULL = "RESOLVED_FULL"


class TestStatus(Enum):
    FAILED = "FAILED"
    PASSED = "PASSED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    XFAIL = "XFAIL"


class EvalType(Enum):
    PASS_AND_FAIL = "pass_and_fail"
    FAIL_ONLY = "fail_only"


# Constants - Evaluation Keys
KEY_INSTANCE_ID = "instance_id"
KEY_MODEL = "model_name_or_path"
KEY_PREDICTION = "model_patch"

# Constants - Harness
DOCKER_PATCH = "/tmp/patch.diff"
DOCKER_USER = "root"
DOCKER_WORKDIR = "/testbed"
LOG_REPORT = "report.json"
LOG_INSTANCE = "run_instance.log"
LOG_TEST_OUTPUT = "test_output.txt"
UTF8 = "utf-8"

# Constants - Logging
APPLY_PATCH_FAIL = ">>>>> Patch Apply Failed"
APPLY_PATCH_PASS = ">>>>> Applied Patch"
INSTALL_FAIL = ">>>>> Init Failed"
INSTALL_PASS = ">>>>> Init Succeeded"
INSTALL_TIMEOUT = ">>>>> Init Timed Out"
RESET_FAILED = ">>>>> Reset Failed"
TESTS_ERROR = ">>>>> Tests Errored"
TESTS_FAILED = ">>>>> Some Tests Failed"
TESTS_PASSED = ">>>>> All Tests Passed"
TESTS_TIMEOUT = ">>>>> Tests Timed Out"
START_TEST_OUTPUT = ">>>>> Start Test Output"
END_TEST_OUTPUT = ">>>>> End Test Output"


# Constants - Patch Types
class PatchType(Enum):
    PATCH_GOLD = "gold"
    PATCH_PRED = "pred"
    PATCH_PRED_TRY = "pred_try"
    PATCH_PRED_MINIMAL = "pred_minimal"
    PATCH_PRED_MINIMAL_TRY = "pred_minimal_try"
    PATCH_TEST = "test"

    def __str__(self):
        return self.value



LATEST = "latest"

# Constants - Default Docker Specs

DEFAULT_DOCKER_SPECS = {
    "conda_version": "py311_23.11.0-2",
    "node_version": "21.6.2",
    "pnpm_version": "9.5.0",
    "python_version": "3.10",
    "ubuntu_version": "22.04",
}

GITHUB_URLS = {
    "vllm-project/vllm": "https://github.com/vllm-project/vllm.git",
    "sgl-project/sglang": "https://github.com/sgl-project/sglang.git"
}