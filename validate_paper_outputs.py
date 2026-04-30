"""
validate_paper_outputs.py
=========================
Validate required output artifacts and key fields for paper reporting.
"""

import argparse
import json
import os
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Validate hardened + continuous output artifacts.")
    p.add_argument("--hardened-dir", default="results_hardened")
    p.add_argument("--continuous-dir", default="results_continuous")
    return p.parse_args()


def require_file(path: str, errors):
    if not os.path.exists(path):
        errors.append(f"Missing file: {path}")


def require_keys(obj, keys, label, errors):
    for k in keys:
        if k not in obj:
            errors.append(f"Missing key in {label}: {k}")


def load_json(path, errors):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse JSON {path}: {e}")
        return None


def main():
    args = parse_args()
    errors = []

    hardened_required = [
        "hardened_metrics.json",
        "hardened_metrics.txt",
        "threshold_curve.csv",
        "score_histogram.png",
        "far_frr_curve.png",
        "per_user_eer.csv",
        "threshold_artifact.json",
    ]
    continuous_required = [
        "continuous_metrics.json",
        "continuous_metrics.txt",
        "continuous_sessions.csv",
        "continuous_detection_delay.png",
        "continuous_llm_roc.png",
        "continuous_llm_calibration.png",
    ]

    for name in hardened_required:
        require_file(os.path.join(args.hardened_dir, name), errors)
    for name in continuous_required:
        require_file(os.path.join(args.continuous_dir, name), errors)

    hardened_json_path = os.path.join(args.hardened_dir, "hardened_metrics.json")
    continuous_json_path = os.path.join(args.continuous_dir, "continuous_metrics.json")
    if os.path.exists(hardened_json_path):
        hardened = load_json(hardened_json_path, errors)
        if hardened is not None:
            require_keys(
                hardened,
                [
                    "threshold_tuned_on_xv",
                    "xe_eer",
                    "xe_far_at_tuned_thr",
                    "xe_frr_at_tuned_thr",
                    "xe_hter_at_tuned_thr",
                ],
                hardened_json_path,
                errors,
            )

    if os.path.exists(continuous_json_path):
        continuous = load_json(continuous_json_path, errors)
        if continuous is not None:
            require_keys(
                continuous,
                ["continuous_impostor", "continuous_llm", "llm_detector", "threshold_tuning_xv"],
                continuous_json_path,
                errors,
            )
            imp = continuous.get("continuous_impostor", {})
            llm = continuous.get("continuous_llm", {})
            require_keys(
                imp,
                ["detection_rate", "false_alarm_before_attack_rate", "mean_detection_delay_steps_95ci"],
                "continuous_impostor",
                errors,
            )
            require_keys(
                llm,
                ["detection_rate", "false_alarm_before_attack_rate", "mean_detection_delay_steps_95ci"],
                "continuous_llm",
                errors,
            )

    ablation_json_path = os.path.join(args.continuous_dir, "ablations", "ablation_summary.json")
    if os.path.exists(ablation_json_path):
        ablation = load_json(ablation_json_path, errors)
        if ablation is not None:
            require_keys(
                ablation,
                ["dataset", "checkpoint", "seeds", "session_settings", "policies", "rows"],
                ablation_json_path,
                errors,
            )

    if errors:
        print("[VALIDATION] FAILED")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)

    print("[VALIDATION] PASSED")
    print(f"- Hardened dir: {args.hardened_dir}")
    print(f"- Continuous dir: {args.continuous_dir}")


if __name__ == "__main__":
    main()
