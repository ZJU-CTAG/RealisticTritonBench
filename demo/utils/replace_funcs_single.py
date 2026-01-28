#!/usr/bin/env python3
"""
Usage:
  python replace_funcs.py \
    --repo /path/to/repo \
    --base_commit abc123 \
    --head_commit def456 \
    --file_path vllm/model_executor/layers/mamba/ops/ssd_bmm.py \
    --source_funcs _bmm_chunk_fwd_kernel,_bmm_chunk_fwd \
    --target_funcs _bmm_chunk_fwd_kernel,_bmm_chunk_fwd

What it does:
  1) git checkout base_commit
  2) extract full source of each function in source_funcs from file_path
  3) git checkout head_commit
  4) replace corresponding functions in target_funcs with the saved ones
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
from typing import Dict, List, Tuple
from itertools import zip_longest


def run(cmd: List[str], cwd: str):
    subprocess.check_call(cmd, cwd=cwd)


def git_checkout(repo: str, commit: str):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base_commit", required=True)
    parser.add_argument("--head_commit", required=True)
    parser.add_argument("--file_path", required=True)
    parser.add_argument("--source_funcs", required=True,
                    help="comma-separated list")
    parser.add_argument("--target_funcs", required=True,
                    help="comma-separated list")
    
    args = parser.parse_args()

    source_funcs = [x.strip() for x in args.source_funcs.split(",") if x.strip()]
    target_funcs = [x.strip() for x in args.target_funcs.split(",") if x.strip()]

    assert len(source_funcs) <= len(target_funcs), "source_funcs must be <= target_funcs"

    # 1) checkout base_commit
    git_checkout(args.repo, args.base_commit)

    base_src = read_file(args.repo, args.file_path)
    base_blocks = find_function_blocks(base_src, source_funcs)

    saved_blocks: Dict[str, str] = {}
    for name in source_funcs:
        saved_blocks[name] = base_blocks[name][2]

    # 2) checkout head_commit
    git_checkout(args.repo, args.head_commit)

    head_src = read_file(args.repo, args.file_path)

    # map target_name -> source_text
    replacements: Dict[str, str] = {}
    for s_name, t_name in zip_longest(source_funcs, target_funcs):
        if s_name is None:
            replacements[t_name] = ""
        else:
            replacements[t_name] = saved_blocks[s_name]

    new_src = replace_blocks(head_src, replacements)

    write_file(args.repo, args.file_path, new_src)

    print("Done. Functions replaced in", args.file_path)


if __name__ == "__main__":
    main()
