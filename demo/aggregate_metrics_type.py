import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def avg(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


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


def compute_metrics(
    report_path: Path, task_type: Optional[str] = None, problems_path: Optional[Path] = None
) -> Dict[str, Any]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    reports = data.get("reports", [])
    total_reports = len(reports)

    filtered_out_by_type = 0
    unknown_task_id_count = 0
    if task_type is not None:
        if problems_path is None:
            raise ValueError("problems_path is required when task_type is specified.")
        task_type_map = load_task_type_map(problems_path)
        filtered_reports = []
        for task in reports:
            task_id = parse_report_task_id(task.get("task"))
            if task_id is None:
                unknown_task_id_count += 1
                continue
            case_type = task_type_map.get(task_id)
            if case_type is None:
                unknown_task_id_count += 1
                continue
            if matches_task_type(case_type, task_type):
                filtered_reports.append(task)
            else:
                filtered_out_by_type += 1
        reports = filtered_reports

    overall_rates: List[float] = []
    overall_full_pass_count = 0
    for task in reports:
        v = task.get("unit_test_pass_summary", {}).get("overall_unit_test_pass_rate")
        if is_number(v):
            fv = float(v)
            overall_rates.append(fv)
            if fv == 1.0:
                overall_full_pass_count += 1
    avg_overall_unit_test_pass_rate = avg(overall_rates)

    nr_total = 0
    nr_pass = 0
    for task in reports:
        overall = task.get("unit_test_pass_summary", {}).get("overall_unit_test_pass_rate")
        accuracy_tests = task.get("accuracy_tests", [])
        
        if not accuracy_tests or overall < 1:
            continue

        for test in accuracy_tests:
            nr_total += 1
            diff = test.get("diff", {})
            model_metrics = test.get("model", {})
            model_flexible_extract = model_metrics.get("flexible-extract")
            f_diff = diff.get("flexible-extract")
            s_diff = diff.get("strict-match")

            # If model flexible-extract is null, treat this NR test as failed.
            if model_flexible_extract is None:
                continue

            if (
                is_number(f_diff)
                and is_number(s_diff)
                and 0 <= float(f_diff) <= 0.1
                and 0 <= float(s_diff) <= 0.1
            ):
                nr_pass += 1

    avg_nr = (nr_pass / nr_total) if nr_total > 0 else None

    ttft_values: List[float] = []
    tpot_values: List[float] = []
    latency_eligible_tests = 0
    for task in reports:
        overall = task.get("unit_test_pass_summary", {}).get("overall_unit_test_pass_rate")
        latency_tests = task.get("latency_tests", [])
        if not latency_tests or overall < 1:
            continue

        for test in latency_tests:
            latency_eligible_tests += 1
            spd = test.get("latency_speedup", {})
            model_metrics = test.get("model", {})
            ttft = spd.get("ttft")
            tpot = spd.get("tpot")
            e2el = spd.get("e2el")
            model_ttft = model_metrics.get("ttft")
            model_tpot = model_metrics.get("tpot")
            model_e2el = model_metrics.get("e2el")

            # If model ttft/tpot/e2el are all missing, default speedups to 0.98.
            if model_ttft is None and model_tpot is None and model_e2el is None:
                ttft_values.append(0.98)
                tpot_values.append(0.98)
                continue

            # If ttft and tpot are both missing, use e2el speedup as substitute.
            if ttft is None and tpot is None and is_number(e2el):
                ttft_values.append(float(e2el))
                tpot_values.append(float(e2el))
            # If ttft, tpot, and e2el are all missing, default ttft/tpot to 0.98.
            elif ttft is None and tpot is None and e2el is None:
                ttft_values.append(0.98)
                tpot_values.append(0.98)
            else:
                if is_number(ttft):
                    ttft_values.append(float(ttft))
                if is_number(tpot):
                    tpot_values.append(float(tpot))

    avg_latency_spd_ttft = avg(ttft_values)
    avg_latency_spd_tpot = avg(tpot_values)

    return {
        "source_report": str(report_path),
        "task_type_filter": task_type,
        "problems_path": str(problems_path) if problems_path is not None else None,
        "total_tasks_before_filter": total_reports,
        "total_tasks": len(reports),
        "avg_overall_unit_test_pass_rate": avg_overall_unit_test_pass_rate,
        "avg_nr": avg_nr,
        "avg_latency_spd_ttft": avg_latency_spd_ttft,
        "avg_latency_spd_tpot": avg_latency_spd_tpot,
        "detail": {
            "filtered_out_by_type": filtered_out_by_type,
            "unknown_task_id_count": unknown_task_id_count,
            "overall_rate_task_count": len(overall_rates),
            "overall_rate_full_pass_count": overall_full_pass_count,
            "nr_eligible_accuracy_tests": nr_total,
            "nr_pass_count": nr_pass,
            "latency_eligible_tests": latency_eligible_tests,
            "latency_ttft_sample_count": len(ttft_values),
            "latency_tpot_sample_count": len(tpot_values),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate average metrics from res_analysis_*.json report."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to res_analysis JSON file, e.g. demo/logs/res_analysis_ds_chat.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. Defaults to <input>_avg_metrics.json",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        default=None,
        help="Optional task type filter (from data/problems.json), e.g. bug_fix/new_op/optimization.",
    )
    parser.add_argument(
        "--problems",
        type=Path,
        default=Path("data/problems.json"),
        help="Path to problems.json used for task_id -> type mapping.",
    )
    args = parser.parse_args()

    metrics = compute_metrics(
        args.input,
        task_type=args.task_type,
        problems_path=args.problems if args.task_type is not None else None,
    )
    output = args.output
    if output is None:
        output = args.input.with_name(f"{args.input.stem}_avg_metrics_{args.task_type}.json")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"[DONE] Wrote aggregated metrics to: {output}")


if __name__ == "__main__":
    main()
