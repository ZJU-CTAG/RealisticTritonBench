# Appendix

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




