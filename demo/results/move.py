import os
import shutil
import re

src_dir = "/home/jinjunhuang/RTBench/RTBench/demo/results/RTbench_trae-agent"      # 原始 patch 文件目录
dst_dir = "/home/jinjunhuang/RTBench/RTBench/demo/results/RTbench_trae_deepseek"     # 输出目录

os.makedirs(dst_dir, exist_ok=True)

pattern = re.compile(r"(\d+)\.patch$")

for root, dirs, files in os.walk(src_dir):
    for file in files:
        match = pattern.match(file)
        if match:
            idx = match.group(1)

            src_path = os.path.join(root, file)
            dst_name = f"{idx}_prediction.json"
            dst_path = os.path.join(dst_dir, dst_name)

            shutil.copy(src_path, dst_path)

            print(f"{src_path} -> {dst_path}")