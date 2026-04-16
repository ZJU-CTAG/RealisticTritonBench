import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def as_float(x: Any) -> Optional[float]:
    if is_number(x):
        return float(x)
    return None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def index_unit_tests(unit_tests: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for i, item in enumerate(unit_tests):
        key = str(item.get("test_id", i))
        indexed[key] = item
    return indexed


def extract_numeric_accuracy_metrics(d: Dict[str, Any]) -> Dict[str, float]:
    # Keep only non-latency numeric metrics as fallback accuracy indicators.
    excluded = {
        "test_id",
        "output",
        "dataset",
        "passed",
        "failed",
        "ttft",
        "tpot",
        "e2el",
        "output_throughput",
        "total_throughput",
    }
    out: Dict[str, float] = {}
    for k, v in d.items():
        if k in excluded:
            continue
        fv = as_float(v)
        if fv is not None:
            out[k] = fv
    return out


def find_non_passed_tests(items: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict) and "passed" not in item and item:
            out.append(item)
    return out


def classify_test(test: Dict[str, Any]) -> str:
    # According to requirement: dataset exists => accuracy test, else latency test.
    if "dataset" in test:
        return "accuracy"
    return "latency"


def compare_accuracy(gold: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "test_id": model.get("test_id") or gold.get("test_id"),
        "gold": {},
        "model": {},
        "diff": {},
    }

    f_gold = as_float(gold.get("flexible-extract"))
    f_model = as_float(model.get("flexible-extract"))
    s_gold = as_float(gold.get("strict-match"))
    s_model = as_float(model.get("strict-match"))

    result["gold"]["flexible-extract"] = f_gold
    result["model"]["flexible-extract"] = f_model
    result["diff"]["flexible-extract"] = None if (f_gold is None or f_model is None) else (f_model - f_gold)

    result["gold"]["strict-match"] = s_gold
    result["model"]["strict-match"] = s_model
    result["diff"]["strict-match"] = None if (s_gold is None or s_model is None) else (s_model - s_gold)

    fallback_gold = extract_numeric_accuracy_metrics(gold)
    fallback_model = extract_numeric_accuracy_metrics(model)
    fallback_diff: Dict[str, Optional[float]] = {}
    for k in sorted(set(fallback_gold) | set(fallback_model)):
        gv = fallback_gold.get(k)
        mv = fallback_model.get(k)
        fallback_diff[k] = None if (gv is None or mv is None) else (mv - gv)

    result["gold"]["other_accuracy_metrics"] = fallback_gold
    result["model"]["other_accuracy_metrics"] = fallback_model
    result["diff"]["other_accuracy_metrics"] = fallback_diff

    return result


def compare_latency(gold: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    metrics = ["ttft", "tpot", "e2el", "output_throughput", "total_throughput"]
    result: Dict[str, Any] = {
        "test_id": model.get("test_id") or gold.get("test_id"),
        "gold": {m: as_float(gold.get(m)) for m in metrics},
        "model": {m: as_float(model.get(m)) for m in metrics},
        "latency_speedup": {
            "ttft": None,
            "tpot": None,
            "e2el": None,
        },
    }

    g_ttft = result["gold"]["ttft"]
    m_ttft = result["model"]["ttft"]
    g_tpot = result["gold"]["tpot"]
    m_tpot = result["model"]["tpot"]

    if g_ttft is None and m_ttft is None and g_tpot is None and m_tpot is None:
        # Only when TTFT/TPOT are both null, compute E2EL speedup.
        result["latency_speedup"]["e2el"] = safe_div(result["gold"]["e2el"], result["model"]["e2el"])
    else:
        # Normal latency speedup: gold/model on ttft, tpot.
        result["latency_speedup"]["ttft"] = safe_div(g_ttft, m_ttft)
        result["latency_speedup"]["tpot"] = safe_div(g_tpot, m_tpot)

    return result


def analyze_one_task(gold_path: Path, model_path: Path) -> Dict[str, Any]:
    gold = load_json(gold_path)
    model = load_json(model_path)

    # Eval format: [unit_tests(list), accuracy(dict), latency(dict), other(list)]
    gold_unit = gold[0] if len(gold) > 0 and isinstance(gold[0], list) else []
    model_unit = model[0] if len(model) > 0 and isinstance(model[0], list) else []

    gold_unit_idx = index_unit_tests(gold_unit)
    model_unit_idx = index_unit_tests(model_unit)

    unit_report: List[Dict[str, Any]] = []
    for key in sorted(set(gold_unit_idx) | set(model_unit_idx), key=lambda x: (len(x), x)):
        g = gold_unit_idx.get(key, {})
        m = model_unit_idx.get(key, {})
        g_passed = g.get("passed") if is_number(g.get("passed")) else None
        m_passed = m.get("passed") if is_number(m.get("passed")) else None
        g_failed = g.get("failed") if is_number(g.get("failed")) else None
        m_failed = m.get("failed") if is_number(m.get("failed")) else None
        pass_rate = safe_div(as_float(m_passed), as_float(g_passed))

        unit_report.append(
            {
                "test_id": key,
                "gold_passed": g_passed,
                "gold_failed": g_failed,
                "model_passed": m_passed,
                "model_failed": m_failed,
                "unit_test_pass_rate": pass_rate,
            }
        )

    gold_total_passed = sum(int(x.get("passed", 0)) for x in gold_unit if is_number(x.get("passed")))
    model_total_passed = sum(int(x.get("passed", 0)) for x in model_unit if is_number(x.get("passed")))
    overall_pass_rate = safe_div(float(model_total_passed), float(gold_total_passed))

    result: Dict[str, Any] = {
        "task": gold_path.parent.name,
        "gold_file": str(gold_path),
        "model_file": str(model_path),
        "unit_tests": unit_report,
        "unit_test_pass_summary": {
            "gold_total_passed": gold_total_passed,
            "model_total_passed": model_total_passed,
            "overall_unit_test_pass_rate": overall_pass_rate,
        },
        "non_passed_tests_exist": False,
        "accuracy_tests": [],
        "latency_tests": [],
        "skipped_followup": False,
    }

    # Gate: if model total passed < 1, skip follow-up judgment.
    if model_total_passed < 1:
        result["skipped_followup"] = True
        return result

    gold_rest = [x for x in gold[1:] if isinstance(x, dict)]
    model_rest = [x for x in model[1:] if isinstance(x, dict)]

    gold_non_passed = find_non_passed_tests(gold_rest)
    model_non_passed = find_non_passed_tests(model_rest)

    result["non_passed_tests_exist"] = bool(gold_non_passed or model_non_passed)

    # Pair by order within each category.
    def split_by_type(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        acc: List[Dict[str, Any]] = []
        lat: List[Dict[str, Any]] = []
        for it in items:
            if classify_test(it) == "accuracy":
                acc.append(it)
            else:
                lat.append(it)
        return acc, lat

    g_acc, g_lat = split_by_type(gold_non_passed)
    m_acc, m_lat = split_by_type(model_non_passed)

    for i in range(max(len(g_acc), len(m_acc))):
        ga = g_acc[i] if i < len(g_acc) else {}
        ma = m_acc[i] if i < len(m_acc) else {}
        result["accuracy_tests"].append(compare_accuracy(ga, ma))

    for i in range(max(len(g_lat), len(m_lat))):
        gl = g_lat[i] if i < len(g_lat) else {}
        ml = m_lat[i] if i < len(m_lat) else {}
        result["latency_tests"].append(compare_latency(gl, ml))

    return result


def collect_tasks(gold_root: Path) -> List[Tuple[int, Path]]:
    tasks: List[Tuple[int, Path]] = []
    for task_dir in gold_root.glob("task_*"):
        if not task_dir.is_dir():
            continue
        suffix = task_dir.name.replace("task_", "")
        if not suffix.isdigit():
            continue
        task_id = int(suffix)
        eval_file = task_dir / f"eval_{task_id}.json"
        if eval_file.exists():
            tasks.append((task_id, eval_file))
    tasks.sort(key=lambda x: x[0])
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare run_evaluation_gold and run_evaluation_<model> results.")
    parser.add_argument("--logs-dir", type=Path, default=Path("demo/logs"), help="Logs root containing run_evaluation_* folders")
    parser.add_argument("--gold-dir", type=str, default="run_evaluation_gold_new", help="Gold folder name under logs-dir")
    parser.add_argument("--model-name", type=str, required=True, help="Model name suffix, e.g. gpt => run_evaluation_gpt")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    gold_root = args.logs_dir / args.gold_dir
    model_root = args.logs_dir / f"run_evaluation_{args.model_name}"

    if not gold_root.exists():
        raise FileNotFoundError(f"Gold folder not found: {gold_root}")
    if not model_root.exists():
        raise FileNotFoundError(f"Model folder not found: {model_root}")

    tasks = collect_tasks(gold_root)
    reports: List[Dict[str, Any]] = []
    missing_model_files: List[str] = []

    for task_id, gold_eval in tasks:
        model_eval = model_root / f"task_{task_id}" / f"eval_{task_id}.json"
        if not model_eval.exists():
            missing_model_files.append(str(model_eval))
            continue
        reports.append(analyze_one_task(gold_eval, model_eval))

    summary = {
        "gold_root": str(gold_root),
        "model_root": str(model_root),
        "total_gold_tasks": len(tasks),
        "compared_tasks": len(reports),
        "missing_model_files": missing_model_files,
        "reports": reports,
    }

    output_path = args.output or (args.logs_dir / f"res_analysis_{args.model_name}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Compared {len(reports)} tasks. Output: {output_path}")
    if missing_model_files:
        print(f"[WARN] Missing {len(missing_model_files)} model eval files.")


if __name__ == "__main__":
    main()
