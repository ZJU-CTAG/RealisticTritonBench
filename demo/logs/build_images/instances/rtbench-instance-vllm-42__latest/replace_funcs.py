#!/usr/bin/env python3
"""
Usage:
  python replace_funcs.py \
    --repo /path/to/repo \
    --specs specs.json \
    --predictions predictions.json

What it does:
  1) git checkout base_commit
  2) extract full source of each function in source_func from file_path
  3) git checkout head_commit
  4) replace corresponding functions in target_func with the saved ones
     (indentation preserved)
  5) write file back to disk

Assumptions:
  - One function per name in the file
  - Functions are defined with `def name(...):` or `@decorator\n def name(...):`
  - No nested defs with the same name
"""

import argparse
import os
import re
import subprocess
import ast
import json
import difflib
from typing import Dict, List, Tuple
from itertools import zip_longest

def run(cmd: List[str], cwd: str):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,  # 捕获 stdout 和 stderr
            text=True  # 输出解码成字符串
        )
        print(f"[INFO] Command succeeded: {' '.join(cmd)}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd)}")
        print(f"[ERROR] Return code: {e.returncode}")
        print(f"[ERROR] stdout: {e.stdout}")
        print(f"[ERROR] stderr: {e.stderr}")
        raise

def fetch_pr(repo: str, pr_number: int, local_branch: str):
    run(["git", "fetch", "origin", f"pull/{pr_number}/head:{local_branch}"], cwd=repo)
    run(["git", "checkout", local_branch], cwd=repo)

def git_checkout(repo: str, commit: str):
    run(["git", "reset", "--hard"], cwd=repo)
    run(["git", "clean", "-fd"], cwd=repo)
    run(["git", "checkout", commit], cwd=repo)


def read_file(repo: str, path: str) -> str:
    with open(os.path.join(repo, path), "r", encoding="utf-8") as f:
        return f.read()


def write_file(repo: str, path: str, content: str):
    with open(os.path.join(repo, path), "w", encoding="utf-8") as f:
        f.write(content)


def find_function_blocks(
    src: str, func_names: List[str]
) -> Dict[str, Tuple[int, int, str]]:
    """
    Return: name -> (start_idx, end_idx, text)
    Uses Python AST instead of regex.
    Requires Python >= 3.8 for end_lineno.
    """
    tree = ast.parse(src)

    # line start offsets: lineno (1-based) -> char offset
    lines = src.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line))

    results: Dict[str, Tuple[int, int, str]] = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef):
            if node.name in func_names:
                if not hasattr(node, "end_lineno") or node.end_lineno is None:
                    raise RuntimeError(
                        f"Python < 3.8 detected, end_lineno not available for {node.name}"
                    )

                start_line = node.lineno
                end_line = node.end_lineno

                # Include decorators: start from first decorator if exists
                if node.decorator_list:
                    start_line = min(d.lineno for d in node.decorator_list)

                start_idx = line_offsets[start_line - 1]
                end_idx = line_offsets[end_line]

                text = src[start_idx:end_idx]
                results[node.name] = (start_idx, end_idx, text)

            # Continue walking to catch nested functions too
            self.generic_visit(node)

    Visitor().visit(tree)

    # Sanity check
    for name in func_names:
        if name not in results:
            raise RuntimeError(f"Function {name} not found")

    return results


def replace_blocks(src: str, replacements: Dict[str, str]) -> str:
    # Find all blocks first
    blocks = find_function_blocks(src, list(replacements.keys()))

    # Replace from bottom to top so indices stay valid
    items = sorted(blocks.items(), key=lambda x: x[1][0], reverse=True)

    for name, (start, end, _) in items:
        new_text = replacements[name]
        src = src[:start] + new_text + src[end:]

    return src

def unified_diff(old: str, new: str, path: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pull_number", required=True)
    parser.add_argument("--base_commit", required=True)
    parser.add_argument("--head_commit", required=True)
    parser.add_argument("--specs", required=True, help="JSON file mapping paths to function replacements")
    parser.add_argument("--dry_run", action="store_true", help="If set, do not write changes to disk")
    
    args = parser.parse_args()

    with open(args.specs, "r") as f:
        specs = json.load(f)

    save_blocks_all: Dict[str, Dict[str, str]] = {}

    # 1) checkout base_commit
    git_checkout(args.repo, args.base_commit)

    for file_path, entry in specs.items():
        source_func = entry["source_func"]

        try:
            base_src = read_file(args.repo, file_path)
        # New File, no need to replace
        except FileNotFoundError:
            save_blocks_all[file_path] = {}
            continue

        base_blocks = find_function_blocks(base_src, source_func)

        saved_blocks: Dict[str, str] = {}
        for name in source_func:
            saved_blocks[name] = base_blocks[name][2]
        
        save_blocks_all[file_path] = saved_blocks

    # 2) checkout head_commit
    fetch_pr(args.repo, args.pull_number, local_branch=f"pr-{args.pull_number}")
    git_checkout(args.repo, args.head_commit)

    for file_path, entry in specs.items():
        target_func = entry["target_func"]
        source_func = entry["source_func"]

        assert len(source_func) <= len(target_func), "source_func must be <= target_func"
        head_src = read_file(args.repo, file_path)
        
        saved_blocks = save_blocks_all[file_path]

        replacements: Dict[str, str] = {}
        for s_name, t_name in zip_longest(source_func, target_func):
            if s_name is None:
                replacements[t_name] = ""
            else:
                replacements[t_name] = saved_blocks[s_name]

        new_src = replace_blocks(head_src, replacements)

        if new_src != head_src:
            any_diff = True
            diff = unified_diff(head_src, new_src, file_path)
            print(f"\n===== DIFF {file_path} =====")
            print(diff)

            if not args.dry_run:
                write_file(args.repo, file_path, new_src)
                print(f"[HEAD] Patched {file_path}")
            else:
                print(f"[DRY-RUN] Would patch {file_path}")
        else:
            print(f"[SKIP] No change for {file_path}")

    if args.dry_run:
        print("\nDry-run complete. No files were written.")
    else:
        print("\nDone. All files patched successfully.")

    if not any_diff:
        print("Warning: No differences produced. Check spec.json and commits.")


if __name__ == "__main__":
    main()
