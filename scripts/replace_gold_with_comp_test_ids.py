#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def collect_json_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("*.json") if p.is_file())


def collect_test_id_nodes(obj: Any, nodes: List[Dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        if "test_id" in obj:
            nodes.append(obj)
        for value in obj.values():
            collect_test_id_nodes(value, nodes)
    elif isinstance(obj, list):
        for item in obj:
            collect_test_id_nodes(item, nodes)


def replace_test_id_nodes(gold_obj: Any, comp_obj: Any) -> tuple[Any, int, int]:
    gold_nodes: List[Dict[str, Any]] = []
    comp_nodes: List[Dict[str, Any]] = []
    collect_test_id_nodes(gold_obj, gold_nodes)
    collect_test_id_nodes(comp_obj, comp_nodes)

    comp_by_test_id: Dict[str, Dict[str, Any]] = {}
    for node in comp_nodes:
        comp_by_test_id[str(node.get("test_id"))] = node

    replaced = 0
    unmatched = 0
    for gold_node in gold_nodes:
        test_id = str(gold_node.get("test_id"))
        comp_node = comp_by_test_id.get(test_id)
        if comp_node is None:
            unmatched += 1
            continue
        gold_node.clear()
        gold_node.update(comp_node)
        replaced += 1
    return gold_obj, replaced, unmatched


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Match same-name JSON files under comp/gold trees, replace gold "
            "test_id-bearing entries with corresponding entries from comp, and "
            "write into a new output directory."
        )
    )
    parser.add_argument(
        "--comp",
        default="demo/logs/run_evaluation_comp",
        help="Path to comp directory.",
    )
    parser.add_argument(
        "--gold",
        default="demo/logs/run_evaluation_gold",
        help="Path to gold directory.",
    )
    parser.add_argument(
        "--out",
        default="demo/logs/run_evaluation_gold_new",
        help="Path to output directory.",
    )
    args = parser.parse_args()

    comp_root = Path(args.comp).resolve()
    gold_root = Path(args.gold).resolve()
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    comp_files = collect_json_files(comp_root)
    if not comp_files:
        print(f"[ERROR] No JSON files found in comp dir: {comp_root}")
        return 1

    processed = 0
    replaced_files = 0
    missing_in_gold = 0
    mismatch_files = 0

    for comp_file in comp_files:
        rel = comp_file.relative_to(comp_root)
        gold_file = gold_root / rel
        if not gold_file.exists():
            missing_in_gold += 1
            print(f"[WARN] Missing in gold: {rel}")
            continue

        try:
            with comp_file.open("r", encoding="utf-8") as f:
                comp_obj = json.load(f)
            with gold_file.open("r", encoding="utf-8") as f:
                gold_obj = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read JSON {rel}: {e}")
            continue

        new_obj, replaced, unmatched = replace_test_id_nodes(gold_obj, comp_obj)
        if unmatched != 0:
            mismatch_files += 1
            print(
                f"[WARN] unmatched test_id in gold {rel}: unmatched={unmatched}"
            )
        if replaced > 0:
            replaced_files += 1

        out_file = out_root / rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(new_obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
        processed += 1

    print(
        f"[DONE] processed={processed}, replaced_files={replaced_files}, "
        f"missing_in_gold={missing_in_gold}, mismatch_files={mismatch_files}, "
        f"out={out_root}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
