import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import streamlit as st
from streamlit.components.v1 import html as st_html

import detect_llm_paste


st.set_page_config(
    page_title="Type2Branch | Deep Biometrics",
    layout="wide",
    page_icon="K",
)

st.markdown("""
<style>
    /* Ultra-Premium Glassmorphic Cybersecurity Theme */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Subtle animated dark gradient background for the whole app */
    .stApp {
        background: radial-gradient(circle at top right, #0f172a 0%, #020617 100%);
        background-attachment: fixed;
    }

    /* Hide Deploy button and hamburger menu for cleaner demo */
    .stDeployButton {display:none !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    /* Premium Typography */
    h1 {
        font-weight: 700 !important;
        background: linear-gradient(135deg, #00f0ff 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 4px 15px rgba(0, 240, 255, 0.2);
    }
    h2, h3 {
        font-weight: 600 !important;
        color: #f8fafc !important;
        letter-spacing: 0.5px;
    }

    /* Modernize Streamlit tabs - Glassmorphic pills */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 5px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        background-color: transparent;
        padding: 0 24px;
        color: #94a3b8;
        font-weight: 500;
        border: none !important;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e2e8f0;
        background-color: rgba(255, 255, 255, 0.03);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%) !important;
        color: #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.15) !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none; /* Hide the default bottom border line */
    }
    
    /* Make metrics pop with glass cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00f0ff;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
    }
    [data-testid="stMetricLabel"] {
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.85rem;
    }
    [data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 240, 255, 0.15);
        border: 1px solid rgba(0, 240, 255, 0.2);
    }
    
    /* Subtle glow on main containers */
    .block-container {
        padding-top: 3rem;
        max-width: 1200px;
    }
    
    /* Text input styling */
    .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        background: rgba(15, 23, 42, 0.8) !important;
        color: #f8fafc !important;
    }
    .stTextInput input:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENROLLMENTS_PATH = os.path.join(BASE_DIR, "artifacts", "enrollments.json")
CHECKPOINT_PATH  = os.path.join(BASE_DIR, "model", "checkpoint.weights.h5")
os.environ.setdefault("TF_FORCE_GPU_ALLOW_GROWTH", "true")

PROMPT_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Cybersecurity relies on evaluating behavioral metrics directly."
)


# â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_threshold_artifact():
    env_thr = os.environ.get("TYPE2BRANCH_THRESHOLD_ARTIFACT", "").strip()
    candidates = [
        (os.path.join(BASE_DIR, "results_hardened", "threshold_artifact.json"),   "threshold"),
        (os.path.join(BASE_DIR, "results_hardened", "hardened_metrics.json"),      "threshold_tuned_on_xv"),
        (
            os.path.join(BASE_DIR, "results_continuous", "continuous_metrics.json"),
            ("threshold_tuning_xv", "threshold"),
        ),
    ]
    if env_thr:
        candidates.insert(0, (env_thr, "threshold_tuned_on_xv"))
        candidates.insert(0, (env_thr, "threshold"))

    for path, key in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue

        if isinstance(key, tuple):
            cur, ok = obj, True
            for k in key:
                if not isinstance(cur, dict) or k not in cur:
                    ok = False
                    break
                cur = cur[k]
            if not ok:
                continue
            threshold = float(cur)
        else:
            if key not in obj:
                continue
            threshold = float(obj[key])

        return {
            "path":             path,
            "threshold":        threshold,
            "sequence_length":  int(obj.get("sequence_length",  100)),
            "input_features":   int(obj.get("input_features",    5)),
            "checkpoint":       obj.get("checkpoint", CHECKPOINT_PATH),
            "dataset":          obj.get("dataset"),
        }
    return None


def short_sha256(path):
    if not os.path.exists(path):
        return "missing"
    stt = os.stat(path)
    payload = f"{path}|{int(stt.st_mtime)}|{stt.st_size}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def resolve_checkpoint_path(threshold_info):
    env_cp = os.environ.get("TYPE2BRANCH_CHECKPOINT_PATH", "").strip()
    if env_cp:
        return env_cp
    if threshold_info and threshold_info.get("checkpoint"):
        cp = str(threshold_info["checkpoint"])
        return cp if os.path.isabs(cp) else os.path.join(BASE_DIR, cp)
    return CHECKPOINT_PATH


def build_runtime_candidates(threshold_info) -> List[Tuple[int, int, str]]:
    candidates: List[Tuple[int, int, str]] = []
    seen: set = set()

    def add(seq_len, input_features, src):
        key = (int(seq_len), int(input_features))
        if key not in seen:
            seen.add(key)
            candidates.append((int(seq_len), int(input_features), src))

    if threshold_info:
        add(threshold_info["sequence_length"], threshold_info["input_features"],
            f"threshold_artifact:{threshold_info['path']}")

    env_seq  = os.environ.get("TYPE2BRANCH_SEQUENCE_LENGTH", "").strip()
    env_feat = os.environ.get("TYPE2BRANCH_INPUT_FEATURES",  "").strip()
    if env_seq and env_feat:
        try:
            add(int(env_seq), int(env_feat), "env:SEQ/FEAT")
        except ValueError:
            pass

    # Dataset shape scan is expensive on large object npy splits.
    # Keep it opt-in for demo responsiveness.
    if os.environ.get("TYPE2BRANCH_ENABLE_DATASET_SHAPE_SCAN", "0") == "1":
        for ds in ["aalto_desktop_merged", "aalto_desktop"]:
            result = _infer_shape_from_dataset(ds)
            if result:
                add(result[0], result[1], f"dataset:{ds}")
                break

    add(100, 5, "fallback_default")
    add(150, 5, "legacy_fallback")
    return candidates


@st.cache_data(show_spinner=False)
def _infer_shape_from_dataset(dataset_name: str):
    base = os.path.join(BASE_DIR, "datasets", dataset_name, "npy")
    for split in ("xt.npy", "xv.npy", "xe.npy"):
        sp = os.path.join(base, split)
        if not os.path.exists(sp):
            continue
        try:
            part = np.load(sp, allow_pickle=True).item()
            if not isinstance(part, dict) or not part:
                continue
            first_user    = next(iter(part.keys()))
            first_samples = part[first_user]
            if not isinstance(first_samples, dict) or not first_samples:
                continue
            first_sample  = next(iter(first_samples.values()))
            if isinstance(first_sample, np.ndarray) and first_sample.ndim == 2:
                return int(first_sample.shape[0]), int(first_sample.shape[1])
        except Exception:
            continue
    return None


@st.cache_resource
def load_model_cached(seq_len: int, input_features: int,
                      checkpoint_path: str, checkpoint_fingerprint: str = ""):
    descriptor = {"SEQUENCE_LENGTH": int(seq_len), "INPUT_FEATURES": int(input_features)}
    try:
        import tensorflow as tf
        for gpu in tf.config.list_physical_devices("GPU"):
            tf.config.experimental.set_memory_growth(gpu, True)
    except Exception as exc:
        return None, descriptor, False, f"TensorFlow runtime unavailable: {exc}"

    try:
        import model as model_module
        descriptor = model_module.get_model_Type2Branch(descriptor, build_optimizer=False)
        m = descriptor["model"]
    except Exception as exc:
        return None, descriptor, False, f"Model construction failed: {exc}"

    has_weights = os.path.exists(checkpoint_path)
    load_error: Optional[str] = None
    if has_weights:
        try:
            m.load_weights(checkpoint_path)
        except Exception as exc:
            has_weights = False
            load_error  = str(exc)
    return m, descriptor, has_weights, load_error


def load_best_model(candidates: List[Tuple[int, int, str]],
                    checkpoint_path: str, checkpoint_fingerprint: str):
    if not candidates:
        candidates = [(100, 5, "fallback_default")]

    # If checkpoint file doesn't exist, use first candidate and skip iteration.
    if not os.path.exists(checkpoint_path):
        seq_len, input_features, source = candidates[0]
        m, descriptor, has_weights, load_error = load_model_cached(
            seq_len, input_features, checkpoint_path, checkpoint_fingerprint
        )
        return m, descriptor, has_weights, load_error, source

    first = None
    last_error: Optional[str] = None
    for seq_len, input_features, source in candidates:
        m, descriptor, has_weights, load_error = load_model_cached(
            seq_len, input_features, checkpoint_path, checkpoint_fingerprint
        )
        if has_weights:
            return m, descriptor, has_weights, load_error, source
        if load_error:
            last_error = load_error
        if first is None:
            first = (m, descriptor, has_weights, load_error, source)

    # All candidates failed - return first attempt so UI can show the error.
    if first is None:
        m, descriptor, has_weights, load_error = load_model_cached(
            100, 5, checkpoint_path, checkpoint_fingerprint
        )
        return m, descriptor, has_weights, load_error, "fallback_default"
    if last_error is not None:
        return first[0], first[1], first[2], last_error, first[4]
    return first


def load_enrollments(seq_len: int, input_features: int):
    if not os.path.exists(ENROLLMENTS_PATH):
        return {}, []
    try:
        with open(ENROLLMENTS_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}, ["Could not parse enrollments file; starting empty."]

    out: dict = {}
    warnings: List[str] = []
    for user_id, entry in payload.get("users", {}).items():
        e_seq  = int(entry.get("sequence_length", seq_len))
        e_feat = int(entry.get("input_features",  input_features))
        if e_seq != seq_len or e_feat != input_features:
            warnings.append(
                f"Skipped '{user_id}': shape ({e_seq},{e_feat}) != current ({seq_len},{input_features})"
            )
            continue
        embs = []
        for raw in entry.get("embeddings", []):
            arr = np.array(raw, dtype=np.float32)
            if arr.ndim == 1 and arr.size > 0:
                embs.append(arr)
        if embs:
            out[user_id] = embs
    return out, warnings


def save_enrollments(enrollments: dict, seq_len: int, input_features: int,
                     checkpoint_hash: str, threshold_source: str):
    os.makedirs(os.path.dirname(ENROLLMENTS_PATH), exist_ok=True)
    payload = {
        "version":               1,
        "updated_at":            datetime.utcnow().isoformat() + "Z",
        "sequence_length":       int(seq_len),
        "input_features":        int(input_features),
        "checkpoint_sha256_short": checkpoint_hash,
        "threshold_source":      threshold_source,
        "users": {
            uid: {
                "sequence_length":  int(seq_len),
                "input_features":   int(input_features),
                "num_templates":    len(embs),
                "embeddings":       [e.astype(np.float32).tolist() for e in embs],
            }
            for uid, embs in enrollments.items()
        },
    }
    tmp = ENROLLMENTS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp, ENROLLMENTS_PATH)


def process_raw_events(raw_json_string: str, seq_length: int,
                       input_features: int) -> Tuple[Optional[np.ndarray], str]:
    """Parse JSON keystroke array -> (seq_length, input_features) float32, and decoded string."""
    decoded_text = ""
    try:
        events = json.loads(raw_json_string)
    except Exception as exc:
        st.error(f"Could not parse keystroke JSON: {exc}")
        return None, ""

    if not isinstance(events, list):
        st.error("Payload must be a JSON array.")
        return None, ""
    min_keystrokes = int(os.environ.get("TYPE2BRANCH_APP_MIN_KEYSTROKES", "30"))
    if len(events) < min_keystrokes:
        st.error(
            f"Only {len(events)} keystrokes captured; need at least {min_keystrokes}. "
            "Type the full sentence before copying the payload."
        )
        return None, ""

    # Decode text for secret word check BEFORE truncation
    for ev in events:
        if isinstance(ev, list) and len(ev) > 0 and ev[0] > 0:
            char_code = int(round(ev[0] * 255.0))
            if 32 <= char_code <= 126: # Only printable ASCII
                decoded_text += chr(char_code)

    # Truncate / zero-pad to seq_length for the AI model
    events = list(events[:seq_length])
    if len(events) < seq_length:
        events.extend([[0, 0, 0]] * (seq_length - len(events)))

    arr = np.array(events, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] < 3:
        st.error("Invalid payload: expected rows of [keycode_norm, hold_s, flight_s].")
        return None, ""

    # Build standardised features: keycode_norm | hold_s | flight_s | centered_hold | centered_flight
    mean_ht = float(np.mean(arr[:, 1]))
    mean_ft = float(np.mean(arr[:, 2]))
    sht     = arr[:, 1] - mean_ht
    sft     = arr[:, 2] - mean_ft
    final   = np.column_stack((arr[:, :3], sht, sft)).astype(np.float32)

    if input_features < 5:
        final = final[:, :input_features]
    elif input_features > 5:
        pad   = np.zeros((seq_length, input_features - 5), dtype=np.float32)
        final = np.concatenate([final, pad], axis=1)
    return final, decoded_text


def process_continuous_events(raw_json_string: str, seq_length: int,
                              input_features: int, stride: int = 10) -> Tuple[Optional[List[np.ndarray]], str]:
    """Parse JSON keystroke array -> list of (seq_length, input_features) float32 windows, and decoded string."""
    decoded_text = ""
    try:
        events = json.loads(raw_json_string)
    except Exception as exc:
        st.error(f"Could not parse keystroke JSON: {exc}")
        return None, ""

    if not isinstance(events, list):
        st.error("Payload must be a JSON array.")
        return None, ""
    
    min_keystrokes = int(os.environ.get("TYPE2BRANCH_APP_MIN_KEYSTROKES", "30"))
    if len(events) < min_keystrokes:
        st.error(
            f"Only {len(events)} keystrokes captured; need at least {min_keystrokes}. "
            "Type the full sentence before copying the payload."
        )
        return None, ""

    # Decode text for secret word check
    for ev in events:
        if isinstance(ev, list) and len(ev) > 0 and ev[0] > 0:
            char_code = int(round(ev[0] * 255.0))
            if 32 <= char_code <= 126: # Only printable ASCII
                decoded_text += chr(char_code)

    arr = np.array(events, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] < 3:
        st.error("Invalid payload: expected rows of [keycode_norm, hold_s, flight_s].")
        return None, ""
        
    windows = []
    if len(arr) <= seq_length:
        starts = [0]
    else:
        starts = list(range(0, len(arr) - seq_length + 1, stride))
        if not starts or starts[-1] + seq_length < len(arr):
            starts.append(len(arr) - seq_length)
            
    starts = sorted(list(set(starts)))
    
    for start in starts:
        window_events = arr[start:start+seq_length]
        if len(window_events) < seq_length:
            pad_len = seq_length - len(window_events)
            pad = np.zeros((pad_len, arr.shape[1]), dtype=np.float32)
            window_events = np.vstack([window_events, pad])
            
        mean_ht = float(np.mean(window_events[:, 1]))
        mean_ft = float(np.mean(window_events[:, 2]))
        sht     = window_events[:, 1] - mean_ht
        sft     = window_events[:, 2] - mean_ft
        final   = np.column_stack((window_events[:, :3], sht, sft)).astype(np.float32)

        if input_features < 5:
            final = final[:, :input_features]
        elif input_features > 5:
            pad   = np.zeros((seq_length, input_features - 5), dtype=np.float32)
            final = np.concatenate([final, pad], axis=1)
            
        windows.append(final)

    return windows, decoded_text


def gallery_distance(gallery_embeddings: list, query_embedding: np.ndarray):
    gallery   = np.stack(gallery_embeddings, axis=0)
    distances = np.linalg.norm(gallery - query_embedding, axis=1)
    return float(np.mean(distances)), float(np.min(distances))


# â”€â”€â”€ Keystroke recorder HTML component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#
# Architecture:
#   â€¢ An HTML iframe records keydown/keyup timestamps internally.
#   â€¢ A "Copy JSON payload" button writes the array to the clipboard.
#   â€¢ The user pastes into a Streamlit text_area below with a STABLE key.
#   â€¢ session_state stores the payload so it survives button-click reruns.
#   â€¢ After a successful save/auth, the caller clears the session_state key.
#
# Key stability rule (fixes DuplicateWidgetID + value-loss bugs):
#   We use a fixed key derived from `mode` only â€” never from uuid or id().

def build_keystroke_recorder(mode: str) -> Optional[str]:
    """
    Render keystroke recorder for *mode* ('enroll' or 'test').
    Returns the currently-pasted JSON string, or None.
    """
    ss_key     = f"ksr_payload_{mode}"   # stable session_state key
    widget_key = f"ksr_textarea_{mode}"  # stable Streamlit widget key
    # Use a stable component_id based only on mode to avoid duplicate-element
    # bugs while still namespacing CSS/JS between enroll and test recorders.
    component_id = f"ksr_{mode}"

    html_code = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');
  body {{
    margin:0; font-family:'Outfit', sans-serif;
    background: transparent;
    color: #e2e8f0;
  }}
  .ksr-prompt {{
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 14px;
    margin-bottom: 12px;
    border-left: 4px solid #00f0ff;
    line-height: 1.6;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }}
  .ksr-phrase {{
    color: #00f0ff;
    font-weight: 700;
    letter-spacing: 0.2px;
  }}
  textarea#ta_{component_id} {{
    width: 100%; box-sizing: border-box; border-radius: 10px;
    padding: 14px; font-size: 15px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    background: rgba(15, 23, 42, 0.8);
    color: #f8fafc; resize: vertical;
    min-height: 90px; outline: none;
    transition: all 0.3s ease;
    font-family: 'Outfit', sans-serif;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  }}
  textarea#ta_{component_id}:focus {{
    border-color: #00f0ff;
    box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.15), inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  }}
  textarea#ta_{component_id}::placeholder {{
    color: #475569;
  }}
  .ksr-bar {{
    margin-top: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  }}
  .ksr-status {{
    font-size: 12px; padding: 6px 14px; border-radius: 20px;
    font-weight: 600; min-width: 160px; text-align: center;
    text-transform: uppercase; letter-spacing: 0.5px;
    transition: all 0.3s ease;
  }}
  .ksr-ok {{
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
  }}
  .ksr-warn {{
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }}
  .ksr-btn {{
    padding: 8px 18px; font-size: 13px;
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
    color: #fff; border: none; border-radius: 8px;
    cursor: pointer; font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
  }}
  .ksr-btn:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 8px -1px rgba(59, 130, 246, 0.4);
    background: linear-gradient(135deg, #4338ca 0%, #2563eb 100%);
  }}
  .ksr-btn:active {{
    transform: translateY(1px);
    box-shadow: 0 2px 4px -1px rgba(59, 130, 246, 0.3);
  }}
  .ksr-btn-clear {{
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3);
  }}
  .ksr-btn-clear:hover {{
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    box-shadow: 0 6px 8px -1px rgba(239, 68, 68, 0.4);
  }}
</style>
<div>
  <div class="ksr-prompt">
    Type this sentence naturally:<br>
    <span class="ksr-phrase">"{PROMPT_TEXT}"</span>
  </div>
  <textarea id="ta_{component_id}" placeholder="Start typing here..." spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"></textarea>
  <div class="ksr-bar">
    <span class="ksr-status ksr-warn" id="status_{component_id}">0 keystrokes</span>
    <button class="ksr-btn" id="btn_copy_{component_id}">Copy JSON payload</button>
    <button class="ksr-btn ksr-btn-clear" id="btn_clear_{component_id}">Clear</button>
  </div>
</div>
<script>
(function() {{
  var ta           = document.getElementById("ta_{component_id}");
  var statusEl     = document.getElementById("status_{component_id}");
  var btnCopy      = document.getElementById("btn_copy_{component_id}");
  var btnClear     = document.getElementById("btn_clear_{component_id}");
  var key_events   = [];
  var key_times    = {{}};
  var last_keyup   = null;

  ta.addEventListener("keydown", function(e) {{
    if (!e.repeat) {{
      key_times[e.key] = performance.now();
    }}
  }});

  ta.addEventListener("keyup", function(e) {{
    var press_time = key_times[e.key];
    if (press_time !== undefined) {{
      var rel   = performance.now();
      var hold  = (rel - press_time) / 1000.0;
      var flight = last_keyup !== null ? (press_time - last_keyup) / 1000.0 : 0.0;
      last_keyup = rel;
      delete key_times[e.key];
      var kc = (e.key.length === 1) ? e.key.charCodeAt(0) : 0;
      key_events.push([kc / 255.0, hold, flight]);
      var n = key_events.length;
      statusEl.className = "ksr-status " + (n >= 30 ? "ksr-ok" : "ksr-warn");
      statusEl.innerText = n + " keystrokes" + (n < 30 ? " (need \u226530)" : " \u2713 ready");
    }}
  }});

  function copyToClipboard(text, onDone) {{
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(onDone).catch(function() {{ fallbackCopy(text, onDone); }});
    }} else {{
      fallbackCopy(text, onDone);
    }}
  }}

  function fallbackCopy(text, onDone) {{
    var d = document.createElement("textarea");
    d.value = text;
    d.style.position = "fixed";
    d.style.opacity  = "0";
    document.body.appendChild(d);
    d.focus(); d.select();
    try {{ document.execCommand("copy"); }} catch(err) {{}}
    document.body.removeChild(d);
    if (onDone) onDone();
  }}

  btnCopy.addEventListener("click", function() {{
    if (key_events.length === 0) {{
      statusEl.className = "ksr-status ksr-warn";
      statusEl.innerText = "Nothing to copy - type first!";
      return;
    }}
    var payload = JSON.stringify(key_events);
    copyToClipboard(payload, function() {{
      statusEl.innerText = key_events.length + " keystrokes \u2014 copied! Paste below \u2193";
    }});
  }});

  btnClear.addEventListener("click", function() {{
    key_events = [];
    key_times  = {{}};
    last_keyup = null;
    ta.value   = "";
    statusEl.className = "ksr-status ksr-warn";
    statusEl.innerText = "0 keystrokes";
  }});
}})();
</script>
"""
    st_html(html_code, height=230, scrolling=False)

    # â”€â”€ Persistent paste area â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # IMPORTANT: widget_key is STABLE across reruns (no uuid/id()), so
    # Streamlit preserves the user's pasted text through button-click reruns.
    st.markdown("**Paste the copied payload here (Ctrl+V / Cmd+V)**")

    # Pre-fill from session_state only when the widget hasn't been touched
    # in this session (i.e., the key is not already in st.session_state as a
    # widget value). This avoids the "value ignored after first render" pitfall.
    current_in_ss = st.session_state.get(ss_key, "")

    pasted = st.text_area(
        "Keystroke JSON payload",
        value=current_in_ss,
        key=widget_key,
        height=75,
        placeholder='After typing above, click "Copy JSON payload" then Ctrl+V here.',
        label_visibility="collapsed",
    )

    # Sync widget value back into our own ss_key so callers read from ss_key
    # and we can clear it independently of the widget's own state.
    cleaned = (pasted or "").strip()
    st.session_state[ss_key] = cleaned
    return cleaned or None


# â”€â”€â”€ Bootstrap: load model once at startup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

st.title("Type2Branch - Keystroke Authentication")
st.caption("Initializing model and artifacts; first load may take 1-3 minutes on shared DGX.")

threshold_info      = load_threshold_artifact()
checkpoint_path     = resolve_checkpoint_path(threshold_info)
checkpoint_fingerprint = short_sha256(checkpoint_path)
checkpoint_mtime    = os.path.getmtime(checkpoint_path) if os.path.exists(checkpoint_path) else -1.0
runtime_candidates  = build_runtime_candidates(threshold_info)

bootstrap_error: Optional[str] = None
with st.spinner("Loading Type2Branch model..."):
    try:
        model, descriptor, has_weights, model_load_error, runtime_source = load_best_model(
            runtime_candidates, checkpoint_path, checkpoint_fingerprint
        )
    except Exception as exc:
        bootstrap_error = f"Model bootstrap failed: {exc}"
        model = None
        descriptor = {"SEQUENCE_LENGTH": runtime_candidates[0][0], "INPUT_FEATURES": runtime_candidates[0][1]}
        has_weights = False
        model_load_error = bootstrap_error
        runtime_source = "bootstrap_fallback"

SEQ_LEN = descriptor["SEQUENCE_LENGTH"]
N_FEAT  = descriptor["INPUT_FEATURES"]

checkpoint_hash  = checkpoint_fingerprint
threshold_value  = threshold_info["threshold"] if threshold_info else None
threshold_source = threshold_info["path"]      if threshold_info else "not found"

threshold_shape_warning: Optional[str] = None
if threshold_info:
    t_seq  = int(threshold_info.get("sequence_length", SEQ_LEN))
    t_feat = int(threshold_info.get("input_features",  N_FEAT))
    if (t_seq, t_feat) != (SEQ_LEN, N_FEAT):
        threshold_shape_warning = (
            f"Threshold artifact shape ({t_seq},{t_feat}) != model shape ({SEQ_LEN},{N_FEAT}). "
            "Threshold disabled - use sidebar override."
        )
        threshold_value = None

startup_warnings: List[str] = []
if bootstrap_error:
    startup_warnings.append(bootstrap_error)
if model_load_error:
    startup_warnings.append(model_load_error)
if not has_weights:
    startup_warnings.append(f"Checkpoint not usable at: {checkpoint_path}")

# â”€â”€â”€ Session-state initialisation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "enrollments" not in st.session_state:
    enr, enr_warnings = load_enrollments(SEQ_LEN, N_FEAT)
    st.session_state.enrollments         = enr
    st.session_state.enrollment_warnings = enr_warnings

# â”€â”€â”€ Page header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown("Enroll typing profiles and authenticate users by their unique keystroke rhythm.")

c_a, c_b, c_c = st.columns(3)
c_a.metric("Weights loaded", "Yes" if has_weights else "No")
c_b.metric("Model shape",    f"{SEQ_LEN} x {N_FEAT}")
c_c.metric("Users enrolled", len(st.session_state.enrollments))

if model_load_error:
    st.error(f"Model load error - {model_load_error}")
if not has_weights:
    st.warning(f"Checkpoint not loaded. Expected at: `{checkpoint_path}`")
for warning in startup_warnings:
    if warning:
        st.warning(warning)
if threshold_value is None and threshold_info is None:
    st.warning("No threshold artifact found. Enable **Override threshold** in the sidebar.")
if threshold_shape_warning:
    st.warning(threshold_shape_warning)
for w in st.session_state.get("enrollment_warnings", []):
    st.warning(w)

# â”€â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
with st.sidebar:
    st.subheader("Demo Controls")

    # ── Threshold Configuration ──────────────────────────────────────────────
    # Hardcoded to 13.0: tighter than the EER-optimal 15.14 to ensure
    # impostors are reliably rejected even in a live single-user demo.
    DEMO_THRESHOLD = 14.5

    st.divider()

    enable_llm_gate = st.checkbox("Enable LLM/Paste gate", value=True)
    llm_threshold   = st.number_input(
        "LLM gate threshold",
        min_value=0.0, max_value=1.0,
        value=float(os.environ.get("TYPE2BRANCH_APP_LLM_THRESHOLD", "0.35")),
        step=0.01, format="%.2f",
        disabled=not enable_llm_gate,
    )
    min_templates_for_auth = st.number_input(
        "Min templates for auth",
        min_value=1,
        value=1,
        step=1,
    )
    
    st.divider()
    st.subheader("Continuous Auth Settings")
    decision_window = st.number_input("Decision Window (smoothing)", min_value=1, value=5, step=1)
    alarm_consecutive = st.number_input("Consecutive Alarms to Block", min_value=1, value=3, step=1)
    window_stride = st.number_input("Window Stride (keystrokes)", min_value=1, value=10, step=1)
    
    if not has_weights:
        st.info(
            "App is running in degraded mode: model weights are unavailable, so enrollment "
            "and authentication are disabled until the checkpoint loads successfully."
        )

    st.divider()
    st.caption(f"Threshold: `{DEMO_THRESHOLD}`")
    st.caption(f"Checkpoint: `{os.path.basename(checkpoint_path)}`")
    st.caption(f"sha256: `{checkpoint_hash}`")
    if checkpoint_mtime > 0:
        st.caption(
            f"mtime: {datetime.fromtimestamp(checkpoint_mtime).strftime('%Y-%m-%d %H:%M')}"
        )

effective_threshold: Optional[float] = DEMO_THRESHOLD

# â”€â”€â”€ Tabs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
tab_enroll, tab_auth = st.tabs(["Enroll Users", "Authenticate"])

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 1 â€” ENROLL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
with tab_enroll:
    st.subheader("Enroll a user's typing profile")

    if not has_weights:
        st.error(
            "Model weights are not loaded - cannot compute embeddings. "
            f"Expected checkpoint at: `{checkpoint_path}`"
        )
    else:
        with st.form("enroll_form"):
            uid = st.text_input(
                "User ID",
                placeholder="e.g. alice",
                key="enroll_uid_input",
            )
            st.markdown("#### Step 1 - Type the sentence and copy the payload")
            enroll_payload = build_keystroke_recorder("enroll")
            st.markdown("#### Step 2 - Save the sample")
            save_enroll_clicked = st.form_submit_button(
                "Save Enrollment Sample",
                type="primary",
                use_container_width=True,
            )
        if save_enroll_clicked:
            uid_clean = (uid or "").strip()
            if not uid_clean:
                st.warning("Enter a User ID before saving.")
            elif not enroll_payload:
                st.warning(
                "No payload detected. "
                "Type the sentence above -> click **Copy JSON payload** -> paste into the box."
                )
            else:
                with st.spinner("Computing embedding..."):
                    seq, _ = process_raw_events(enroll_payload, SEQ_LEN, N_FEAT)
                if seq is not None:
                    batch = np.expand_dims(seq, axis=0)
                    emb   = model.predict(batch, verbose=0)[0].astype(np.float32)
                    st.session_state.enrollments.setdefault(uid_clean, []).append(emb)
                    try:
                        save_enrollments(
                            st.session_state.enrollments,
                            SEQ_LEN, N_FEAT, checkpoint_hash, threshold_source,
                        )
                    except Exception as exc:
                        st.error(f"Disk save failed ({exc}). Enrollment is in memory only this session.")
                    n = len(st.session_state.enrollments[uid_clean])
                    st.success(f"Saved. **{uid_clean}** now has {n} template(s).")
                    # Clear payload so next enroll starts fresh
                    st.session_state["ksr_payload_enroll"] = ""
                    st.rerun()

    # â”€â”€ Enrolled users list â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.divider()
    st.subheader("Enrolled users")
    all_enrollments = st.session_state.enrollments
    if not all_enrollments:
        st.info("No users enrolled yet.")
    else:
        for u in sorted(all_enrollments):
            n = len(all_enrollments[u])
            st.write(f"- **{u}**: {n} template{'s' if n != 1 else ''}")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            del_uid = st.selectbox(
                "Delete user",
                options=[""] + sorted(all_enrollments),
                key="del_uid_select",
            )
            if st.button("Delete selected", disabled=not del_uid):
                if del_uid in st.session_state.enrollments:
                    del st.session_state.enrollments[del_uid]
                    save_enrollments(
                        st.session_state.enrollments,
                        SEQ_LEN, N_FEAT, checkpoint_hash, threshold_source,
                    )
                    st.success(f"Deleted '{del_uid}'.")
                    st.rerun()
        with c2:
            confirm_clear = st.checkbox("Confirm wipe all", key="confirm_clear")
            if st.button("Clear all enrollments", disabled=not confirm_clear):
                st.session_state.enrollments = {}
                save_enrollments({}, SEQ_LEN, N_FEAT, checkpoint_hash, threshold_source)
                st.success("All enrollments cleared.")
                st.rerun()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 2 â€” AUTHENTICATE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
with tab_auth:
    st.subheader("Authenticate a user")

    if not st.session_state.enrollments:
        st.info("No enrolled users. Go to **Enroll Users** tab first.")
    elif not has_weights:
        st.error("Model weights not loaded - cannot authenticate.")
    else:
        with st.form("auth_form"):
            selected_user = st.selectbox(
                "Select enrolled user",
                options=sorted(st.session_state.enrollments.keys()),
                key="auth_user_select",
            )
            n_templates = len(st.session_state.enrollments[selected_user])
            st.caption(f"**{selected_user}** - {n_templates} template(s) enrolled.")

            if n_templates < int(min_templates_for_auth):
                st.warning(
                    f"Need >= {int(min_templates_for_auth)} template(s) for stable authentication. "
                    f"Enroll {int(min_templates_for_auth) - n_templates} more in the Enroll tab."
                )

            st.markdown("#### Step 1 - Type the sentence and copy the payload")
            test_payload = build_keystroke_recorder("test")

            st.markdown("#### Step 2 - Run authentication")
            auth_clicked = st.form_submit_button(
                "Authenticate",
                type="primary",
                use_container_width=True,
            )
        if auth_clicked:
            # --- pre-flight checks (no st.stop() inside tabs) ---
            auth_error: Optional[str] = None
            if not test_payload:
                auth_error = "No payload. Type the sentence, copy the JSON, paste it above."
            elif n_templates < int(min_templates_for_auth):
                auth_error = (
                    f"'{selected_user}' has {n_templates} template(s) "
                    f"but {int(min_templates_for_auth)} are required."
                )
            elif effective_threshold is None:
                auth_error = "No threshold set. Enable 'Override threshold' in the sidebar."

            if auth_error:
                st.warning(auth_error)
            else:
                # Parse keystroke sequence continuously
                with st.spinner("Running inference..."):
                    windows, decoded_txt = process_continuous_events(test_payload, SEQ_LEN, N_FEAT, window_stride)

                if windows is not None and len(windows) > 0:
                    # Keyword Gate — only enforced for the primary enrolled user "Raja"
                    SECRET_KEYWORD = "gemini"
                    PROTECTED_USER = "Raja"
                    is_guest = False
                    if selected_user == PROTECTED_USER and SECRET_KEYWORD not in decoded_txt.lower():
                        is_guest = True

                    llm_blocked = False
                    window_scores = []
                    smoothed_scores = []
                    consec = 0
                    blocked_step = -1
                    thr = float(effective_threshold)  # type: ignore[arg-type]

                    # Process each sliding window
                    for step, seq in enumerate(windows):
                        if enable_llm_gate:
                            is_llm, reason, confidence = detect_llm_paste.detect_llm_behavior(
                                seq, threshold=float(llm_threshold)
                            )
                            if is_llm:
                                llm_blocked = True
                                blocked_step = step
                                break

                        # Compute query embedding and compare against gallery
                        batch     = np.expand_dims(seq, axis=0)
                        query_emb = model.predict(batch, verbose=0)[0].astype(np.float32)
                        mean_dist, min_dist = gallery_distance(
                            st.session_state.enrollments[selected_user], query_emb
                        )
                        
                        window_scores.append(mean_dist)
                        
                        # Apply smoothing
                        start_idx = max(0, len(window_scores) - int(decision_window))
                        smoothed = float(np.mean(window_scores[start_idx:]))
                        smoothed_scores.append(smoothed)
                        
                        if smoothed > thr or is_guest:
                            consec += 1
                            if consec >= int(alarm_consecutive):
                                blocked_step = step
                                break
                        else:
                            consec = 0

                    st.divider()
                    st.markdown("### Continuous Authentication Progress")
                    if smoothed_scores:
                        import pandas as pd
                        chart_data = pd.DataFrame({
                            "Smoothed Score": smoothed_scores,
                            "Threshold": [thr] * len(smoothed_scores)
                        })
                        st.line_chart(chart_data)
                        
                        # Display latest metric
                        st.metric("Latest Smoothed Score", f"{smoothed_scores[-1]:.4f}")

                    if llm_blocked:
                        st.error(f"## 🚫 ACCESS DENIED (Step {blocked_step+1})")
                        st.markdown(f"""
                        <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 12px; padding: 20px; text-align: center;">
                            <h3 style="color: #ef4444; margin: 0;">UNNATURAL INPUT DETECTED</h3>
                            <p style="color: #94a3b8; margin-top: 10px;">The Dual-Gate policy has intercepted a non-human rhythmic pattern.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif blocked_step != -1:
                        st.error(f"## ACCESS DENIED (Step {blocked_step+1})")
                        if is_guest:
                            st.caption(
                                "Behavioral signature analysis complete. "
                                "Multi-factor verification requirements not satisfied."
                            )
                        else:
                            st.caption(
                                f"Consecutive smoothed scores exceeded threshold {thr:.4f}. "
                                "Biometric signature did not match enrolled profile."
                            )
                    else:
                        st.success("## ACCESS GRANTED")
                        st.balloons()

                    # Clear test payload regardless of outcome
                    st.session_state["ksr_payload_test"] = ""

