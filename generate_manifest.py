"""
generate_manifest.py
====================
Create a run manifest for paper traceability and reproducibility.
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np

import conf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate paper_results_manifest.json for a run.")
    p.add_argument("dataset", help="Dataset name under datasets/<dataset>/npy/")
    p.add_argument("--output", default="paper_results_manifest.json")
    p.add_argument("--seed", type=int, default=int(os.environ.get("TYPE2BRANCH_SEED", "42")))
    p.add_argument("--checkpoint", default="model/checkpoint.weights.h5")
    p.add_argument("--runtime-seconds", type=float, default=None)
    p.add_argument("--pipeline-log", default=None)
    p.add_argument("--hardened-json", default="results_hardened/hardened_metrics.json")
    p.add_argument("--continuous-json", default="results_continuous/continuous_metrics.json")
    p.add_argument("--ablation-json", default="results_continuous/ablations/ablation_summary.json")
    p.add_argument(
        "--fast-dataset-stats",
        action="store_true",
        help="Skip loading full npy dicts; record split file metadata only (safer on huge datasets).",
    )
    return p.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def run_git(args) -> Optional[str]:
    try:
        out = subprocess.check_output(["git"] + args, stderr=subprocess.DEVNULL)
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return None


def git_info() -> Dict[str, Any]:
    commit = run_git(["rev-parse", "HEAD"])
    short_commit = run_git(["rev-parse", "--short", "HEAD"])
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    status = run_git(["status", "--porcelain"])
    return {
        "commit": commit,
        "short_commit": short_commit,
        "branch": branch,
        "dirty": bool(status) if status is not None else None,
    }


def sha256_file(path: str) -> Optional[str]:
    if not os.path.exists(path) or not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_info(path: str, with_hash: bool = False) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"path": path, "exists": False}
    stat = os.stat(path)
    info: Dict[str, Any] = {
        "path": path,
        "exists": True,
        "size_bytes": int(stat.st_size),
        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
    }
    if with_hash:
        info["sha256"] = sha256_file(path)
    return info


def load_json_if_exists(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize_split(split_obj: Dict[str, Dict[str, np.ndarray]]) -> Dict[str, Any]:
    users = len(split_obj)
    sample_count = 0
    sample_shape = None
    min_samples = None
    max_samples = 0
    for user_id, samples in split_obj.items():
        n = len(samples)
        sample_count += n
        min_samples = n if min_samples is None else min(min_samples, n)
        max_samples = max(max_samples, n)
        if sample_shape is None and n > 0:
            first_arr = next(iter(samples.values()))
            sample_shape = list(first_arr.shape)
    return {
        "users": int(users),
        "samples": int(sample_count),
        "sample_shape": sample_shape,
        "min_samples_per_user": int(min_samples) if min_samples is not None else 0,
        "max_samples_per_user": int(max_samples),
    }


def dataset_stats(dataset: str, fast: bool = False) -> Dict[str, Any]:
    base = os.path.join("datasets", dataset, "npy")
    out: Dict[str, Any] = {"dataset": dataset, "base_path": base, "exists": os.path.exists(base)}
    if not os.path.exists(base):
        return out

    splits = {}
    for split in ("xt", "xv", "xe"):
        path = os.path.join(base, f"{split}.npy")
        if not os.path.exists(path):
            splits[split] = {"path": path, "exists": False}
            continue
        if fast:
            split_info = file_info(path, with_hash=False)
            split_info["mode"] = "fast_file_metadata"
        else:
            obj = np.load(path, allow_pickle=True).item()
            split_info = summarize_split(obj)
            split_info["path"] = path
            split_info["exists"] = True
        splits[split] = split_info

    out["splits"] = splits
    return out


def conf_snapshot() -> Dict[str, Any]:
    keys = [
        "N",
        "K",
        "BETA",
        "MODEL_WIDTH",
        "MODEL_FILTERS",
        "MODEL_DROPOUT",
        "TRAINING_STEPS",
        "VALIDATION_STEPS",
        "EPOCHS",
        "EARLY_STOP_PATIENCE",
        "CURRICULUM_DELAY",
        "CURRICULUM_MAX_NEIGHBOURS",
    ]
    snap = {}
    for k in keys:
        snap[k] = getattr(conf, k, None)
    return snap


def metric_excerpt(hardened: Optional[Dict[str, Any]], continuous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if hardened:
        out["hardened"] = {
            "threshold_tuned_on_xv": hardened.get("threshold_tuned_on_xv"),
            "xe_eer": hardened.get("xe_eer"),
            "xe_far_at_tuned_thr": hardened.get("xe_far_at_tuned_thr"),
            "xe_frr_at_tuned_thr": hardened.get("xe_frr_at_tuned_thr"),
            "xe_hter_at_tuned_thr": hardened.get("xe_hter_at_tuned_thr"),
            "xe_eer_95ci": hardened.get("xe_eer_95ci"),
        }
    if continuous:
        out["continuous"] = {
            "continuous_impostor": continuous.get("continuous_impostor"),
            "continuous_llm": continuous.get("continuous_llm"),
            "llm_detector": continuous.get("llm_detector"),
        }
    return out


def main():
    args = parse_args()

    hardened = load_json_if_exists(args.hardened_json)
    continuous = load_json_if_exists(args.continuous_json)
    ablation = load_json_if_exists(args.ablation_json)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "generated_at_local": local_now_iso(),
        "dataset": args.dataset,
        "seed": args.seed,
        "runtime_seconds": args.runtime_seconds,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "git": git_info(),
        "config_snapshot": conf_snapshot(),
        "dataset_stats": dataset_stats(args.dataset, fast=args.fast_dataset_stats),
        "checkpoint": file_info(args.checkpoint, with_hash=True),
        "artifacts": {
            "pipeline_log": file_info(args.pipeline_log) if args.pipeline_log else None,
            "hardened_metrics_json": file_info(args.hardened_json, with_hash=True),
            "continuous_metrics_json": file_info(args.continuous_json, with_hash=True),
            "ablation_summary_json": file_info(args.ablation_json, with_hash=True),
        },
        "metric_excerpt": metric_excerpt(hardened, continuous),
        "ablation_present": ablation is not None,
    }

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[Manifest] wrote {args.output}")


if __name__ == "__main__":
    main()
