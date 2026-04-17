"""
Build dataset by filter raw PRs from GitHub repositories.
1. Filter PRs that are closed and merged by keyword
"""

import json
import argparse
import logging
import os
import re

from .utils import (
    get_all_tags_with_time, 
    extract_patches,
    find_nearest_tag_by_time,
    call_llm,
    extract_code_block,
    SUMMARY_PR_TEMPLATE,
    REPO_TAG_FILES,
    Repo
)

from datetime import datetime
from typing import Optional, Dict, List, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

STATES = ["closed", "merged", "open"]
KEYWORDS = ["triton", "op", "ops", "operator", "kernel", "fused", "implementation"]
NO_WORDS = ["tune", "tuning", "CI", "doc", "documentation", "CPU", "config", "tunings", "configs", "rocm", "tpu", "marlin", "cutlass", "revert"]
CODE_CHANGE_KEYWORDS = ["@triton.jit", "triton", "tl.constexpr", "tl."]

RAW_DATA_PATH = "/home/jinjunhuang/RTBench/RTBench/data/raw_prs.jsonl"
OPEN_RAW_DATA_PATH = "/home/jinjunhuang/RTBench/RTBench/data/open_raw_prs.jsonl"
FILTER_BY_TEXT_RAW_DATA_PATH = "/home/jinjunhuang/RTBench/RTBench/data/filter_by_text_raw_prs.jsonl"
FILTER_BY_CODE_RAW_DATA_PATH = "/home/jinjunhuang/RTBench/RTBench/data/filter_by_code_raw_prs.jsonl"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def keyword_match(text: str, keywords: list[str]) -> bool:
    if not text:
        return False
    
    pattern = re.compile(
        r"\b(" + "|".join(keywords) + r")\b",
        flags=re.IGNORECASE
    )
    return bool(pattern.search(text))

def body_match(text: str, keywords: list[str]) -> bool:
    if not(any(keyword in text for keyword in keywords)):
        return False
    return True

def create_single_task(pr: dict, repo: Repo, tags: List[Dict], client) -> Optional[Dict]:
    """
    Create a single task instance from a PR dictionary.

    Args:
        pr (dict): Pull request data
    """
    title = pr["title"]
    body = pr["body"]

    task_description_prompt = SUMMARY_PR_TEMPLATE.format(
        pr_title=title,
        pr_body=body
    )
    raw_response = call_llm(task_description_prompt, model="deepseek-chat", client=client)
    assert raw_response is not None, "LLM returned None"
    raw_dict = json.loads(extract_code_block(raw_response, "json"))

    pr_summary = raw_dict["PR_summary"]
    task_description = raw_dict["problem_statement"]

    merged_at = pr["merged_at"]
    if not merged_at:
        status = "open"
    else:
        status = "merged"
    created_at = pr["created_at"]

    pr_createed_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    base_tag = find_nearest_tag_by_time(pr_createed_time, tags)

    code_patch = extract_patches(pr, repo)

    return {
        "repo": repo.full_name,
        "pull_number": pr["number"],
        "status": status,
        "head_commit": pr["head"]["sha"],
        "base_commit": pr["base"]["sha"],
        "base_tag": base_tag,
        "name": pr["title"],
        "body": pr["body"],
        "pr_summary": pr_summary,
        "task_description": task_description,
        "patch": code_patch,
        "created_at": created_at,
    }








def filter_by_text(args) -> list[dict]:
    print("---------- Filtering by Text Keywords -------")
    with open(RAW_DATA_PATH, "r") as f:
        raw_data = [json.loads(line) for line in f.readlines()]
    with open(OPEN_RAW_DATA_PATH, "r") as f:
        open_raw_data = [json.loads(line) for line in f.readlines()]

    raw_data.extend(open_raw_data)
    print(f"---------- Total Raw PRs: {len(raw_data)} ----------")
    
    merged_pr = []
    open_pr = []
    
    # Filter PRs
    for pr in tqdm(raw_data, desc="Filtering PRs"):
        title = pr["title"]
        merged_at = pr["merged_at"]
        closed_at = pr["closed_at"]
        draft = pr["draft"]
        body = str(pr["body"])

        # # Debug
        # number = pr.get("number", None)
        # if str(number) != "27291":
        #     continue

        if not keyword_match(title, KEYWORDS):
            continue

        if keyword_match(title, NO_WORDS):
            continue

        if not merged_at and closed_at:
            continue
        if draft:
            continue

        if merged_at:
            merged_pr.append(pr)
        if not merged_at and not closed_at:
            open_pr.append(pr)
        
    print(f"---------- Filtered Merged PRs: {len(merged_pr)} ----------")
    print(f"---------- Filtered Open PRs: {len(open_pr)} ----------")

    os.makedirs(os.path.dirname(FILTER_BY_TEXT_RAW_DATA_PATH), exist_ok=True)
       
    with open("/home/jinjunhuang/RTBench/RTBench/data/filter_numbers_raw_data.txt", "w") as number_file:
        for pr in merged_pr:
            number = pr.get("number", None)
            number_file.write(f"{number}\n")
        for pr in open_pr:
            number = pr.get("number", None)
            number_file.write(f"{number}\n")


