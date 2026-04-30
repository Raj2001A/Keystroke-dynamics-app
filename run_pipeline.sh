#!/bin/bash
# =============================================================
#  Type2Branch x Insider Threat - DGX Training Pipeline
#  Run: bash run_pipeline.sh 2>&1 | tee pipeline.log
# =============================================================

set -euo pipefail

# Always execute relative to this script's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================
#  Python interpreter detection
# =============================================================
if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[ERROR] Neither 'python' nor 'python3' found in PATH."
    exit 1
fi

# TensorFlow shared-GPU safety: avoid eager full-VRAM reservation.
export TF_FORCE_GPU_ALLOW_GROWTH="${TF_FORCE_GPU_ALLOW_GROWTH:-true}"

# =============================================================
#  GPU selection: pick GPU with most free memory
# =============================================================
if command -v nvidia-smi >/dev/null 2>&1; then
  BEST_GPU=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits \
      | sort -t',' -k2 -rn \
      | head -n1 \
      | cut -d',' -f1 \
      | tr -d ' ')
  export CUDA_VISIBLE_DEVICES=$BEST_GPU
  echo "[GPU] Selected GPU $BEST_GPU (most free memory)"
else
  echo "[WARN] nvidia-smi not found; continuing without explicit GPU selection"
fi

TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="pipeline_${TIMESTAMP}.log"
PIPELINE_START_EPOCH=$(date +%s)

echo "=========================================================" | tee -a "$LOG_FILE"
echo " Type2Branch x Insider Threat Detection Pipeline"         | tee -a "$LOG_FILE"
echo " Started: $(date)"                                        | tee -a "$LOG_FILE"
echo " Log: $LOG_FILE"                                          | tee -a "$LOG_FILE"
echo "=========================================================" | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 0: Environment check
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 0/9] Checking environment..." | tee -a "$LOG_FILE"

$PYTHON_BIN -c "
import tensorflow as tf
import numpy as np
import matplotlib
import sklearn

gpus = tf.config.list_physical_devices('GPU')
print(f'  TensorFlow: {tf.__version__}')
print(f'  NumPy:      {np.__version__}')
print(f'  GPUs:       {len(gpus)}')
for g in gpus:
    print(f'    -> {g}')
if len(gpus) == 0:
    print('  WARNING: No GPU detected. Training will be slow.')
" 2>&1 | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 1: Ingest Aalto dataset if needed
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
if [ -f "datasets/aalto_desktop/npy/xt.npy" ] && [ -f "datasets/aalto_desktop/npy/xv.npy" ] && [ -f "datasets/aalto_desktop/npy/xe.npy" ]; then
    echo "[Step 1/9] Dataset split files already exist, skipping ingestion." | tee -a "$LOG_FILE"
    DATASET="aalto_desktop"
elif [ -d "datasets/aalto_desktop" ]; then
    echo "[Step 1/9] Found datasets/aalto_desktop but missing required xt/xv/xe files; re-ingesting..." | tee -a "$LOG_FILE"
    if [ -f "data/raw/Keystrokes.zip" ]; then
        $PYTHON_BIN ingest_aalto.py data/raw/Keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    elif [ -f "data/raw/keystrokes.zip" ]; then
        $PYTHON_BIN ingest_aalto.py data/raw/keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    elif [ -f "Keystrokes.zip" ]; then
        $PYTHON_BIN ingest_aalto.py Keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    elif [ -f "keystrokes.zip" ]; then
        $PYTHON_BIN ingest_aalto.py keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    else
        echo "[ERROR] Dataset directory is incomplete and no Keystrokes.zip was found for re-ingestion." | tee -a "$LOG_FILE"
        exit 1
    fi
    DATASET="aalto_desktop"
elif [ -f "data/raw/Keystrokes.zip" ]; then
    echo "[Step 1/9] Found data/raw/Keystrokes.zip, ingesting Aalto dataset..." | tee -a "$LOG_FILE"
    $PYTHON_BIN ingest_aalto.py data/raw/Keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    DATASET="aalto_desktop"
elif [ -f "data/raw/keystrokes.zip" ]; then
    echo "[Step 1/9] Found data/raw/keystrokes.zip, ingesting Aalto dataset..." | tee -a "$LOG_FILE"
    $PYTHON_BIN ingest_aalto.py data/raw/keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    DATASET="aalto_desktop"
elif [ -f "Keystrokes.zip" ]; then
    echo "[Step 1/9] Found Keystrokes.zip, ingesting Aalto dataset..." | tee -a "$LOG_FILE"
    $PYTHON_BIN ingest_aalto.py Keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    DATASET="aalto_desktop"
elif [ -f "keystrokes.zip" ]; then
    echo "[Step 1/9] Found keystrokes.zip, ingesting Aalto dataset..." | tee -a "$LOG_FILE"
    $PYTHON_BIN ingest_aalto.py keystrokes.zip 2>&1 | tee -a "$LOG_FILE"
    DATASET="aalto_desktop"
