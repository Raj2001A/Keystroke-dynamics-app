"""
demo_preflight.py
=================
Quick PASS/FAIL checks for viva demo readiness.
"""

import argparse
import json
import os
import sys
from typing import Tuple

import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preflight checks for Streamlit demo readiness.")
    p.add_argument("--dataset", default="aalto_desktop_merged", help="Dataset name under datasets/<name>/npy/")
    p.add_argument("--checkpoint", default="model/checkpoint.weights.h5")
    p.add_argument("--threshold-artifact", default="results_hardened/threshold_artifact.json")
    p.add_argument("--min-users", type=int, default=2)
    return p.parse_args()


def check_file(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, f"missing: {path}"
    if os.path.isdir(path):
        return True, f"ok dir: {path}"
    size = os.path.getsize(path)
    if size <= 0:
        return False, f"empty file: {path}"
    return True, f"ok file: {path} ({size} bytes)"


def check_dataset(dataset: str, min_users: int):
    base = os.path.join("datasets", dataset, "npy")
    paths = {
        "xt": os.path.join(base, "xt.npy"),
        "xv": os.path.join(base, "xv.npy"),
        "xe": os.path.join(base, "xe.npy"),
    }

    ok = True
    notes = []
    for split, path in paths.items():
        exists, msg = check_file(path)
        notes.append(f"[{split}] {msg}")
        ok = ok and exists

    if not ok:
        return False, notes, None

    shapes = {}
    for split, path in paths.items():
        part = np.load(path, allow_pickle=True).item()
        if not isinstance(part, dict) or len(part) < min_users:
            notes.append(f"[{split}] invalid or too few users: {len(part) if isinstance(part, dict) else 'n/a'}")
            ok = False
            continue
        first_user = next(iter(part.keys()))
        first_sample = next(iter(part[first_user].values()))
        shapes[split] = tuple(first_sample.shape)
        notes.append(f"[{split}] users={len(part)} shape={shapes[split]}")

    if ok and not (shapes["xt"] == shapes["xv"] == shapes["xe"]):
        notes.append(f"[shape] mismatch xt/xv/xe: {shapes}")
        ok = False
    return ok, notes, shapes.get("xt")


def check_threshold_artifact(path: str):
    exists, msg = check_file(path)
    if not exists:
        return False, [msg], None

    notes = [msg]
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        thr = obj.get("threshold")
        if thr is None:
            thr = obj.get("threshold_tuned_on_xv")
        if thr is None and isinstance(obj.get("threshold_tuning_xv"), dict):
            thr = obj["threshold_tuning_xv"].get("threshold")
        seq = obj.get("sequence_length")
        feat = obj.get("input_features")
        if thr is None:
            return False, notes + ["threshold key missing"], None
        notes.append(f"threshold={float(thr):.6f} shape=({seq},{feat})")
        return True, notes, (int(seq), int(feat)) if seq is not None and feat is not None else None
    except Exception as e:
        return False, notes + [f"invalid json: {e}"], None


def main():
    args = parse_args()
    all_ok = True

    print("=" * 72)
    print("DEMO PREFLIGHT")
    print("=" * 72)

    ok_ckpt, msg_ckpt = check_file(args.checkpoint)
    all_ok = all_ok and ok_ckpt
    print(f"[checkpoint] {msg_ckpt}")

    ok_data, data_notes, data_shape = check_dataset(args.dataset, args.min_users)
    all_ok = all_ok and ok_data
    for line in data_notes:
        print(f"[dataset] {line}")

    ok_thr, thr_notes, thr_shape = check_threshold_artifact(args.threshold_artifact)
    all_ok = all_ok and ok_thr
    for line in thr_notes:
        print(f"[threshold] {line}")

    if data_shape is not None and thr_shape is not None and data_shape != thr_shape:
        print(f"[shape] mismatch dataset={data_shape} threshold_artifact={thr_shape}")
        all_ok = False

    print("-" * 72)
    print("PASS" if all_ok else "FAIL")
    print("-" * 72)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
