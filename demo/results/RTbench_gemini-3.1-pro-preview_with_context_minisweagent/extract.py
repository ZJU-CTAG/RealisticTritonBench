import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent
input_file = base_dir / "preds.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for task_id, item in data.items():
    if "model_patch" not in item:
        continue

    model_patch_str = item["model_patch"]

    try:
        model_patch_json = json.loads(model_patch_str)
    except json.JSONDecodeError:
        print(f"Task {task_id} 的 model_patch 不是合法 JSON")
        continue

    output_file = base_dir / f"{task_id}_prediction.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(model_patch_json, f, indent=2, ensure_ascii=False)

    print(f"已生成 {output_file}")

# import json
# with open("/home/jinjunhuang/RTBench/RTBench/demo/results/RTbench_deepseek-chat_minisweagent/0_prediction.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# for k, v in data.items():
#     print(f"File: {k}")
#     for func_name, func_body in v.items():
#         print(f"  Function: {func_name}")
#         print(f"  Body:\n{func_body}\n")