else
    echo "[ERROR] No Keystrokes.zip found and no pre-ingested dataset. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# ----------------------------------------------------------
#  Step 2: Generate synthetic features
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 2/9] Adding synthetic features..." | tee -a "$LOG_FILE"
$PYTHON_BIN generate_synthetic_features.py "$DATASET" 2>&1 | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 3: Preflight validation (before training)
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 3/9] Running preflight validation..." | tee -a "$LOG_FILE"

PREFLIGHT_FLAGS="--require-gpu --max-users-scan 2000 --max-samples-scan 50000"
if [ "${PREFLIGHT_FULL_SCAN:-0}" = "1" ]; then
    PREFLIGHT_FLAGS="$PREFLIGHT_FLAGS --full-shape-scan"
fi

$PYTHON_BIN preflight_dgx.py "${DATASET}_merged" $PREFLIGHT_FLAGS 2>&1 | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 4: Train model
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 4/9] Training Type2Branch model..." | tee -a "$LOG_FILE"
echo "         Dataset: ${DATASET}_merged" | tee -a "$LOG_FILE"
echo "         This may take 2-4 hours on H200." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
$PYTHON_BIN train.py "${DATASET}_merged" 2>&1 | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 5: Post-train checkpoint validation + standard eval
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 5/9] Validating checkpoint and optional legacy evaluation..." | tee -a "$LOG_FILE"
$PYTHON_BIN preflight_dgx.py "${DATASET}_merged" --require-gpu --require-checkpoint --max-users-scan 200 --max-samples-scan 5000 2>&1 | tee -a "$LOG_FILE"
if [ "${RUN_LEGACY_EVAL:-0}" = "1" ]; then
  echo "[Step 5/9] RUN_LEGACY_EVAL=1 -> running evaluate.py (legacy, non-authoritative)." | tee -a "$LOG_FILE"
  $PYTHON_BIN evaluate.py "${DATASET}_merged" 2>&1 | tee -a "$LOG_FILE"
else
  echo "[Step 5/9] Skipping evaluate.py (legacy). Hardened paper metrics are produced in Step 6." | tee -a "$LOG_FILE"
fi

# ----------------------------------------------------------
#  Step 6: Hardened static evaluation (publication protocol)
# ----------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo "[Step 6/9] Running hardened evaluation (xv tune -> xe test)..." | tee -a "$LOG_FILE"
HARD_MAX_USERS_XV="${HARD_MAX_USERS_XV:-0}"
HARD_MAX_USERS_XE="${HARD_MAX_USERS_XE:-0}"
HARD_MAX_GENUINE_QUERIES="${HARD_MAX_GENUINE_QUERIES:-30}"
$PYTHON_BIN evaluate_hardened.py "${DATASET}_merged" \
  --output-dir results_hardened \
  --max-users-xv "$HARD_MAX_USERS_XV" \
  --max-users-xe "$HARD_MAX_USERS_XE" \
  --max-genuine-queries-per-user "$HARD_MAX_GENUINE_QUERIES" \
  2>&1 | tee -a "$LOG_FILE"

# ----------------------------------------------------------
#  Step 7: Continuous-auth novelty evaluation
# ----------------------------------------------------------
if [ "${RUN_CONTINUOUS_EVAL:-1}" = "1" ]; then
  echo "" | tee -a "$LOG_FILE"
  echo "[Step 7/9] Running continuous authentication evaluation..." | tee -a "$LOG_FILE"

  CONT_MAX_USERS_XV="${CONT_MAX_USERS_XV:-1000}"
  CONT_MAX_USERS_XE="${CONT_MAX_USERS_XE:-2000}"
  CONT_SESSIONS_PER_USER="${CONT_SESSIONS_PER_USER:-1}"
  CONT_LLM_THRESHOLD="${CONT_LLM_THRESHOLD:-0.35}"
  CONT_LLM_ASSISTED_NPY="${CONT_LLM_ASSISTED_NPY:-}"
  CONT_LLM_ASSISTED_MAX_SAMPLES="${CONT_LLM_ASSISTED_MAX_SAMPLES:-5000}"

  CONT_EXTRA_ARGS=()
  if [ -n "$CONT_LLM_ASSISTED_NPY" ]; then
    CONT_EXTRA_ARGS+=(--llm-assisted-npy "$CONT_LLM_ASSISTED_NPY" --llm-assisted-max-samples "$CONT_LLM_ASSISTED_MAX_SAMPLES")
  fi

  $PYTHON_BIN evaluate_continuous.py "${DATASET}_merged" \
    --output-dir results_continuous \
    --max-users-xv "$CONT_MAX_USERS_XV" \
    --max-users-xe "$CONT_MAX_USERS_XE" \
    --sessions-per-user "$CONT_SESSIONS_PER_USER" \
    --llm-threshold "$CONT_LLM_THRESHOLD" \
    "${CONT_EXTRA_ARGS[@]}" \
    2>&1 | tee -a "$LOG_FILE"
