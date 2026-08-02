# Appendix

## Impact of Agent Scaffold

**Performance of GPT-5.4 with Codex on RealisticTritonBench**

| Metric | Opt. | Mod. | New | Overall |
|:--|--:|--:|--:|--:|
| Success (%) | 38.46 | 57.14 | 27.27 | 38.71 |
| Applied (%) | 100.00 | 100.00 | 100.00 | 100.00 |
| FTP (%) | 92.31 | 71.43 | 63.64 | 77.42 |
| UTP (%) | 99.31 | 74.29 | 63.64 | 81.00 |
| NR (%) | 50.00 | 50.00 | 83.33 | 60.00 |
| $S_{\text{TTFT}}$ | 1.3915 | 1.0341 | 0.8892 | 1.1900 |
| $S_{\text{TPOT}}$ | 0.9709 | 1.0160 | 0.9517 | 0.9688 |

In the main experiments, we use mini-SWE-agent as the fixed scaffold so that the comparison focuses on model capability. To examine the effect of a native scaffold—i.e., an agent scaffold developed by the model vendor and co-optimized with the model—we additionally evaluated GPT-5.4 using Codex. The table above shows the performance comparison.

Compared with GPT-5.4 under mini-SWE-agent, using Codex improves GPT-5.4's overall success rate from 16.13% to 38.71%. This improvement may come from better model-scaffold alignment: the native harness may better match GPT-5.4's tool-use behavior and thinking pattern, enabling more effective environment interaction and execution feedback.

However, even with Codex, the framework-level metrics remain weak: NR reaches only 60.00%, and $S_{\text{TPOT}}$ remains below 1 (0.9688), meaning that the generated kernels still degrade model accuracy and increase inference latency on many tasks. This indicates that realistic Triton development tasks remain challenging. Models still struggle to meet numerical robustness and end-to-end latency requirements. This supports the need for framework-level evaluation.

## Sensitivity of Evaluation Metrics

Our task success criterion involves a tolerance threshold of $0.98$ on the end-to-end latency speedups, $S_{\text{TTFT}}$ and $S_{\text{TPOT}}$. To examine whether our conclusions are sensitive to this choice, we recompute the average success rate under different thresholds, as shown in the table below.

Relaxing the threshold from $0.98$ to $0.95$ only increases the average success rate from 18.71% to 20.00%, while tightening the threshold to $0.99$ reduces the average success rate to 11.61%. This indicates that our results are robust to moderate threshold relaxation, while the stricter threshold $0.99$ is more affected by latency noise.

**Table: Sensitivity of the average success rate to the latency speedup threshold.**

| Threshold | Average Success Rate |
|---:|---:|
| 0.95 | 20.00% |
| 0.98 | 18.71% |
| 0.99 | 11.61% |

## Data Contamination Analysis

Since RealisticTritonBench is constructed from historical PRs in public repositories, the evaluated models may have been exposed to the gold patches during pre-training. We analyze this risk from two perspectives: the potential contamination rate based on model training cutoffs and the textual similarity between generated patches and gold patches.

First, we compare PR merge dates with model training cutoffs where available, and also report conservative release-date-based results in the table below. Among the evaluated models, only Gemini-3.1-Pro-Preview discloses its training cutoff, 2025-01-01, under which merely 9.68% of the tasks were merged before the cutoff and are potentially contaminated. This suggests that Gemini-3.1-Pro-Preview has little contamination risk. For other models whose cutoffs are undisclosed, we conservatively use their release dates as an upper bound of the training data horizon, under which almost all tasks, 99.19% on average, would be considered potentially contaminated. However, if memorization were the dominant factor, models with higher contamination exposure would be expected to substantially outperform Gemini-3.1-Pro-Preview. In practice, the success rates of other models are close to that of Gemini-3.1-Pro-Preview, which suggests that memorization is unlikely to be the dominant factor behind other models' performance.

To further investigate the impact of memorization, we measure the textual similarity between the generated patches and the original gold patches using the normalized character-level Levenshtein distance. As shown in the table below, the average normalized edit distance across all models is 0.3164, with per-model averages ranging from 0.2688 for Gemini-3.1-Pro-Preview to 0.3597 for Deepseek-V3.2 non-reasoning. These distances indicate that the generated solutions differ substantially from the gold patches at the textual level, confirming that the evaluated models are not reproducing memorized patches.

**Table: Release-date-based potential contamination rates and normalized edit distance between generated patches and gold patches.**

| Model | Release Date | Contam. (release) | Edit Dist. |
|---|---:|---:|---:|
| Deepseek-V3.2 (non-reasoning) | 2025-12-01 | 96.77% | 0.3597 |
| Deepseek-V3.2 (reasoning) | 2025-12-01 | 96.77% | 0.2836 |
| Qwen3.5-397B-A17B | 2026-03-09 | 100.00% | 0.3160 |
| Gemini-3.1-Pro-Preview | 2026-02-19 | 100.00% | 0.2688 |
| GPT-5.4 | 2026-03-05 | 100.00% | 0.3540 |
| **Average** | -- | **99.19%** | **0.3164** |




