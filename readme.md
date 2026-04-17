# RealisticTritonBench Replication Guide

## Unzip the repo

tar -xzvf RTbench.tar.gz

## Environment Setup

Follow these steps to setup the environment for RealisticTritonBench

```bash
# Download the packages for the repo
conda create -n rtbench python=3.12
conda activate rtbench

pip install -r requirements.txt
cd mini-swe-agent && pip install -e .
```

Before running kernel generation and evaluation, you need to build the Docker container and download all the models involved for each task.

```bash
# Build all the containers
python eval.py --skip_evaluation

# Download models and datsets from huggingface
bash scripts/download_necessities.sh
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

Key points:

- Output directory format: `results/RTbench_{model_name}_minisweagent/`
- Main output file: `preds.json`

## Evaluation

`eval.py` supports two evaluation modes:

1. Gold patch evaluation (`--use_gold`)
2. Model prediction evaluation (`--predictions_path`)

### 1) Gold patch evaluation

```bash
python eval.py \
  --use_gold \
  --skip_install \
  --skip_image_build
```

### 2) Evaluate generated predictions

`eval.py` expects per-task files named:

- `{predictions_path}/{task_id}_prediction.json`

Convert `preds.json` first:

```bash
python utils/extract.py results/RTbench_deepseek-chat_minisweagent
```

Then run evaluation:

```bash
python eval.py \
  --predictions_path results/RTbench_deepseek-chat_minisweagent \
  --skip_install \
  --skip_image_build
```

Key points:

- Output directory format: `logs/run_evaluation`

### 3) Data analysis

Evaluation logs are organized as:

- `logs/run_evaluation_gold/task_{id}/eval_{id}.json`
- `logs/run_evaluation_{model_name}/task_{id}/eval_{id}.json`

If your logs are in another folder (for example `logs_backup`), replace `logs` with that path in commands below.

Set variables:

```bash
LOGS_DIR=logs_backup
MODEL_NAME=ds_chat
```

Compare model results against gold:

```bash
python scripts/res_analysis.py \
  --logs-dir ${LOGS_DIR} \
  --gold-dir logs/run_evaluation_gold_new \
  --model-name ${MODEL_NAME} \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json
```

Aggregate overall metrics:

```bash
python scripts/aggregate_metrics.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}_avg_metrics.json
```

Compute overall success ratio:

```bash
python scripts/calc_success_ratio.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --output ${LOGS_DIR}/success_ratio_${MODEL_NAME}.json
```

Optional: type-level metrics/success ratio (`modificaton`, `new_op`, `optimization`):

```bash
python scripts/aggregate_metrics_type.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --task-type optimization \
  --problems data/problems.json \
  --output ${LOGS_DIR}/res_analysis_${MODEL_NAME}_avg_metrics_optimization.json

python scripts/calc_success_ratio_type.py \
  --input ${LOGS_DIR}/res_analysis_${MODEL_NAME}.json \
  --task-type optimization \
  --problems data/problems.json \
  --output ${LOGS_DIR}/success_ratio_${MODEL_NAME}.json
```

Replace `optimization` with `modificaton` or `new_op` to analyze other task types.

