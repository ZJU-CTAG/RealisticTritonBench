#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import os
import tempfile
import ast

from pathlib import Path
from typing import Dict, List

PROBLEM_JSONS = "/home/jinjunhuang/RTBench/dataset/optimization/FusedMoE/problems.json"

# ---------- Helper Functions ----------
def replace_function_in_file(path: Path, function_name: str, new_function_src: str):
    """
    Replace functions in a Python file with new implementations.

    :param path: Path to the Python file.
    :param function_name: Name of the function to replace.
    :param new_function_src: New function source code as a string.
    """
    original_code = path.read_text()
    tree = ast.parse(original_code)

    # Create a mapping from function name to new source code
    func_map = {function_name: new_function_src}

    class FunctionReplacer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name in func_map:
                # Parse the new function source code and replace the node
                new_node = ast.parse(func_map[node.name]).body[0]
                return new_node
            return node

    # Transform the AST
    transformer = FunctionReplacer()
    modified_tree = transformer.visit(tree)
    ast.fix_missing_locations(modified_tree)

    modified_code = ast.unparse(modified_tree)

    path.write_text(modified_code)



# ---------- Main Test logic ----------


def run(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def git(repo, *args, check=True):
    return run(["git", *args], cwd=repo, check=check)


def checkout_pr(repo: Path, pr: int, commit: str | None):
    branch = f"tmp-pr-{pr}"

    git(repo, "fetch", "origin", f"pull/{pr}/head:{branch}")
    git(repo, "checkout", branch)

    if commit:
        git(repo, "checkout", commit)

    return branch





def run_tests(repo: Path, tests: list[str], json_report: Path):
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *tests,
        "--json-report",
        f"--json-report-file={json_report}",
    ]
    return run(cmd, cwd=repo, check=False)


def analyze_report(report_path: Path):
    if not report_path.exists():
        return {"status": "no-report"}

    report = json.loads(report_path.read_text())
    tests = report.get("tests", [])

    failed = [t for t in tests if t["outcome"] == "failed"]
    passed = [t for t in tests if t["outcome"] == "passed"]

    return {
        "status": "failed" if failed else "passed",
        "passed": len(passed),
        "failed": len(failed),
        "failed_tests": [t["nodeid"] for t in failed],
    }


def cleanup(repo: Path, branch: str, keep: bool):
    if keep:
        print(f"Keeping branch {branch}")
        return

    git(repo, "checkout", "main")
    git(repo, "branch", "-D", branch)

def source_back(repo: Path, task: dict, source_files: list[Path]):
    target_files = task.get("targets", [])
    assert len(target_files) == len(source_files), "Number of source files must match number of target functions"

    for src in source_files:
        source_name = src.name
        assert str(source_name) in target_files, f"Source file {src} not in target functions"
        target_file_path = repo / task['targets']["path"]

        original_src = src.read_text()
        target_file_path.write_text(original_src)

def apply_patch(repo: Path, task: dict, patch_files: list[Path]):
    target_files = task.get("targets", [])
    assert len(target_files) == len(patch_files), "Number of patch files must match number of target files"

    for patch in patch_files:
        patch_target_file = os.path.join(str(patch.parent.name), ".py")
        assert patch_target_file in target_files, f"Patch file {patch} not in target files"
        
        target_functions = task["targets"][patch_target_file]["functions"]
        patch_function = patch.stem
        assert str(patch_function) in target_functions, f"Patch function {patch_function} not in target functions"

        target_file_path = repo / task['targets'][patch_target_file]['path']

        target_function = patch.read_text()
        replace_function_in_file(target_file_path, patch_function, target_function)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_id", required=True, type=int)
    parser.add_argument("--repo", required=True, type=str)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--commit", required=False)
    parser.add_argument("--source_files", nargs="+", type=str)
    parser.add_argument("--patch_files", nargs="+", type=str)
    parser.add_argument("--tests", nargs="+", required=True)
    parser.add_argument("--out_dir", type=str, default="/home/jinjunhuang/RTBench/dataset/results")
    parser.add_argument("--keep_branch", action="store_true")

    args = parser.parse_args()

    with open (PROBLEM_JSONS, "r") as f:
        tasks_json = json.load(f)

    task: Dict = next((p for p in tasks_json if p["task_id"] == args.task_id))

    task_type = task.get("type", "Unknown")
    task_name = task.get("name", "Unknown")

    try:
        # Step1: Checkout target PR
        branch = checkout_pr(Path(args.repo), args.pr, args.commit)

        # Step2: Keep back the original source files that model need to replace
        source_back(Path(args.repo), task, [Path(f) for f in args.source_files])

        # Step3: Apply patch functions
        apply_patch(Path(args.repo), task, [Path(f) for f in args.patch_files])

        # Step4: Run tests
        out_dir = Path(args.out_dir) / f"Problem_{task_type}_task_{args.task_id}_{task_name}"
        out_dir.mkdir(parents=True, exist_ok=True)

        report_path = out_dir / "result.json"

        results = run_tests(args.repo, args.tests, report_path)
        summary = analyze_report(report_path)

        args.out.write_text(json.dumps(summary, indent=2))

        print("\n=== Summary ===")
        print(json.dumps(summary, indent=2))

    finally:
        cleanup(args.repo, branch, args.keep_branch)


if __name__ == "__main__":
    main()