fi

# ----------------------------------------------------------
#  Step 8: Ablation + sensitivity suite (optional, expensive)
# ----------------------------------------------------------
if [ "${RUN_CONTINUOUS_ABLATIONS:-0}" = "1" ]; then
  echo "" | tee -a "$LOG_FILE"
  echo "[Step 8/9] Running continuous ablation suite..." | tee -a "$LOG_FILE"
  ABLATION_SEEDS="${ABLATION_SEEDS:-42,43,44,45}"
  ABLATION_SESSION_SETTINGS="${ABLATION_SESSION_SETTINGS:-40:80,80:160}"
  CONT_MAX_USERS_XV="${CONT_MAX_USERS_XV:-1000}"
  CONT_MAX_USERS_XE="${CONT_MAX_USERS_XE:-2000}"
  CONT_SESSIONS_PER_USER="${CONT_SESSIONS_PER_USER:-1}"

  EXTRA_ABLATION_FLAGS=""
  if [ "${RUN_CONTINUOUS_SENSITIVITY:-0}" = "1" ]; then
    EXTRA_ABLATION_FLAGS="--include-sensitivity"
  fi

  $PYTHON_BIN run_continuous_ablations.py "${DATASET}_merged" \
    --output-dir results_continuous/ablations \
    --seeds "$ABLATION_SEEDS" \
    --session-settings "$ABLATION_SESSION_SETTINGS" \
    --max-users-xv "$CONT_MAX_USERS_XV" \
    --max-users-xe "$CONT_MAX_USERS_XE" \
    --sessions-per-user "$CONT_SESSIONS_PER_USER" \
    $EXTRA_ABLATION_FLAGS \
    2>&1 | tee -a "$LOG_FILE"
fi

# ----------------------------------------------------------
#  Step 9: Run manifest (default ON)
# ----------------------------------------------------------
PIPELINE_END_EPOCH=$(date +%s)
PIPELINE_RUNTIME_SEC=$((PIPELINE_END_EPOCH - PIPELINE_START_EPOCH))
if [ "${RUN_MANIFEST:-1}" = "1" ]; then
  echo "" | tee -a "$LOG_FILE"
  echo "[Step 9/9] Writing paper run manifest..." | tee -a "$LOG_FILE"
  MANIFEST_FAST_FLAG=""
  if [ "${TYPE2BRANCH_MANIFEST_FAST:-1}" = "1" ]; then
    MANIFEST_FAST_FLAG="--fast-dataset-stats"
  fi
  $PYTHON_BIN generate_manifest.py "${DATASET}_merged" \
    --output paper_results_manifest.json \
    --checkpoint model/checkpoint.weights.h5 \
    --seed "${TYPE2BRANCH_SEED:-42}" \
    --runtime-seconds "$PIPELINE_RUNTIME_SEC" \
    --pipeline-log "$LOG_FILE" \
    $MANIFEST_FAST_FLAG \
    2>&1 | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "=========================================================" | tee -a "$LOG_FILE"
echo " Pipeline complete: $(date)" | tee -a "$LOG_FILE"
echo " Runtime (sec): $PIPELINE_RUNTIME_SEC" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo " Output files:" | tee -a "$LOG_FILE"
echo "   model/                                 -> Trained model checkpoints" | tee -a "$LOG_FILE"
echo "   LOSS.png                               -> Training loss curve" | tee -a "$LOG_FILE"
echo "   results_hardened/hardened_metrics.txt  -> EER/FAR/FRR/HTER report" | tee -a "$LOG_FILE"
echo "   results_hardened/hardened_metrics.json -> Machine-readable metrics" | tee -a "$LOG_FILE"
echo "   results_hardened/threshold_artifact.json -> Threshold + shape artifact for apps" | tee -a "$LOG_FILE"
echo "   results_hardened/threshold_curve.csv   -> FAR/FRR curve data" | tee -a "$LOG_FILE"
echo "   results_hardened/per_user_eer.csv      -> Per-user EER on xe" | tee -a "$LOG_FILE"
echo "   results_hardened/score_histogram.png" | tee -a "$LOG_FILE"
echo "   results_hardened/far_frr_curve.png" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_metrics.txt  -> Continuous-auth report" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_metrics.json -> Machine-readable continuous metrics" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_sessions.csv -> Per-session outcomes" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_detection_delay.png" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_llm_roc.png" | tee -a "$LOG_FILE"
echo "   results_continuous/continuous_llm_calibration.png" | tee -a "$LOG_FILE"
echo "   results_continuous/ablations/*          -> Optional ablation outputs" | tee -a "$LOG_FILE"
echo "   paper_results_manifest.json             -> Reproducibility manifest" | tee -a "$LOG_FILE"
echo "   pipeline_*.log                         -> Full console log" | tee -a "$LOG_FILE"
echo "=========================================================" | tee -a "$LOG_FILE"
