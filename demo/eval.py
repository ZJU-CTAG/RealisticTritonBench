import argparse
import json
import os
import docker
import subprocess
import tempfile
import shutil
import time
from typing import Dict, List, Any
from pathlib import Path

from utils.utils import _load_dataset, kill_all_gpu_processes, omit_warning_in_stderr
from utils.python import VLLM_CONFIG
from utils.parser import result_parser
from evaluation.docker_build import build_base_image, build_repo_image, build_instance_image
from evaluation.docker_utils import build_container, copy_to_container, exec_run_with_timeout, exec_run_with_stream_out

from utils.constants import RUN_EVALUATION_LOG_DIR, HTTP_PROXY, HTTPS_PROXY, GIT_PROXY_SET_COMMAND

def run_instance(
    client: docker.DockerClient,
    instance_id, 
    data: Dict,
    image_name: str,
    predictions: Dict,
    log_dir: Path,
    force_rebuild: bool = False,
    timeout: int = 300,
    accuracy_timeout: int = 600,
    latency_timeout: int = 600
):
    # pass
    '''
    Run a single instance with the given prediction.
    '''
    specs = data['targets']
    spec_file = log_dir / "specs.json"
    with spec_file.open("w", encoding="utf-8") as f:
        json.dump(specs, f, ensure_ascii=False, indent=2)
    
    prediction_file = log_dir / "predictions.json"
    with prediction_file.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)

    # Run Docker container
    image_name_prefix = image_name.split(":")[0]
    container_name = f'instance-{instance_id}-{image_name_prefix}'
    try:
        existing_container = client.containers.get(container_name)

        print(f"Found existing container {container_name}")
        if existing_container and force_rebuild:
            print("Force Rebuilding container...")
            # existing_container.stop(timeout=0)
            # existing_container.remove(force=True)

            container = build_container(
                client=client,
                image_name=image_name,
                container_name=container_name,
            )
        else:
            container = existing_container

    except docker.errors.NotFound:
        container = build_container(
            client=client,
            image_name=image_name,
            container_name=container_name
        )

    except Exception as e:
        print(f"[ERROR] Failed to run container {container_name}: {e}")
  
    container.start()

    # Test GPU 
    print(f"[INFO] Testing GPU availability inside the container...")
    gpu_test_cmd = "nvidia-smi"
    res = container.exec_run(gpu_test_cmd, demux=True)
    stdout, stderr = res.output

    if stderr and len(stderr) > 0:
        print(f"[INFO] GPU Test Command Error (if any):\n{stderr.decode('utf-8') if stderr else ''}")
        raise Exception("GPU is unavailable.")
    else:
        print(f"[INFO] GPU Test Command completed successfully.")
        print(stdout.decode('utf-8') if stdout else '')


    # Install python package
    print(f"[INFO] Installing pre-packages inside the container...")
    config = VLLM_CONFIG[data["base_tag"]]
    print(config)
    
    packages = config["pip_packages"]
    install = config["install"]

    cmd = f"pip install -v -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple {' '.join([f'\"{p}\"' for p in packages])}"
    print(f"[INFO] cmd: {cmd}")

    res = exec_run_with_stream_out(
        container=container,
        cmd = cmd
    )

    stdout, stderr = res
    stderr = omit_warning_in_stderr(stderr)

    if stderr and len(stderr) > 0:
        print(f"[INFO] Package Pre-Installation Error (if any):\n{stderr.encode('utf-8') if stderr else ''}")
        raise Exception("Pre-Package installation failed.")
    else:
        print(f"[INFO] Package Pre-Installation completed successfully.")

    print("[INFO] Installing repo inside the container...")

    cmd = f"{GIT_PROXY_SET_COMMAND} && {install}"
    print("[INFO] cmd:", cmd)

    res = exec_run_with_stream_out(
        container=container,
        cmd=cmd
    )

    stdout, stderr = res
    stderr = omit_warning_in_stderr(stderr)

    if stderr and len(stderr) > 0:
        print(f"[INFO] Repo Installation Error (if any):\n{stderr.encode('utf-8') if stderr else ''}")
        raise Exception("Repo installation failed.")
    else:
        print(f"[INFO] Repo Installation completed successfully.")

    copy_to_container(
        container=container,
        src = Path("utils/replace_funcs_eval.py"),
        dst = Path("/workspace/replace_funcs_eval.py")
    )

    copy_to_container(
        container=container,
        src = spec_file,
        dst = Path("/workspace/specs.json")
    )

    copy_to_container(
        container=container,
        src = prediction_file,
        dst = Path("/workspace/predictions.json")
    )

    # Apply function replacements inside the container
    cmd_res = container.exec_run("python /workspace/replace_funcs_eval.py --specs /workspace/specs.json --predictions /workspace/predictions.json", workdir=f"/workspace/{data['repo']}", demux=True)

    stdout, stderr = cmd_res.output

    stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
    stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""

    if stderr and len(stderr) > 0:
        print(f"[INFO] replace_funcs_eval.py encountered errors:\n{stderr_text}")
    else:
        print(f"[INFO] replace_funcs_eval.py completed successfully.]n{stdout_text}")

    if cmd_res.exit_code != 0:
        print(f"[ERROR] Failed to apply function replacements for instance {instance_id}")
        print(f"[ERROR] Output: {cmd_res.output.decode('utf-8')}")
    else:
        print(f"[INFO] Successfully applied function replacements for instance {instance_id}")

    
    # Run Tests from the data
    tests_scripts = data['test_scripts']

    unit_tests = []
    accuracy_test = None
    latency_test = None
    other_tests = []

    serving_command = None

    for id, command in tests_scripts.items():
        if id == "serve":
            serving_command = command
        elif command.startswith("pytest"):
            unit_tests.append({
                "id": id,
                "command": command
            })
        elif command.startswith("lm_eval"):
            accuracy_test = {
                "id": id,
                "command": command
            }
        elif command.startswith("vllm bench serve"):
            latency_test = {
                "id": id,
                "command": command
            }
        else:
            other_tests.append({
                "id": id,
                "command": command
            })

    unit_results = []
    accuracy_result = None
    latency_result = None
    other_tests_results = []

    # 1. pytest tests
    if unit_tests:
        print(f"[INFO] Running unit tests...")
        for test in unit_tests:
            test_cmd = f"cd /workspace/{data['repo']} conda run -n testbed --no-capture-output {test['command']}"

            print(f"test cmd {test['id']}: {test_cmd}")

            stdout, stderr = exec_run_with_stream_out(
                container = container,
                cmd = test_cmd,
            )

            print(f"test output {test['id']}: {stdout}")
        
            unit_results.append({
                "test_id": test["id"],
                "output": stdout,
            })
    else:
        print(f"[INFO] No unit tests to run.")


    # 2. accuracy test
    if accuracy_test:
        print(f"[INFO] Running accuracy test...")
        test_cmd = f" conda run -n testbed  --no-capture-output {accuracy_test['command']}"

        print(f"test cmd {accuracy_test['id']}: {test_cmd}")

        stdout, stderr = exec_run_with_stream_out(
            container = container,
            cmd = test_cmd,
        )

        accuracy_result = {
            "test_id": accuracy_test["id"],
            "output": stdout,
        }

        # print(f"test output {accuracy_test['id']}: {stdout}")
    else:
        print(f"[INFO] No accuracy test to run.")
    

    # 3. latency test
    if latency_test:
        print(f"[INFO] Running latency test...")
        # Serving
        serving_cmd = f"source ~/.bashrc &&  conda run -n testbed --no-capture-output {serving_command}"
        print(f"[Info] Starting serving command: {serving_cmd}")

        serve_res = container.exec_run(
            ["bash", "-c", serving_cmd],
            demux=True,
            detach=True
        )

        print(f"[INFO] Waiting for vllm server to be ready...")        

        ready = False
        for i in range(60):
            print(f"Testing num: {i}")
            probe_cmd = "curl -f http://127.0.0.1:9010/v1/models"
            
            probe_res = container.exec_run(
                ["bash", "-c", probe_cmd],
                demux=True
            )

            print(f"probe_res: {probe_res}")

            if probe_res.exit_code == 0:
                stdout, stderr = probe_res.output

                print(f"stdout: {stdout}")

                ready = True
                print("[INFO] vllm server is ready!")
                break

            time.sleep(2)
        if not ready:
            raise RuntimeError("vllm server failed to start within the expected time.")
        
        clear_flag = False

        try:
            test_cmd = f"conda run -n testbed --no-capture-output {latency_test['command']}"

            print(f"test cmd {latency_test['id']}: {test_cmd}")

            stdout, stderr = exec_run_with_stream_out(
                container = container,
                cmd = test_cmd,
            )

            latency_result = {
                "test_id": latency_test["id"],  
                "output": stdout,
            }

            
        except Exception as e:
            kill_all_gpu_processes()
            clear_flag = True
            raise Exception(f"Latency test execution failed. {e}")
    else:
        print(f"[INFO] No latency test to run.")
        
    # collect results
    result = {
        "task_id": data['task_id'],
        "instance_id": instance_id,
        "unit_tests_result": unit_results,
        "accuracy_test_result": accuracy_result,
        "latency_test_result": latency_result,
        "other_tests_result": other_tests_results
    }

    print(f"[INFO] {instance_id} results: {result}")

    with open("logs/test_results.txt", "w", encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if not clear_flag:
        kill_all_gpu_processes()
        clear_flag = True
     

    return result


# -------- Main Logic demo for evaluation --------
def main(args):
    # ---------------
    # 1. Load dataset
    print(f"--------- Loading dataset from {args.dataset_path}")
    dataset = _load_dataset(local_path=args.dataset_path)

    # Filter dataset based on task_id
    if args.task_id:
        dataset = [item for item in dataset if item["task_id"] in args.task_id]
    
    print(f"{len(dataset)} tasks loaded from dataset")

    # ----------------
    # 2. Build Image and container for each task
    print(f"--------- Building images for all tasks") 
    docker_client = docker.from_env()
    base_full_image = build_base_image(
        client=docker_client,
        base_image_name="rtbench-base",
        base_image_tag="latest"
    )

    base_image = base_full_image.split(":")[0]

    for idx, data in enumerate(dataset):
        print(f"Building image for task {data['task_id']}")

        if data["repo"] == "vllm-project/vllm":
            repo = "vllm"

        repo_full_image = build_repo_image(
            client=docker_client,
            data=data,
            base_image_name=base_image,
            repo_image_name=f"rtbench-{repo}",
            repo_image_tag="latest"
        )

        repo_image = repo_full_image.split(":")[0]

        instance_image = build_instance_image(
            client=docker_client,
            data=data,
            repo_image_name=repo_image,
            repo_image_tag="latest",
            instance_image_name=f"rtbench-instance-{repo}-{data['task_id']}",
            instance_image_tag="latest",
            force_rebuild=False
        )
       
    # ----------------
    # 3. Run each task
    print(f"--------- Evaluating tasks and generating report")
    results = []
    for idx, data in enumerate(dataset):
        print(f"Evaluating task {data['task_id']}")

        if data["repo"] == "vllm-project/vllm":
            repo = "vllm"

        instance_image_name = f"rtbench-instance-{repo}-{data['task_id']}:latest"

        # Load predictions
        if args.use_gold:
            predictions = data["gold_patch"]
        else:
            pred_file_path = os.path.join(args.predictions_path, f"{data['task_id']}_prediction.json")
            with open(pred_file_path, "r") as f:
                predictions = json.load(f)

        log_dir = RUN_EVALUATION_LOG_DIR / f"task_{data['task_id']}"
        log_dir.mkdir(parents=True, exist_ok=True)

        result = run_instance(
            client=docker_client,
            instance_id=data['task_id'],
            data=data,
            image_name=instance_image_name,
            predictions=predictions,
            log_dir=log_dir,
            timeout=args.timeout
        )

        results.append(result)
    
    with open("/home/jinjunhuang/RTBench/RTBench/demo/logs/test_results.txt", "r") as f:
        result = json.load(f)

    results.append(result)

    # 4. Evaluate Results and Save report
    print(f"--------- Generating evaluation report")
    for result in results:
        single_report = result_parser(result)  

        log_dir = RUN_EVALUATION_LOG_DIR / f"task_{result['task_id']}"
        log_dir.mkdir(parents=True, exist_ok=True)

        report_file = log_dir / f"eval_{result['instance_id']}.json"
        with report_file.open("w", encoding="utf-8") as f:
            json.dump(single_report, f, ensure_ascii=False, indent=2)
        
    # Save overall results
    output_file = Path(args.output_file)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Evaluation completed. Results saved to {output_file}")
    
  



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main evaluation script")
    parser.add_argument(
        "--predictions_path", type=str, default="./results", help="Path to prediction file"
    )
    parser.add_argument(
        "--dataset_path", type=str, default="/home/jinjunhuang/RTBench/RTBench/data/problems.json", help="Path to the RTBench dataset"
    )
    parser.add_argument(
        "--task_id", type=str, nargs="+", help="Task identifier"
    )
    parser.add_argument(
        "--output_file", type=str, default="./eval_results.json", help="Path to save evaluation results"
    )
    parser.add_argument(
        "--timeout", type=int, default=600, help="Timeout for each test in seconds"
    )
    parser.add_argument(
        "--use_gold", action="store_true", help="Use golden patch predictions from the dataset"
    )
    args = parser.parse_args()

    main(args)