# RealisticTritonBench

RealisticTritonBench is a benchmark for evaluating whether language-model
agents can repair or implement realistic Triton kernels in an end-to-end
framework setting. The benchmark is built from real pull requests and
includes task metadata, source/test files, Docker-based evaluation utilities,
agent-generation scripts, and analysis scripts for reporting correctness and
latency metrics. This guide describes the repository layout and the standard
workflow for reproducing kernel generation, evaluation, and result analysis.

## File Structure

```text
RealisticTritonBench/
|-- appendix/
|   `-- appendix.md                 # Online appendix material.
|-- collect/                        # Scripts for collecting and building the dataset.
|   |-- build_dataset.py
|   |-- print_pulls.py
|   |-- tf_to_excel.py
|   `-- utils.py
|-- data/                           # Dataset metadata, filtered PRs, and task assets.
|   |-- problems.json               # Main task metadata used by evaluation/analysis.
|   |-- problems_template.json
|   |-- filter_dataset.jsonl
|   |-- bug_fix/
|   |-- new_op/
|   `-- optimization/
|-- demo/                           # Main replication entry point.
|   |-- eval.py                     # Docker-based task evaluation.
|   |-- generate_miniswe.py         # mini-SWE-agent generation script.
|   |-- requirements.txt
|   |-- config/                     # Agent configuration files.
|   |-- dockerfiles/                # Docker image definitions.
|   |-- evaluation/                 # Evaluation and test-spec utilities.
|   |-- mini-swe-agent/             # Local mini-SWE-agent checkout.
|   |-- scripts/                    # Runtime scripts used inside evaluation.
|   |-- utils/                      # Patch extraction/replacement helpers.
|   `-- results/                    # Example/generated model trajectories and outputs.
|-- scripts/                        # Repository-level maintenance scripts.
|-- construct_dataset.py            # Dataset construction entry point.
|-- context.py                      # Context/template data used by the benchmark.
|-- problems.json                   # Exported task metadata at repository root.
|-- output.xlsx                     # Spreadsheet version of task/output metadata.
`-- readme.md
```

## Online Appendix

The appendix is listed in `/appendix/appendix.md`

## Unpack the Repository

If you received the benchmark as a compressed artifact, unpack it first:

```bash
tar -xzvf RTbench.tar.gz
cd RealisticTritonBench
```

## Environment Setup

Create a Python environment, install the replication dependencies, and install
the bundled mini-SWE-agent package:

```bash
conda create -n rtbench python=3.12
conda activate rtbench

cd demo
pip install -r requirements.txt
cd mini-swe-agent && pip install -e .
cd ..
```

Before running kernel generation or evaluation, build the Docker containers and
download the required models/datasets for the tasks:

```bash
# Build all task containers.
python eval.py --skip_evaluation

# Download models from Hugging Face. The script uses HF_TOKEN.
export HF_TOKEN="YOUR_HF_TOKEN"
bash utils/download_model.sh
```

## Kernel Generation

Use `generate_miniswe.py` to generate model predictions for all tasks.

Example:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"

python generate_miniswe.py \
  --subset rtbench \
  --from-local True \
  --workers 6 \
  --environment-class docker \
  --output results \
  --model deepseek-chat \
  --model-class litellm
```

Generation outputs are written in the following format:

```text
results/RTbench_{model_name}_minisweagent/
```

The main aggregated prediction file is:

```text
preds.json
```

## Evaluation

`eval.py` supports two evaluation modes:

1. Gold patch evaluation with `--use_gold`.
2. Model prediction evaluation with `--predictions_path`.

### Gold Patch Evaluation

```bash
python eval.py \
  --use_gold \
  --skip_install \
  --skip_image_build
```

### Model Prediction Evaluation

`eval.py` expects per-task prediction files named:

```text
{predictions_path}/{task_id}_prediction.json
```

Convert `preds.json` into per-task prediction files first. The repository
includes an `extract.py` helper in each example result directory; run it from
the target result directory or copy it into a newly generated result directory.

```bash
python results/RTbench_deepseek-chat_minisweagent/extract.py
```

Then run evaluation:

```bash
python eval.py \
  --predictions_path results/RTbench_deepseek-chat_minisweagent \
  --skip_install \
  --skip_image_build
```

Evaluation outputs are written under:

```text
logs/run_evaluation
```

## Result Analysis

Evaluation logs are organized as:

```text
logs/run_evaluation_gold/task_{id}/eval_{id}.json
logs/run_evaluation_{model_name}/task_{id}/eval_{id}.json
```

If your logs are stored in another directory, replace `logs` with that path in
the commands below.

Set the log directory and model name:

```bash
LOGS_DIR=logs_backup
MODEL_NAME=ds_chat
```

Compare model results against gold:

```bash
python res_analysis.py \
  --logs-dir ${LOGS_DIR} \
  --gold-dir logs/run_evaluation_gold_new \
  --model-name ${MODEL_NAME} \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json
```

Aggregate overall metrics:

```bash
python aggregate_metrics.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}_avg_metrics.json
```

Compute the overall success ratio:

```bash
python calc_success_ratio.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --output ${LOGS_DIR}/success_ratio_${MODEL_NAME}.json
```

Optional: compute type-level metrics and success ratios. The supported filters
include `optimization`, `new_op`, and `modificaton`; `modificaton` is a combined
filter used by the analysis scripts for modification-style tasks.

```bash
python aggregate_metrics_type.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --task-type optimization \
  --problems ../data/problems.json \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}_avg_metrics_optimization.json

python calc_success_ratio_type.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --task-type optimization \
  --problems ../data/problems.json \
  --output ${LOGS_DIR}/success_ratio_${MODEL_NAME}.json
```

Replace `optimization` with `new_op` or `modificaton` to analyze other task
groups.
