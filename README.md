# tifs-type2branch
Companion source code for the article Type2Branch: Keystroke Biometrics based on a Dual-branch Architecture with Attention Mechanisms and Set2set Loss, to be published in IEEE Transactions on Information Forensics and Security.

## Authors

**Nahuel González** (corresponing author) <br>
ngonzalez@lsia.fi.uba.ar

Laboratorio de Sistemas de Información Avanzados (LSIA) <br>
Facultad de Ingeniería, Universidad de Buenos Aires (UBA) <br>
Ciuad Autónoma de Buenos Aires, Argentina

**Giuseppe Stragapede, Ruben Vera-Rodriguez, Ruben Tolosana** <br>
{giuseppe.stragapede,ruben.vera,ruben.tolosana}@uam.es

Biometrics and Data Pattern Analytics (BiDA) Lab <br>
Universidad Autonoma de Madrid <br>
Madrid, Spain


## Abstract

In 2021, the pioneering work on TypeNet showed that keystroke dynamics verification could scale to hundreds of thousands of users with minimal performance degradation. Recently, the KVC-onGoing competition has provided an open and robust experimental protocol for evaluating keystroke dynamics verification systems of such scale, including considerations of algorithmic fairness. This article describes Type2Branch, the model and techniques that achieved the lowest error rates at the KVC-onGoing, in both desktop and mobile scenarios. The novelty aspects of the proposed Type2Branch include: i) synthesized timing features emphasizing user behavior deviation from the general population, ii) a dual-branch architecture combining recurrent and convolutional paths with various attention mechanisms, iii) a new loss function named Set2set that captures the global structure of the embedding space, and iv) a training curriculum of increasing difficulty. Considering five enrollment samples per subject of approximately 50 characters typed, the proposed Type2Branch achieves state-of-the-art performance with mean per-subject EERs of 0.77% and 1.03% on evaluation sets of respectively 15,000 and 5,000 subjects for desktop and mobile scenarios. With a uniform global threshold for all subjects, the EERs are 3.25% for desktop and 3.61% for mobile, outperforming previous approaches by a significant margin. 


## Usage instructions

Use the commands below for end-to-end training, evaluation, and demo setup.

Additional workspace notes for this branch (DGX workflow, pipeline map, research checklist):
- [AGENT_MEMORY.md](AGENT_MEMORY.md)

Hardened publication-style biometric evaluation (threshold tuned on `xv`, reported on held-out `xe`):
- `python evaluate_hardened.py <dataset_name> --output-dir results_hardened`

Continuous-authentication novelty evaluation (genuine->impostor and genuine->LLM switch sessions):
- `python evaluate_continuous.py <dataset_name> --output-dir results_continuous`
- Supports ablation toggles:
  - `--disable-llm-gate` (biometric-only baseline)
  - `--disable-biometric-gate` (LLM-only baseline)
- Supports external assisted-input pool for non-synthetic LLM evaluation:
  - `--llm-assisted-npy <path_to_samples.npy> --llm-assisted-max-samples 5000`
- Supports explicit detector calibration threshold:
  - `--llm-threshold 0.35`

DGX preflight (recommended before long runs):
- `python preflight_dgx.py <dataset_name> --require-gpu`

Paper run manifest:
- `python generate_manifest.py <dataset_name> --output paper_results_manifest.json`

Continuous ablations and policy sensitivity:
- `python run_continuous_ablations.py <dataset_name> --seeds 42,43,44,45`
- Session sensitivity is controlled by `--session-settings 40:80,80:160`
- Add `--include-sensitivity` for decision-window/alarm grid.

Final policy selection (fixed ordered criteria + CI-overlap guard):
- `python select_final_policy.py --ablation-json results_continuous/ablations/ablation_summary.json --hardened-json results_hardened/hardened_metrics.json --output-dir results_continuous/final_selection`

Paper table bundle generation:
- `python generate_paper_tables.py --hardened-json results_hardened/hardened_metrics.json --continuous-json results_continuous/continuous_metrics.json --ablation-json results_continuous/ablations/ablation_summary.json --selection-json results_continuous/final_selection/policy_selection.json --output-dir results_paper`

Artifact validator:
- `python validate_paper_outputs.py --hardened-dir results_hardened --continuous-dir results_continuous`

Streamlit demo (persistent multi-user enrollment):
- `streamlit run app.py`
- Enrollments persist at `artifacts/enrollments.json`.
- Use [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) for viva-ready launch/tunnel flow and fallbacks.
- Optional path overrides if files live elsewhere:
  - `TYPE2BRANCH_CHECKPOINT_PATH=/abs/path/checkpoint.weights.h5`
  - `TYPE2BRANCH_THRESHOLD_ARTIFACT=/abs/path/threshold_artifact.json`

End-to-end DGX pipeline:
- `bash run_pipeline.sh 2>&1 | tee pipeline_$(date +%F_%H-%M-%S).log`
- Raw dataset zip is now expected at `data/raw/Keystrokes.zip` (legacy root path still supported).
- Set `RUN_CONTINUOUS_EVAL=0` to skip continuous evaluation.
- Optional continuous LLM controls:
  - `CONT_LLM_THRESHOLD=0.35`
  - `CONT_LLM_ASSISTED_NPY=/path/to/assisted.npy`
  - `CONT_LLM_ASSISTED_MAX_SAMPLES=5000`
- Set `RUN_CONTINUOUS_ABLATIONS=1` to run baseline/ablation suite.
- Set `RUN_CONTINUOUS_SENSITIVITY=1` together with `RUN_CONTINUOUS_ABLATIONS=1` for policy grid.
- Set `ABLATION_SESSION_SETTINGS=40:80,80:160` (or custom warmup:attack list) for session-length analysis.
- Set `RUN_MANIFEST=0` to skip `paper_results_manifest.json`.

Novelty planning document:
- [NOVELTY_PLAN_CONTINUOUS_LLM_IEEE.md](NOVELTY_PLAN_CONTINUOUS_LLM_IEEE.md)


## Links

Article Preprint <br>
https://arxiv.org/abs/2405.01088

IEEE BigData 2023 Keystroke Verification Challenge (KVC) <br>
https://ieeexplore.ieee.org/document/10386557 <br>
https://arxiv.org/pdf/2401.16559 (preprint)