def filter_by_code_change(args) -> list[dict]:
    print("---------- Filtering by Code Change -------")
    assert os.path.exists(FILTER_BY_TEXT_RAW_DATA_PATH), f"{FILTER_BY_TEXT_RAW_DATA_PATH} does not exist. Please run filter_by_text first."

    with open(FILTER_BY_TEXT_RAW_DATA_PATH, "r") as f:
        raw_data = [json.loads(line) for line in f.readlines()]

    with open(FILTER_BY_CODE_RAW_DATA_PATH, "r") as f:
        raw_code_data = [json.loads(line) for line in f.readlines()]
    
    example_list = ["24503", "30585"]

    in_text_flag = False
    in_data_flag = False

    for pr in raw_data:
        number = pr.get("number", None)
        if any(str(number) == ex for ex in example_list):
            in_text_flag = True
            break

    for pr in raw_code_data:
        number = pr.get("number", None)
        if any(str(number) == ex for ex in example_list):
            in_data_flag = True
            break
    
    if in_text_flag:
        print("---------- Example Found in raw_text_data -------")
    else:
        print("---------- Example Not Found in raw_text_data -------")

            
    if in_data_flag:
        print("---------- Example Found in raw_code_data -------")
    else:
        print("---------- Example Not Found in raw_code_data -------")

    exit(0)
    def processing_single_pr(pr: dict, args) -> Optional[Tuple[str, dict]]:
        merged_at = pr.get("merged_at")
        closed_at = pr.get("closed_at")

        try:
            patch_fix = extract_patches(pr, args.repo_name)
        except Exception as e:
            print(e)
            return None

        if not patch_fix or not body_match(patch_fix, CODE_CHANGE_KEYWORDS):
            return None

        if merged_at:
            return ("merged", pr)

        if not merged_at and not closed_at:
            return ("open", pr)

        return None

    os.makedirs(os.path.dirname(FILTER_BY_CODE_RAW_DATA_PATH), exist_ok=True)

    merged_dataset = []
    open_dataset = []

    print(f"---------- Total Raw PRs: {len(raw_data)} ----------")

    merged_pr = []
    open_pr = []

    max_workers = 40

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(processing_single_pr, pr, args)
            for pr in raw_data
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Filtering PRs (threaded)"
        ):
            result = future.result()
            if result is None:
                continue

            tag, pr = result
            if tag == "merged":
                merged_pr.append(pr)
            elif tag == "open":
                open_pr.append(pr)
  
        
    print(f"---------- Filtered Merged PRs: {len(merged_pr)} ----------")
    print(f"---------- Filtered Open PRs: {len(open_pr)} ----------")
       
    
    with open(FILTER_BY_CODE_RAW_DATA_PATH, "w") as file:
        for pr in merged_pr:
            print(json.dumps(pr), end="\n", flush=True, file=file)
        for pr in open_pr:
            print(json.dumps(pr), end="\n", flush=True, file=file)
    

def main(args):
    # 1. Filter by keyword in title and body
    filter_by_text(args)

    # 2. Filter by Code change 
    # filter_by_code_change(args)

    # # 3. Build dataset
    # filtered_dataset = []

    # with open(FILTER_BY_TEXT_RAW_DATA_PATH, "r") as f:
    #     raw_data = [json.loads(line) for line in f.readlines()]
    
    # print(f"---------- Total Text-Filtered PRs: {len(raw_data)} ----------")

    # os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # if args.token is None:
    #     args.token = os.environ.get("GITHUB_TOKEN")
    # owner, name = args.repo_name.split("/")
    # repo = Repo(owner, name, token=args.token)

    # print(f"---------- Loaded Repo Tags: {repo.full_name} ----------")
    # if os.path.exists(REPO_TAG_FILES.get(f"{owner}/{name}", f"{name}_tags.json")):
    #     with open(REPO_TAG_FILES.get(f"{owner}/{name}", f"{name}_tags.json"), "r") as f:
    #         tags = json.load(f)
    # else:
    #     tags = get_all_tags_with_time(repo.api, owner, name)
    
    # if os.path.exists(args.output):
    #     print(f"---------- Skip existing seen PRs from {args.output} ----------")
    #     with open(args.output, "r") as file:
    #         seen_prs = [json.loads(line) for line in file.readlines()]
    #     print(f"---------- Seen PRs: {len(seen_prs)} ----------")

    # seen_pr_numbers = set(pr["pull_number"] for pr in seen_prs)
    # raw_data = [pr for pr in raw_data if (pr["number"]) not in seen_pr_numbers]

    # print(f"---------- Remaining PRs to process: {len(raw_data)} ----------")

    # client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    # with ThreadPoolExecutor(max_workers=40) as executor:
    #     futures = [executor.submit(create_single_task, pr, repo, tags, client) for pr in raw_data]

    #     with open(args.output, "a") as file:
    #         for future in tqdm(
    #             as_completed(futures),
    #             total=len(futures),
    #             desc="Processing PRs"
    #         ):
    #             try:
    #                 instance = future.result()
    #                 if instance is not None:
    #                     filtered_dataset.append(instance)
    #                     print(
    #                         json.dumps(instance),
    #                         end="\n",
    #                         flush=True,
    #                         file=file
    #                     )
    #             except Exception:
    #                 import traceback
    #                 traceback.print_exc()

    # print(f"---------- Final Filtered PRs: {len(filtered_dataset)} ----------")
    

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="__doc__")
    argparser.add_argument("--repo_name", type=str, default="vllm-project/vllm",help="Name of the repository")
    argparser.add_argument("--token", type=str, default="", help="GitHub token")
    argparser.add_argument(
        "--output", type=str, default="/home/jinjunhuang/RTBench/RTBench/data/filter_dataset.jsonl", help="Path to save the filtered dataset"
    )
    args = argparser.parse_args()
    main(args)