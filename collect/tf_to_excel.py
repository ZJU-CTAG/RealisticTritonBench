FILTER_DATA_PATH = "/home/jinjunhuang/RTBench/RTBench/data/filter_dataset.jsonl"

import json
import pandas as pd

with open(FILTER_DATA_PATH, "r") as f:
    data = [json.loads(line) for line in f.readlines()]

# 2. 指定 Excel 的列顺序
columns = [
    "task_id",
    "name",
    "type",
    "task_description",
    "targets",
    "context",
    "test_scripts",
    "hardware",
    "repo",
    "pull_number",
    "status",
    "head_commit",
    "base_commit",
    "base_tag",
    "created_at",
    "patch",
]

# 3. 构建 DataFrame，如果某个 key 不存在，就置空
rows = []
for item in data:
    row = {col: item.get(col, "") for col in columns}
    rows.append(row)

df = pd.DataFrame(rows, columns=columns)

# 4. 输出 Excel
df.to_excel("output.xlsx", index=False)
print("Saved to output.xlsx")