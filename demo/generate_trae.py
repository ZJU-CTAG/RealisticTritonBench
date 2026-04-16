# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import argparse
import io
import json
import shutil
import subprocess
import tarfile
import traceback
import docker
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from docker.types import DeviceRequest
from typing import Any

from docker import DockerClient, from_env
from docker.errors import ImageNotFound
from docker.models.containers import Container
from tqdm import tqdm

from utils.utils import BENCHMARK_CONFIG, docker_exec
from utils.constants import REPO_TO_INSTALL_NAME


class BenchmarkEvaluation:
    """
    Main class for running experiments and evaluations.
    Handles Docker image management, environment preparation, patch generation, and evaluation.
    """

    def __init__(
        self,
        benchmark: str,
        working_dir: str,
        trae_config_file_name: str,
        dataset: str = "SWE-bench_Verified",
        docker_env_config: str = "",
        run_id: str = "trae-agent",
        max_workers: int = 4,
        instance_ids: list[str] | None = None,
    ):
        """
        Initialize the BenchmarkEvaluation class.

        Args:
            benchmark: Benchmark name.
            working_dir: Path for workspace (used for temp files and artifacts).
            trae_config_file_name: Path to Trae config file.
            dataset: Dataset name.
            docker_env_config: Path to Docker environment config file.
            run_id: Unique run identifier.
            max_workers: Maximum number of parallel workers.
            instance_ids: List of instance IDs to run (optional).
        """
        self.config = BENCHMARK_CONFIG[benchmark]
        self.dataset_name = dataset

        self.benchmark = benchmark
        self.dataset = self.config.load_dataset(self.dataset_name)
        self.docker_client: DockerClient = from_env()

        self.working_dir = Path(working_dir)
        self.run_id = run_id
        self.max_workers = max_workers
        if instance_ids is None:
            instance_ids = [instance["task_id"] for instance in self.dataset]
        else:
            self.instance_ids = instance_ids

        if docker_env_config != "":
            with open(docker_env_config, "r") as f:
                self.docker_env_config: dict[str, dict[str, str]] = json.load(f)
        else:
            self.docker_env_config = {}

        self.working_dir.mkdir(parents=True, exist_ok=True)

        self.trae_config_file_name = trae_config_file_name
        shutil.copyfile(self.trae_config_file_name, self.working_dir / "trae_config.yaml")

        self.results_dir = Path("results")
        self.task_id = f"{self.dataset_name}_{self.run_id}".replace("/", "_")
        self.task_results_dir = self.results_dir / self.task_id
        self.task_results_dir.mkdir(parents=True, exist_ok=True)


    def prepare_trae_agent_for_one_container(self, instance):
        """
        Build Trae Agent and UV inside a base Ubuntu container.
        Save built artifacts to workspace for later use in experiment containers.
        """
        task_id = instance["task_id"]
        image_name = f"rtbench-instance-{REPO_TO_INSTALL_NAME[instance['repo']]}-{task_id.lower()}:v1"

        try:
            image = self.docker_client.images.get(image_name)
        except Exception:
            raise ImageNotFound(f"Target Image not found: {image_name}")
        
        container_name = f'trae-instance-{task_id}'

        repo_root_path = Path(__file__).resolve().parent / "trae-agent"
        print(repo_root_path)
        assert (repo_root_path / "trae_agent" / "__init__.py").is_file()

        instance_result_dir = self.task_results_dir / task_id
        instance_result_dir.mkdir(parents=True, exist_ok=True)

        self.config.problem_statement(instance, instance_result_dir)

        try:
            container = self.docker_client.containers.get(container_name)
            print(f"Found existing container {container_name}")
        except docker.errors.NotFound:
            container = self.docker_client.containers.run(
                image=image,
                name=container_name,
                user='root',
                shm_size="24g",
                device_requests=[
                    DeviceRequest(
                        count=-1,                # -1 == all GPUs
                        capabilities=[["gpu"]]
                    )
                ],
                command="/bin/bash",
                network="host",
                detach=True,
                tty=True,
                stdin_open=True,
                volumes={
                    self.working_dir.absolute().as_posix(): {"bind": "/trae-workspace", "mode": "rw"},
                    repo_root_path.absolute().as_posix(): {"bind": "/trae-src", "mode": "ro"},
                    instance_result_dir.absolute().as_posix(): {"bind": "/instance-data", "mode": "rw"},
                },
                working_dir="/trae-workspace",
                environment=self.docker_env_config.get("preparation_env", None),
                stream=True,
            )
    
            build_commands = [
                "apt-get update",
                "apt-get install -y curl",
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                "rm -rf /trae-workspace/trae-agent && mkdir /trae-workspace/trae-agent",
                "cp -r -t /trae-workspace/trae-agent/ /trae-src/trae_agent /trae-src/.python-version /trae-src/pyproject.toml /trae-src/uv.lock /trae-src/README.md",
                "cd /trae-workspace/trae-agent && source $HOME/.local/bin/env && uv sync --all-extras",
            ]

            for command in tqdm(
                build_commands, desc="Building trae-agent inside base Docker container"
            ):
                try:
                    new_command = f'/bin/bash -c "{command}"'
                    return_code, output = docker_exec(container, new_command)
                except Exception:
                    print(f"{command} failed.")
                    print(traceback.format_exc())
                    break
                if return_code is not None and return_code != 0:
                    print("Docker exec error. Error message: {}".format(output))
                    container.stop()
                    container.remove()
                    exit(-1)

            for tar_name, src_path in [
                (f"{task_id}-trae-agent.tar", "/trae-workspace/trae-agent"),
                (f"{task_id}-uv.tar", "/root/.local/bin/uv"),
                (f"{task_id}-uv_shared.tar", "/root/.local/share/uv"),
            ]:
                try:
                    with open(self.working_dir / tar_name, "wb") as f:
                        bits, _ = container.get_archive(src_path)
                        for chunk in bits:
                            f.write(chunk)
                except Exception:
                    print(f"Failed to save {tar_name} from container.")
                    container.stop()
                    container.remove()


    def run_one_instance(self, instance_id: str):
        """
        Run patch generation for a single instance.
        All outputs are written directly to the mounted results directory.
        Args:
            instance_id: Instance identifier.
        """
        instance = next((inst for inst in self.dataset if inst["task_id"] == instance_id), None)
        if instance is None:
            print(f"Instance {instance_id} not found.")
            return

        working_dir = self.config.working_dir(instance_id, self.working_dir)

        container_problem_statement_path = "/instance-data/problem_statement.txt"
        container_traj_path = f"/instance-data/{instance_id}.json"

        container_name = f'trae-instance-{instance_id}'

        try:
            container = self.docker_client.containers.get(container_name)
            print(f"Found existing container {container_name}")
        except docker.errors.NotFound:
            raise Exception(f"Container {container_name} not found. Please run preparation step first.")

        command = (
            f"source trae-agent/.venv/bin/activate && "
            f"trae-cli run --file {container_problem_statement_path} "
            f'--working-dir="{working_dir}" '
            f"--config-file trae_config.yaml  "
            f"--trajectory-file {container_traj_path}"
        )
        print(command)
        new_command = f"/bin/bash -c '{command}'"
        try:
            return_code, output = docker_exec(container, new_command)
            if return_code is not None and return_code != 0:
                print("Docker exec error. Error message: {}".format(output))
        except Exception:
            print(f"{command} failed.")
            print(traceback.format_exc())

        # container.stop()
        # container.remove()

    def run_all(self):
        """
        Run patch generation for all instances in the dataset, with parallelism controlled by max_workers.
        """
        instance_ids = [instance["instance_id"] for instance in self.dataset]
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.run_one_instance, instance_id): instance_id
                for instance_id in instance_ids
            }
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Running all instances"
            ):
                instance_id = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Instance {instance_id} failed: {e}")

    def get_all_preds(self, instance_ids: list[str] | None = None):
        """
        Collect all generated patches and write predictions.json to results directory.

        Args:
            instance_ids: List of instance IDs to collect (optional).
        """
        preds: list[dict[str, str]] = []
        if not instance_ids:
            instance_ids = [instance["task_id"] for instance in self.dataset]
        for instance_id in instance_ids:
            patch_path = self.task_results_dir / instance_id / f"{instance_id}.patch"
            if not patch_path.exists():
                continue
            with open(patch_path, "r") as f:
                patch = f.read()
            preds.append(
                {
                    "task_id": instance_id,
                    "model_name_or_path": "trae-agent",
                    "prediction": patch,
                }
            )
        with open(self.task_results_dir / "predictions.json", "w") as f:
            json.dump(preds, f)


