import json

with open("/home/jinjunhuang/RTBench/dataset/context.py", "r") as f:
    text = f.read()

with open("/home/jinjunhuang/RTBench/dataset/example.json", "r") as f:
    data = json.load(f)

print(data["context"])

data["context"]["fused_moe.py"] = text

with open("/home/jinjunhuang/RTBench/dataset/example.json", "w") as f:
    json.dump(data, f, indent=4)