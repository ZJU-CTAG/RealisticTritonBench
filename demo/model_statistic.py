import json
import shlex
from pathlib import Path


check_item = [
    "0","1","2","6","7","9","10","11","13","14","15","16","17","18","19","20","21","22","25","26","27","28","29","30","33","34","36","39","44","49","50","53","54"
]

INPUT_PATH = "/home/jinjunhuang/RTBench/RTBench/data/problems.json"
OUTPUT_PATH = "/home/jinjunhuang/RTBench/RTBench/demo/model_statistic.json"

def extract_model_from_vllm_serve(command: str):
    """
    从类似:
        vllm serve openai/gpt-oss-20b
    提取:
        openai/gpt-oss-20b
    """
    try:
        parts = shlex.split(command)
    except ValueError:
        return None

    for i in range(len(parts) - 2):
        if parts[i] == "vllm" and parts[i + 1] == "serve":
            return parts[i + 2]
    return None


def extract_model_from_model_flag(command: str):
    """
    从类似:
        python benchmarks/benchmark_serving.py --dataset-name random --num-prompts 500 --model RedHatAI/Qwen2-7B-Instruct-quantized.w8a8
    提取:
        RedHatAI/Qwen2-7B-Instruct-quantized.w8a8
    """
    try:
        parts = shlex.split(command)
    except ValueError:
        return None

    for i in range(len(parts) - 1):
        if parts[i] == "--model":
            return parts[i + 1]
    return None


def get_script_value(script_item):
    """
    兼容两种情况：
    1. script_item 本身就是字符串命令
    2. script_item 是 dict，命令在 value 字段中
    """
    if isinstance(script_item, str):
        return script_item
    if isinstance(script_item, dict):
        return script_item.get("value")
    return None

def get_last_value_from_dict(d: dict):
    """获取字典最后一个插入项的 value"""
    if not d:
        return None
    return list(d.values())[-1]

def main():
    model_cases = {}
    model_check_cases = {}

    input_path = Path(INPUT_PATH)
    with input_path.open("r", encoding="utf-8") as f:
        problems = json.load(f)

    results = []

    for idx, problem in enumerate(problems):
        test_scripts = problem.get("test_scripts", [])
        task_id = problem.get("task_id", idx)

        model_name = None

        # 先找 serve
        serve_value = None
        if isinstance(test_scripts, dict) and "serve" in test_scripts:
            serve_value = test_scripts.get("serve")

        if serve_value:
            model_name = extract_model_from_vllm_serve(serve_value)

        # 如果没有 serve
        if model_name is None and test_scripts:
            last_value = get_last_value_from_dict(test_scripts)

            if "benchmark_serving" not in last_value and "vllm bench serve" not in last_value:
                model_name = "Unexisted"
            else:
                if last_value:
                    model_name = extract_model_from_model_flag(last_value)

        if model_name is None:
            model_name = "Unknown"

        results.append({
            "index": idx,
            "task_id": task_id,
            "model_name": model_name,
        })

        # -----------------------
        # 统计所有 case
        # -----------------------
        model_cases.setdefault(model_name, []).append(task_id)

        # -----------------------
        # 统计 check_item case
        # -----------------------
        if task_id in check_item:
            model_check_cases.setdefault(model_name, []).append(task_id)
    output = {
        "results": results,
        "model_cases": model_cases,
        "model_check_cases": model_check_cases
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    


if __name__ == "__main__":
    main()