def main():
    """
    Main entry point for benchmark evaluation script.
    Parses command-line arguments and runs patch generation and/or evaluation.
    """
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--benchmark", type=str, default="RTbench", help="Benchmark name."
    )
    argument_parser.add_argument(
        "--dataset", type=str, default="RTbench", help="Dataset name."
    )
    argument_parser.add_argument(
        "--working-dir", type=str, default="./trae-workspace", help="Workspace directory."
    )
    argument_parser.add_argument(
        "--instance_ids",
        nargs="+",
        type=str,
        help="Instance IDs to run (space separated).",
    )
    argument_parser.add_argument(
        "--config-file", type=str, default="trae_config.yaml", help="Trae agent config file path."
    )
    argument_parser.add_argument(
        "--docker-env-config", type=str, default="trae_docker_env.json", required=False, help="Docker env config file."
    )

    argument_parser.add_argument(
        "--max_workers", type=int, default=4, help="Maximum number of parallel workers."
    )

    args = argument_parser.parse_args()

    # Trae Agent preparation
    evaluation = BenchmarkEvaluation(
        benchmark=args.benchmark,
        dataset=args.dataset,
        working_dir=args.working_dir,
        trae_config_file_name=args.config_file,
        docker_env_config=args.docker_env_config,
        max_workers=args.max_workers,
        instance_ids=args.instance_ids,
    )

    for instance_id in evaluation.instance_ids:
        print(f"[INFO] Started preparing Trae Agent for instance {instance_id}.")
        instance = next((inst for inst in evaluation.dataset if inst["task_id"] == str(instance_id)), None)
        if instance is None:
            print(f"Instance {instance_id} not found.")
            continue
        evaluation.prepare_trae_agent_for_one_container(instance)
        print(f"[INFO] Finished preparing Trae Agent for instance {instance_id}.")
    
    # Patch generation
    with ThreadPoolExecutor(max_workers=evaluation.max_workers) as executor:
        futures = {
            executor.submit(evaluation.run_one_instance, instance_id): instance_id
            for instance_id in evaluation.instance_ids
        }
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Running all instances"
        ):
            
            instance_id = futures[future]
            try:
                print(f"[INFO] Started running Trae Agent for instance {instance_id}.")
                future.result()
                print(f"[INFO] Finished running Trae Agent for instance {instance_id}.")
            except Exception as e:
                print(f"Instance {instance_id} failed: {e}")

    # for instance_id in tqdm(evaluation.instance_ids, desc="Running Trae Agent"):
    #     print(f"[INFO] Started running Trae Agent for instance {instance_id}.")
    #     evaluation.run_one_instance(instance_id)
    #     print(f"[INFO] Finished running Trae Agent for instance {instance_id}.")

    evaluation.get_all_preds(evaluation.instance_ids)

if __name__ == "__main__":
    main()