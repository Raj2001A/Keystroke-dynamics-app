# Agent Memory: Type2Branch Research Workspace

## Scope
- Project: keystroke dynamics for user verification and insider-threat style detection.
- Base model: Type2Branch (dual branch with recurrent + convolutional paths, attention, Set2Set loss).
- Primary dataset pipeline in this repo: Aalto desktop keystrokes via `ingest_aalto.py`.

## Current Codebase Reality
- Core training config is in `conf.py` and is already tuned upward for DGX use.
- Key values: `K=40`, `MODEL_WIDTH=512`, `MODEL_FILTERS=256`, `BETA=0.05`.
- Training script: `train.py` (mixed precision enabled when available, TensorBoard callback included).
- Verification script: `evaluate.py` (EER-focused, gallery sizes `G=[1,2,5,7,10]`).
- LLM/paste heuristic detector: `detect_llm_paste.py`.
- Hardened static evaluator: `evaluate_hardened.py` (xv threshold tune -> xe report).
- Continuous evaluator: `evaluate_continuous.py` (impostor + LLM switch sessions).
- Paper manifest generator: `generate_manifest.py`.
- Ablation runner: `run_continuous_ablations.py`.
- Streamlit demo: `app.py` with persistent multi-user enrollment in `artifacts/enrollments.json`.
- One-command runner: `run_pipeline.sh` (GPU auto-selection, ingestion, synthetic features, train, eval, metrics).
- Path handling hardened:
  - `run_pipeline.sh` now changes to script directory before executing steps.
  - `train.py`, `evaluate.py`, `evaluate_hardened.py`, `evaluate_continuous.py`, `preflight_dgx.py`, `generate_manifest.py`, and `run_continuous_ablations.py` force repo-root cwd from script location.
  - `app.py` resolves checkpoint/artifact paths from script directory and supports env overrides.

## Data Flow
1. `ingest_aalto.py data/raw/Keystrokes.zip` creates `datasets/aalto_desktop/npy/{xt,xv,xe}.npy`.
2. `generate_synthetic_features.py aalto_desktop` builds merged dataset with extra features (`*_merged`).
3. `train.py aalto_desktop_merged` writes model checkpoint to `model/checkpoint.weights.h5`.
4. `evaluate.py aalto_desktop_merged` prints verification EER results.
5. `evaluate_hardened.py aalto_desktop_merged` writes publication static metrics in `results_hardened/`.
6. `evaluate_continuous.py aalto_desktop_merged` writes novelty metrics in `results_continuous/`.
7. `generate_manifest.py aalto_desktop_merged` writes `paper_results_manifest.json`.
8. `app.py` loads/saves enrollment templates for demo authentication and persists across restarts.

## Recommended Remote Training Workflow (University DGX over SSH)
- Use persistent terminal sessions (`tmux`/`screen`) to avoid job loss on disconnect.
- Keep experiments isolated by timestamped logs and config snapshots.
- Do not assume root/admin access; avoid system-wide installs.
- Prefer virtual env/conda in user space.
- Run with explicit logging: `bash run_pipeline.sh 2>&1 | tee pipeline_$(date +%F_%H-%M-%S).log`.
- Optional ablations: `RUN_CONTINUOUS_ABLATIONS=1 ABLATION_SEEDS=42,43,44,45 bash run_pipeline.sh`.
- Session-length sensitivity: set `ABLATION_SESSION_SETTINGS=40:80,80:160` (or custom list).

## Server Safety and Compliance Notes
- Treat data as institutional data: do not move raw data outside approved storage.
- Avoid storing credentials in scripts; use SSH keys and server-managed secrets.
- Keep compute usage fair on shared university resources (schedule heavy jobs off-peak if required).
- Document exact commit/hash and config used for each result intended for publication.

## Research Priorities for Next Iteration
- Validate whether synthetic LLM/paste samples are representative of real assisted-writing behavior.
- Separate biometric verification metrics (EER/FAR/FRR) from insider-threat multi-class metrics.
- Add reproducibility controls: fixed seeds in scripts, versioned config artifact per run, and run manifest (dataset, split counts, hyperparameters, checkpoint path).
- Keep Streamlit demos bound to evaluator artifacts (`results_hardened/threshold_artifact.json`) rather than hardcoded thresholds.

## Quick Commands
- Ingest: `python ingest_aalto.py data/raw/Keystrokes.zip`
- Feature merge: `python generate_synthetic_features.py aalto_desktop`
- Train: `python train.py aalto_desktop_merged`
- Evaluate: `python evaluate.py aalto_desktop_merged`
- Hardened eval: `python evaluate_hardened.py aalto_desktop_merged --output-dir results_hardened`
- Continuous eval: `python evaluate_continuous.py aalto_desktop_merged --output-dir results_continuous`
- Ablations: `python run_continuous_ablations.py aalto_desktop_merged --seeds 42,43,44,45`
- Ablations with session settings: `python run_continuous_ablations.py aalto_desktop_merged --seeds 42,43,44,45 --session-settings 40:80,80:160`
- Manifest: `python generate_manifest.py aalto_desktop_merged --output paper_results_manifest.json`
- Pipeline: `bash run_pipeline.sh`
- Demo app: `streamlit run app.py`
- Demo path overrides:
  - `TYPE2BRANCH_CHECKPOINT_PATH=/abs/path/checkpoint.weights.h5 streamlit run app.py`
  - `TYPE2BRANCH_THRESHOLD_ARTIFACT=/abs/path/threshold_artifact.json streamlit run app.py`

