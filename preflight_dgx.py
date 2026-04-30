"""
preflight_dgx.py
================
Fast pre-run validator to catch common DGX failures before long jobs.
"""

import argparse
import importlib
import os
import platform
import sys
from typing import Dict, Tuple

import numpy as np

import conf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preflight checks for Type2Branch DGX runs.")
    p.add_argument("dataset", help="Dataset name under datasets/<dataset>/npy/")
    p.add_argument("--require-gpu", action="store_true", help="Fail if TensorFlow sees no GPU")
    p.add_argument("--require-checkpoint", action="store_true", help="Fail if model checkpoint is missing")
    p.add_argument("--full-shape-scan", action="store_true", help="Check all users/samples shapes (slower)")
    p.add_argument("--max-users-scan", type=int, default=2000, help="Max users scanned per partition in quick mode")
    p.add_argument("--max-samples-scan", type=int, default=50000, help="Max samples scanned per partition in quick mode")
    return p.parse_args()


def fail(msg: str):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def warn(msg: str):
    print(f"[WARN] {msg}")


def ok(msg: str):
    print(f"[OK] {msg}")


def python_tensorflow_hint() -> str:
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 13:
        return (
            f"Python {major}.{minor} is not a supported TensorFlow runtime for this project. "
            "Use Python 3.10-3.12 with a TensorFlow wheel compatible with your platform."
        )
    return (
        f"Python {major}.{minor} detected. If TensorFlow import fails, verify that a compatible "
        "TensorFlow wheel is installed for this Python version."
    )


def check_imports():
    required = ["tensorflow", "numpy", "matplotlib", "sklearn", "scipy"]
    for name in required:
        try:
            importlib.import_module(name)
            ok(f"import {name}")
        except Exception as e:
            if name == "tensorflow":
                fail(f"cannot import tensorflow: {e}. {python_tensorflow_hint()}")
            fail(f"cannot import {name}: {e}")


def check_tf_gpu(require_gpu: bool):
    import tensorflow as tf

    gpus = tf.config.list_physical_devices("GPU")
    ok(f"TensorFlow {tf.__version__} loaded")
    if len(gpus) == 0:
        msg = "no GPU visible to TensorFlow"
        if require_gpu:
            fail(msg)
        warn(msg)
    else:
        ok(f"TensorFlow sees {len(gpus)} GPU(s): {[g.name for g in gpus]}")


def load_partition(base: str, split: str) -> Dict:
    path = os.path.join(base, f"{split}.npy")
    if not os.path.exists(path):
        fail(f"missing {path}")
    obj = np.load(path, allow_pickle=True).item()
    if len(obj) == 0:
        fail(f"{split}.npy is empty")
    ok(f"loaded {split}.npy with {len(obj)} users")
    return obj


def scan_partition(
    split: str,
    data: Dict,
    expected_shape: Tuple[int, int] = None,
    full_scan: bool = False,
    max_users_scan: int = 2000,
    max_samples_scan: int = 50000,
):
    users = list(data.keys())
    first_user = users[0]
    first_samples = data[first_user]
    if len(first_samples) == 0:
        fail(f"{split}.npy has user {first_user} with 0 samples")
    first_arr = next(iter(first_samples.values()))
    shape = first_arr.shape

    if expected_shape is not None and shape != expected_shape:
        fail(f"{split}.npy first sample shape {shape} != expected {expected_shape}")

    users_to_scan = users if full_scan else users[: min(len(users), max_users_scan)]
    scanned_users = 0
    scanned_samples = 0
    under_n = 0

    for u in users_to_scan:
        samples = data[u]
        if len(samples) == 0:
            fail(f"{split}.npy has user {u} with 0 samples")
        if len(samples) < conf.N:
            under_n += 1

        for sid, arr in samples.items():
            if arr.shape != shape:
                fail(
                    f"{split}.npy shape mismatch user={u} sample={sid} "
                    f"shape={arr.shape} expected={shape}"
                )
            scanned_samples += 1
            if not full_scan and scanned_samples >= max_samples_scan:
                break
        scanned_users += 1
        if not full_scan and scanned_samples >= max_samples_scan:
            break

    ok(
        f"{split}.npy shape scan passed: shape={shape}, "
        f"scanned_users={scanned_users}, scanned_samples={scanned_samples}"
    )
    if under_n > 0:
        warn(f"{split}.npy has {under_n} scanned users with < N ({conf.N}) samples; oversampling will be used")

    return shape


