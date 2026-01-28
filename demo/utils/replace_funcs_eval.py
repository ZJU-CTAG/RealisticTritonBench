import argparse
import json
import os
import difflib
from typing import Dict, List
from itertools import zip_longest
import ast

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def find_function_blocks(src: str, func_names: List[str]) -> Dict[str, str]:
    """
    返回 name -> text
    """
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line))

    results: Dict[str, str] = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            if node.name in func_names:
                start_line = node.lineno
                end_line = node.end_lineno
                if node.decorator_list:
                    start_line = min(d.lineno for d in node.decorator_list)
                start_idx = line_offsets[start_line - 1]
                end_idx = line_offsets[end_line]
                results[node.name] = src[start_idx:end_idx]
            self.generic_visit(node)

    Visitor().visit(tree)
    for name in func_names:
        if name not in results:
            raise RuntimeError(f"Function {name} not found")
    return results


def replace_blocks(src: str, replacements: Dict[str, str], func_names: List[str]) -> str:
    # 找到文件中对应函数的位置
    blocks = find_function_blocks(src, func_names)
    # 从下往上替换，保持索引不变
    items = sorted(blocks.items(), key=lambda x: src.find(x[1]), reverse=True)
    for name, old_text in items:
        new_text = replacements.get(name, old_text)
        start = src.find(old_text)
        end = start + len(old_text)
        src = src[:start] + new_text + src[end:]
    return src

def unified_diff(old: str, new: str, path: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}"
    )
    return "".join(diff)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    with open(args.specs, "r") as f:
        specs = json.load(f)
    with open(args.predictions, "r") as f:
        predictions = json.load(f)

    any_diff = False

    for file_path, entry in specs.items():
        source_func = entry["source_func"]
        target_func = entry["target_func"]

        assert len(source_func) <= len(target_func), \
            f"source_func and target_func length mismatch for {file_path}"

        if file_path not in predictions:
            raise RuntimeError(f"No predictions found for {file_path}")

        pred_entry: Dict[str, str] = predictions[file_path]

        for name in target_func:
            if name not in pred_entry:
                raise RuntimeError(f"Missing prediction for {file_path}:{name}")

        # ---------- 情况 1：文件不存在 ----------
        if not os.path.exists(file_path):
            print(f"[NEW FILE] {file_path} does not exist, creating")

            new_content = []
            for t_name in target_func:
                new_content.append(pred_entry[t_name].rstrip() + "\n\n")

            final_src = "".join(new_content)

            print(f"\n===== DIFF {file_path} =====")
            print(unified_diff("", final_src, file_path))

            if not args.dry_run:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                write_file(file_path, final_src)
                print(f"[CREATED] {file_path}")
            else:
                print(f"[DRY-RUN] Would create {file_path}")

            any_diff = True
            continue

        # ---------- 情况 2：文件存在 ----------
        head_src = read_file(file_path)
        new_src = head_src

        for s_name, t_name in zip_longest(source_func, target_func):
            t_impl = pred_entry[t_name].rstrip() + "\n"

            # 1) 新增函数：source 为空
            if s_name is None:
                print(f"[APPEND] {file_path}: adding new function {t_name}")
                new_src = new_src.rstrip() + "\n\n" + t_impl
                continue

            # 2) 替换函数：source 非空
            try:
                blocks = find_function_blocks(new_src, [s_name])
            except RuntimeError:
                raise RuntimeError(
                    f"Source function {s_name} not found in {file_path}"
                )

            old_text = blocks[s_name]
            start = new_src.find(old_text)
            end = start + len(old_text)

            new_src = new_src[:start] + t_impl + new_src[end:]

        # ---------- 输出 diff / 写文件 ----------
        if new_src != head_src:
            any_diff = True
            diff = unified_diff(head_src, new_src, file_path)
            print(f"\n===== DIFF {file_path} =====")
            print(diff)

            if not args.dry_run:
                write_file(file_path, new_src)
                print(f"[PATCHED] {file_path}")
            else:
                print(f"[DRY-RUN] Would patch {file_path}")
        else:
            print(f"[SKIP] No change for {file_path}")
if __name__ == "__main__":
    main()