## Caveats Noted While Reading
- Some files show encoding artifacts in comments/strings; normalize to UTF-8 when cleaning docs.
- `README.md` references `HOWTO.txt`, but that file is not present in this workspace.
- `run_pipeline.sh` assumes Linux shell environment; local Windows execution should run through remote SSH host.
- Legacy optional scripts were removed to keep the workspace lean: `generate_results.py`, `visualize_threats.py`, `ingest_free_text.py`, `util.py`.
- App enrollment reliability:
  - Enrollment writes are atomic (`enrollments.json.tmp` -> `enrollments.json` via `os.replace`).
  - App blocks enrollment/auth when checkpoint weights fail to load (prevents accidental random-weight demo).

## 2026-03-17 Hardening Update
- `evaluate_continuous.py`:
  - Fixed variable collision that could corrupt LLM ROC/calibration reporting (`llm_detector_scores` vs per-user `llm_attack_scores`).
  - Synthetic LLM pool generation is now seed-driven via shared RNG for reproducibility.
  - Added hard fail when `llm_pool_size <= 0`.
- `app.py`:
  - Added runtime shape discovery from dataset splits (`TYPE2BRANCH_DATASET`, `aalto_desktop_merged`, `aalto_desktop`) when threshold artifact is missing/stale.
  - Added candidate-based model load fallback (artifact shape -> env shape -> inferred dataset shape -> defaults).
  - Added threshold/model shape compatibility guard: mismatched threshold artifacts are disabled with explicit warning.
  - Added richer runtime telemetry banner (`model_shape`, `load_source`) for demo auditability.
- `fetch_results.bat`:
  - Updated pulls to current outputs: `results_hardened/`, `results_continuous/`, `paper_results_manifest.json`, `LOSS.png`, `pipeline_*.log`.
  - Keeps backward-safe behavior with per-file warning note.
- Workspace hygiene:
  - Removed stale local `__pycache__/` directory prior to packaging/demo.

## 2026-03-23 Reliability Patch Set
- Inference/evaluation OOM mitigation:
  - `model.get_model_Type2Branch()` now supports `build_optimizer=False`.
  - `evaluate_hardened.py`, `evaluate_continuous.py`, and `app.py` load the model with `build_optimizer=False` to avoid unnecessary optimizer state allocation during inference-only runs.
  - Embedding extraction in evaluators now casts input batches to `float32` before `model.predict(...)`.
- Curriculum learning correctness:
  - `training_generator.py` now enforces nearest-neighbor cap as `min(K-2, CURRICULUM_MAX_NEIGHBOURS)` to honor config and avoid over-aggressive curriculum pressure.
- Validation representativeness:
  - `train.py` now auto-derives validation steps as `max(1, len(xv)//K)` by default.
  - Override remains available via `TYPE2BRANCH_VALIDATION_STEPS`.
- Synthetic feature generation stability:
  - `generate_synthetic_features.py` now emits `float32` augmented arrays (`(seq_len, 5)`), preventing silent `float64` inflation.
- Continuous evaluator guardrails:
  - `evaluate_continuous.py` now hard-validates critical policy args (`decision-window`, `alarm-consecutive`, `warmup-steps`, `attack-steps`, `llm-threshold`, etc.) before running heavy jobs.
- Pipeline ingestion safety:
  - `run_pipeline.sh` now skips ingestion only when all required split files exist (`xt.npy`, `xv.npy`, `xe.npy`), not just when dataset folder exists.

## 2026-04-06 Paper-First Implementation Update
- App reliability and viva readiness:
  - `app.py` now supports explicit startup feedback with spinner during model bootstrap.
  - Dataset shape probing in app runtime candidate discovery is now opt-in via `TYPE2BRANCH_ENABLE_DATASET_SHAPE_SCAN=1` to avoid slow startup by default.
  - Minimum keystroke count in payload parsing is now configurable via `TYPE2BRANCH_APP_MIN_KEYSTROKES` (default 30).
  - Enrollment and authentication submits use Streamlit forms to reduce accidental rerun behavior and improve flow stability.
- Paper artifact automation:
  - Added `select_final_policy.py` to enforce fixed ordered selection criteria and CI-overlap guardrails (`better` vs `comparable_tradeoff` wording).
  - Added `generate_paper_tables.py` to build a paper-facing bundle (`results_paper/*`) from hardened/continuous/ablation outputs.
  - Added `DEMO_RUNBOOK.md` with exact DGX launch + laptop tunnel + fallback commands.
- Claim framing guardrail:
  - Claims should be framed as “LLM-aware continuous framework under tested conditions.”
  - Do not claim general LLM detection unless external-assisted evidence (`--llm-assisted-npy`) is included and reported.
