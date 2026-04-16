#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def accuracy_ok(item: Dict[str, Any]) -> bool:
    diff = item.get("diff") or {}
    fe = diff.get("flexible-extract")
    sm = diff.get("strict-match")
    return (fe is not None and fe >= 0) and (sm is not None and sm >= 0)


def latency_ok(item: Dict[str, Any]) -> bool:
    speed = item.get("latency_speedup") or {}
    ttft = speed.get("ttft")
    tpot = speed.get("tpot")
    return (ttft is not None and ttft >= 0.96) and (tpot is not None and tpot >= 0.96)


def is_success(report: Dict[str, Any]) -> bool:
    summary = report.get("unit_test_pass_summary") or {}
    if summary.get("overall_unit_test_pass_rate") < 1.0:
        return False

    accuracy_tests = report.get("accuracy_tests") or []
    latency_tests = report.get("latency_tests") or []

    # Additional tests (if present) require their own rules to all pass.
    if accuracy_tests and not all(accuracy_ok(item) for item in accuracy_tests):
        return False
    if latency_tests and not all(latency_ok(item) for item in latency_tests):
        return False
    return True


def load_task_type_map(problems_path: Path) -> Dict[str, str]:
    problems = json.loads(problems_path.read_text(encoding="utf-8"))
    task_type_map: Dict[str, str] = {}
    for item in problems:
        task_id = item.get("task_id")
        task_type = item.get("type")
        if task_id is None or task_type is None:
            continue
        task_type_map[str(task_id)] = str(task_type)
    return task_type_map


def parse_report_task_id(task_name: Any) -> Optional[str]:
    if not isinstance(task_name, str):
        return None
    if task_name.startswith("task_"):
        return task_name[len("task_") :]
    return None


def matches_task_type(case_type: str, requested_task_type: str) -> bool:
    # Special combined filter: "modificaton" means bug_fix or feature.
    if requested_task_type == "modificaton":
        return case_type in {"bug_fix", "feature"}
    return case_type == requested_task_type


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate success ratio from a result analysis JSON file."
    )
    parser.add_argument(
        "--input",
        default="demo/logs/res_analysis_ds_chat.json",
        help="Input analysis JSON path.",
    )
    parser.add_argument(
        "--output",
        default="demo/logs/success_ratio_ds_chat.json",
        help="Output JSON path for computed summary.",
    )
    parser.add_argument(
        "--task-type",
        default=None,
        help="Optional task type filter (from data/problems.json), e.g. bug_fix/new_op/optimization/modificaton.",
    )
    parser.add_argument(
        "--problems",
        default="data/problems.json",
        help="Path to problems.json used for task_id -> type mapping.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(f"{args.output}_{args.task_type}")
    problems_path = Path(args.problems)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    reports: List[Dict[str, Any]] = data.get("reports", [])
    total_before_filter = len(reports)
    filtered_out_by_type = 0
    unknown_task_id_count = 0
    if args.task_type is not None:
        task_type_map = load_task_type_map(problems_path)
        filtered_reports: List[Dict[str, Any]] = []
        for report in reports:
            task_id = parse_report_task_id(report.get("task"))
            if task_id is None:
                unknown_task_id_count += 1
                continue
            case_type = task_type_map.get(task_id)
            if case_type is None:
                unknown_task_id_count += 1
                continue
            if matches_task_type(case_type, args.task_type):
                filtered_reports.append(report)
            else:
                filtered_out_by_type += 1
        reports = filtered_reports

    success_tasks: List[str] = []
    failed_tasks: List[str] = []

    for report in reports:
        task = report.get("task", "unknown_task")
        if is_success(report):
            success_tasks.append(task)
        else:
            failed_tasks.append(task)

    total = len(reports)
    success = len(success_tasks)
    ratio = (success / total) if total else 0.0

    result = {
        "input_file": str(input_path.resolve()),
        "task_type_filter": args.task_type,
        "problems_path": str(problems_path.resolve()) if args.task_type is not None else None,
        "total_tasks_before_filter": total_before_filter,
        "total_tasks": total,
        "filtered_out_by_type": filtered_out_by_type,
        "unknown_task_id_count": unknown_task_id_count,
        "success_tasks_count": success,
        "success_ratio": ratio,
        "success_percent": round(ratio * 100, 2),
        "success_criteria": {
            "unit_only": "overall_unit_test_pass_rate == 1.0",
            "accuracy": "diff.flexible-extract >= 0 and diff.strict-match >= 0",
            "latency": "latency_speedup.ttft >= 0.96 and latency_speedup.tpot >= 0.96",
        },
        "success_tasks": success_tasks,
        "failed_tasks": failed_tasks,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(
        f"Saved result to {output_path.resolve()} | "
        f"success={success}/{total} ({ratio*100:.2f}%)"
    )


if __name__ == "__main__":
    main()