def check_conf_compatibility(xt: Dict, xv: Dict):
    if conf.K > len(xt):
        fail(f"conf.K={conf.K} > training users={len(xt)}")
    if conf.K > len(xv):
        fail(f"conf.K={conf.K} > validation users={len(xv)}")
    if conf.CURRICULUM_MAX_NEIGHBOURS > conf.K - 2:
        fail(
            f"conf.CURRICULUM_MAX_NEIGHBOURS={conf.CURRICULUM_MAX_NEIGHBOURS} "
            f"must be <= K-2 ({conf.K - 2})"
        )
    if conf.N <= 1:
        fail(f"conf.N must be > 1, got {conf.N}")
    ok(
        f"conf compatibility passed (N={conf.N}, K={conf.K}, "
        f"CURRICULUM_MAX_NEIGHBOURS={conf.CURRICULUM_MAX_NEIGHBOURS})"
    )


def check_paths(require_checkpoint: bool):
    os.makedirs("model", exist_ok=True)
    os.makedirs("results_hardened", exist_ok=True)
    os.makedirs("results_continuous", exist_ok=True)
    ok("model/, results_hardened/, and results_continuous/ are writable")

    checkpoint = os.path.join("model", "checkpoint.weights.h5")
    if os.path.exists(checkpoint):
        ok(f"checkpoint found: {checkpoint}")
    else:
        msg = f"checkpoint not found: {checkpoint}"
        if require_checkpoint:
            fail(msg)
        warn(msg)


def check_script_bom(path: str):
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        head = f.read(3)
    if head == b"\xef\xbb\xbf":
        warn(f"{path} has UTF-8 BOM; prefer BOM-free shell scripts on Linux")
    else:
        ok(f"{path} encoding head is BOM-free")


def main():
    args = parse_args()

    print("=" * 72)
    print("TYPE2BRANCH DGX PREFLIGHT")
    print("=" * 72)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Dataset: {args.dataset}")
    print(f"Config: N={conf.N}, K={conf.K}, delay={conf.CURRICULUM_DELAY}, max_neigh={conf.CURRICULUM_MAX_NEIGHBOURS}")

    check_imports()
    check_tf_gpu(require_gpu=args.require_gpu)

    base = os.path.join("datasets", args.dataset, "npy")
    if not os.path.exists(base):
        fail(f"dataset folder not found: {base}")

    xt = load_partition(base, "xt")
    xv = load_partition(base, "xv")
    xe = load_partition(base, "xe")

    shape_xt = scan_partition(
        "xt", xt, None, args.full_shape_scan, args.max_users_scan, args.max_samples_scan
    )
    shape_xv = scan_partition(
        "xv", xv, shape_xt, args.full_shape_scan, args.max_users_scan, args.max_samples_scan
    )
    _ = scan_partition(
        "xe", xe, shape_xt, args.full_shape_scan, args.max_users_scan, args.max_samples_scan
    )
    ok(f"partition shape consistency passed: xt={shape_xt}, xv={shape_xv}")

    check_conf_compatibility(xt, xv)
    check_paths(require_checkpoint=args.require_checkpoint)
    check_script_bom("run_pipeline.sh")

    print("=" * 72)
    print("PREFLIGHT PASSED")
    print("=" * 72)


if __name__ == "__main__":
    main()
