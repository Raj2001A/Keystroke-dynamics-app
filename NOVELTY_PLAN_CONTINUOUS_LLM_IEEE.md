# NOVELTY_PLAN_CONTINUOUS_LLM_IEEE

## Summary
This plan defines a publication-grade novelty track for this project with primary contribution: continuous keystroke biometric authentication with explicit detection of LLM-assisted or paste attacks.

The evidence bar is strict:
- held-out protocol,
- calibrated thresholds,
- mandatory ablations,
- confidence intervals,
- validity controls,
- reproducibility manifest per run.

## Locked Decisions
- Target venue: IEEE-style paper.
- Novelty scope: continuous authentication + LLM-assisted attack detection.
- Evidence level: strongest evidence.
- Baseline backbone: Type2Branch embeddings as primary.
- Optional secondary backbone: compact mini-model under identical protocol.

## Primary Claims To Defend
1. Continuous authentication protocol over static login verification.
2. Unified online threat model for human impostor takeover + LLM/paste takeover.
3. Operationally valid evaluation stack (xv tune -> xe report, no leakage).
4. Engineering-at-scale contribution (DGX preflight, reproducible manifests, scalable simulation).

## Out Of Scope (Current Paper Cycle)
- Re-claiming original Type2Branch novelty already published in TIFS.
- UI-only novelty claims.
- Qwen-based novelty claim without separate method + full ablation package.

## Implemented Artifacts In This Repo
1. `results_hardened/*` static verification:
- `hardened_metrics.txt`
- `hardened_metrics.json`
- `threshold_curve.csv`
- `score_histogram.png`
- `far_frr_curve.png`
- `per_user_eer.csv`
- `threshold_artifact.json`

2. `results_continuous/*` continuous protocol:
- `continuous_metrics.json`
- `continuous_metrics.txt`
- `continuous_sessions.csv`
- `continuous_detection_delay.png`
- `continuous_llm_roc.png`
- `continuous_llm_calibration.png`

3. Reproducibility:
- `paper_results_manifest.json` via `generate_manifest.py`.

4. Ablation outputs:
- `results_continuous/ablations/ablation_runs.csv`
- `results_continuous/ablations/ablation_summary.csv`
- `results_continuous/ablations/ablation_summary.json`
- `results_continuous/ablations/continuous_policy_tradeoff.png`

## Frozen Public Interfaces
### Continuous evaluator
`python evaluate_continuous.py <dataset> [flags]`

Key flags:
- `--warmup-steps`
- `--attack-steps`
- `--decision-window`
- `--alarm-consecutive`
- `--sessions-per-user`
- `--max-users-xv`
- `--max-users-xe`
- `--llm-pool-size`
- `--llm-assisted-npy` (optional external non-synthetic assisted-input pool)
- `--llm-threshold` (calibrated detector decision point)

Ablation flags:
- `--disable-llm-gate`
- `--disable-biometric-gate`

### Pipeline toggles
- `RUN_CONTINUOUS_EVAL`
- `RUN_CONTINUOUS_ABLATIONS`
- `RUN_CONTINUOUS_SENSITIVITY`
- `CONT_MAX_USERS_XV`
- `CONT_MAX_USERS_XE`
- `CONT_SESSIONS_PER_USER`
- `RUN_MANIFEST`

## Experimental Protocol
### Splits
- `xt`: training only.
- `xv`: threshold tuning + dev diagnostics only.
- `xe`: held-out final report only.
- No tuning on `xe`.

### Static baseline (required)
1. Train on `xt`.
2. Tune threshold on `xv`.
3. Report EER/FAR/FRR/HTER on `xe`.

### Continuous sessions
For each user:
1. enrollment gallery.
2. warmup genuine stream.
3. switch to attack stream:
- human impostor,
- LLM/paste synthetic stream with detector flags.
4. online decisions with smoothing + consecutive alarm.

### Online decision rule
- score_t = mean distance to gallery.
- smoothing over `decision-window`.
- reject if:
  - LLM gate triggers, or
  - smoothed score exceeds tuned biometric threshold.
- alarm when `alarm-consecutive` rejects occur.

### Reported continuous metrics
- detection rate by attack type.
- mean detection delay (steps).
- false alarm before attack rate.
- pre-attack reject rate.
- attack accept/block rates.
- LLM synthetic TPR.
- LLM human FPR estimate.
- 95% CI fields for key online metrics.

## Mandatory Baselines And Ablations
1. `B0` static-only hardened protocol (`evaluate_hardened.py`).
2. `B1` continuous no smoothing (`decision-window=1`).
3. `B2` continuous biometric-only (`--disable-llm-gate`).
4. `B3` continuous LLM-only (`--disable-biometric-gate`).
5. `P` proposed (`window=5`, `alarm=3`, both gates enabled).

Sensitivity:
- `decision-window`: 1, 3, 5, 7.
- `alarm-consecutive`: 1, 2, 3, 4.
- session lengths: at least two settings (recommended and now default in ablation runner: 40/80 and 80/160).

## Statistical Requirements
- default seed + at least 3 additional seeds.
- report 95% CIs for:
  - detection rate,
  - detection delay,
  - pre-attack false alarms / reject behavior.
- retain hardened bootstrap CI for static metrics.

## LLM Detection Validity Requirements
- report synthetic TPR separately from human FPR estimate.
- include ROC and calibration plots on synthetic-vs-human sanity framing.
- explicitly state limitation: synthetic-assisted proxy is not universal LLM detection.

## Streamlit Demonstration Requirements
1. consume threshold artifact from evaluator outputs (no hardcoded threshold claims).
2. align sequence length and features with artifact/config.
3. display research banner with checkpoint hash and threshold source.
4. avoid fixed EER text in UI.

## Failure Modes And Mitigations
1. missing checkpoint -> hard fail (`preflight_dgx.py --require-checkpoint`).
2. data shape mismatch -> hard fail with user/sample identifier.
3. `K > user_count` incompatibility -> preflight fail.
4. GPU not visible -> preflight fail with `--require-gpu`.
5. shell BOM/encoding problems -> preflight warning on `run_pipeline.sh`.
6. scaling pressure -> user caps and chunked simulation knobs.

## DGX Runbook
1. `python preflight_dgx.py <dataset> --require-gpu`
2. `bash run_pipeline.sh 2>&1 | tee pipeline_$(date +%F_%H-%M-%S).log`
3. Optional full continuous scale:
`CONT_MAX_USERS_XV=0 CONT_MAX_USERS_XE=0 CONT_SESSIONS_PER_USER=2 RUN_CONTINUOUS_EVAL=1 bash run_pipeline.sh ...`
4. Optional ablation suite:
`RUN_CONTINUOUS_ABLATIONS=1 RUN_CONTINUOUS_SENSITIVITY=1 ABLATION_SEEDS=42,43,44,45 ABLATION_SESSION_SETTINGS=40:80,80:160 bash run_pipeline.sh ...`
5. Archive:
- pipeline log,
- `results_hardened/*`,
- `results_continuous/*`,
- `paper_results_manifest.json`.

## Assumptions
1. novelty is protocol/problem-setting novelty (continuous + LLM-aware), not re-claim of Type2Branch internals.
2. `xv` is calibration/dev only, `xe` is final held-out.
3. default continuous policy:
- `warmup-steps=40`
- `attack-steps=80`
- `decision-window=5`
- `alarm-consecutive=3`
- `sessions-per-user=1`
4. default DGX routine scale:
- `max-users-xv=1000`
- `max-users-xe=2000`
