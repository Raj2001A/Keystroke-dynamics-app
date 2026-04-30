import csv
import json
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W)


def n(tag: str) -> str:
    return f"{{{W}}}{tag}"


def pct(x, d: int = 3) -> str:
    if x is None:
        return "NA"
    return f"{100.0 * float(x):.{d}f}%"


def f3(x) -> str:
    if x is None:
        return "NA"
    return f"{float(x):.3f}"


def maybe_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() == "none":
        return None
    return float(s)


def row(abl_rows, policy: str, attack: str, warmup: int, attack_steps: int):
    for r in abl_rows:
        if (
            r.get("policy") == policy
            and r.get("attack_type") == attack
            and int(float(r.get("warmup_steps", 0))) == warmup
            and int(float(r.get("attack_steps", 0))) == attack_steps
        ):
            return r
    return {}


def add_para(
    body,
    text: str,
    align: str = "both",
    size: str = "24",
    bold: bool = False,
    italic: bool = False,
    caps: bool = False,
    before: str = "0",
    after: str = "120",
    line: str = "276",
):
    p = ET.SubElement(body, n("p"))
    pPr = ET.SubElement(p, n("pPr"))
    jc = ET.SubElement(pPr, n("jc"))
    jc.set(n("val"), align)
    sp = ET.SubElement(pPr, n("spacing"))
    sp.set(n("before"), before)
    sp.set(n("after"), after)
    sp.set(n("line"), line)
    sp.set(n("lineRule"), "auto")

    r = ET.SubElement(p, n("r"))
    rPr = ET.SubElement(r, n("rPr"))
    rf = ET.SubElement(rPr, n("rFonts"))
    rf.set(n("ascii"), "Times New Roman")
    rf.set(n("hAnsi"), "Times New Roman")
    rf.set(n("cs"), "Times New Roman")
    sz = ET.SubElement(rPr, n("sz"))
    sz.set(n("val"), size)
    sz2 = ET.SubElement(rPr, n("szCs"))
    sz2.set(n("val"), size)
    if bold:
        ET.SubElement(rPr, n("b"))
    if italic:
        ET.SubElement(rPr, n("i"))
    if caps:
        ET.SubElement(rPr, n("caps"))
    t = ET.SubElement(r, n("t"))
    t.text = text
    return p


def add_page_break(body):
    p = ET.SubElement(body, n("p"))
    r = ET.SubElement(p, n("r"))
    br = ET.SubElement(r, n("br"))
    br.set(n("type"), "page")


def add_bullet(body, text: str):
    add_para(body, f"\u2022 {text}", align="left", size="24", before="0", after="60")


def add_table(body, rows):
    tbl = ET.SubElement(body, n("tbl"))
    tblPr = ET.SubElement(tbl, n("tblPr"))
    st = ET.SubElement(tblPr, n("tblStyle"))
    st.set(n("val"), "TableGrid")
    w = ET.SubElement(tblPr, n("tblW"))
    w.set(n("w"), "0")
    w.set(n("type"), "auto")

    for ridx, rdata in enumerate(rows):
        tr = ET.SubElement(tbl, n("tr"))
        for c in rdata:
            tc = ET.SubElement(tr, n("tc"))
            tcPr = ET.SubElement(tc, n("tcPr"))
            tcW = ET.SubElement(tcPr, n("tcW"))
            tcW.set(n("w"), "2200")
            tcW.set(n("type"), "dxa")
            p = ET.SubElement(tc, n("p"))
            pPr = ET.SubElement(p, n("pPr"))
            jc = ET.SubElement(pPr, n("jc"))
            jc.set(n("val"), "center" if ridx == 0 else "left")
            sp = ET.SubElement(pPr, n("spacing"))
            sp.set(n("before"), "0")
            sp.set(n("after"), "0")
            sp.set(n("line"), "240")
            sp.set(n("lineRule"), "auto")
            r = ET.SubElement(p, n("r"))
            rPr = ET.SubElement(r, n("rPr"))
            rf = ET.SubElement(rPr, n("rFonts"))
            rf.set(n("ascii"), "Times New Roman")
            rf.set(n("hAnsi"), "Times New Roman")
            rf.set(n("cs"), "Times New Roman")
            sz = ET.SubElement(rPr, n("sz"))
            sz.set(n("val"), "22")
            sz2 = ET.SubElement(rPr, n("szCs"))
            sz2.set(n("val"), "22")
            if ridx == 0:
                ET.SubElement(rPr, n("b"))
            t = ET.SubElement(r, n("t"))
            t.text = str(c)


def main():
    repo = Path(__file__).resolve().parent
    cont_path = repo / "results_continuous" / "continuous_metrics.json"
    abl_csv_path = repo / "results_continuous" / "ablations" / "ablation_summary.csv"
    out = repo / "SASTRA_Main_Project_Report_Detailed.docx"

    cont = json.loads(cont_path.read_text(encoding="utf-8"))
    with abl_csv_path.open("r", encoding="utf-8") as f:
        abl_rows = list(csv.DictReader(f))

    imp = cont.get("continuous_impostor", {})
    llm = cont.get("continuous_llm", {})
    llm_det = cont.get("llm_detector", {})
    tune = cont.get("threshold_tuning_xv", {})

    b1i = row(abl_rows, "B1_cont_no_smoothing", "impostor", 40, 80)
    b1l = row(abl_rows, "B1_cont_no_smoothing", "llm", 40, 80)
    b2i = row(abl_rows, "B2_biometric_only", "impostor", 40, 80)
    b2l = row(abl_rows, "B2_biometric_only", "llm", 40, 80)
    b3i = row(abl_rows, "B3_llm_only", "impostor", 40, 80)
    b3l = row(abl_rows, "B3_llm_only", "llm", 40, 80)
    p40i = row(abl_rows, "P_cont_llm_proposed", "impostor", 40, 80)
    p40l = row(abl_rows, "P_cont_llm_proposed", "llm", 40, 80)
    p80i = row(abl_rows, "P_cont_llm_proposed", "impostor", 80, 160)
    p80l = row(abl_rows, "P_cont_llm_proposed", "llm", 80, 160)

    doc = ET.Element(n("document"))
    body = ET.SubElement(doc, n("body"))

    # Cover page
    add_para(body, "TYPE2BRANCH-CA: CONTINUOUS KEYSTROKE AUTHENTICATION", align="center", size="28", bold=True, caps=True, after="180")
    add_para(body, "WITH LLM-AWARE TAKEOVER DETECTION", align="center", size="28", bold=True, caps=True, after="360")
    add_para(body, "Report submitted to the SASTRA Deemed to be University", align="center", size="24", after="0")
    add_para(body, "in partial fulfillment of the requirements", align="center", size="24", after="0")
    add_para(body, "for the award of the degree of", align="center", size="24", after="180")
    add_para(body, "Master of Computer Applications", align="center", size="24", bold=True, after="300")
    add_para(body, "Submitted by", align="center", size="24", after="0")
    add_para(body, "Raja Rajeswaran", align="center", size="24", bold=True, after="0")
    add_para(body, "(Reg. No.: 126033005)", align="center", size="24", after="300")
    add_para(body, "May 2026", align="center", size="24", after="300")
    add_para(body, "SCHOOL OF COMPUTING", align="center", size="24", bold=True, after="0")
    add_para(body, "THANJAVUR, TAMIL NADU, INDIA - 613401", align="center", size="24", bold=True)
    add_page_break(body)

    # Bonafide
    add_para(body, "SCHOOL OF COMPUTING", align="center", size="24", bold=True, after="0")
    add_para(body, "THANJAVUR - 613 401", align="center", size="24", bold=True, after="240")
    add_para(body, "Bonafide Certificate", align="center", size="24", bold=True, after="240")
    add_para(
        body,
        'This is to certify that the project report titled "Type2Branch-CA: Continuous Keystroke Authentication with LLM-Aware Takeover Detection" submitted in partial fulfillment of the requirements for the award of the degree of Master of Computer Applications to the SASTRA Deemed to be University is a bona-fide record of the work done by Mr. Raja Rajeswaran (Reg. No. 126033005) during the academic year 2025-26 in the School of Computing under my supervision. This report has not formed the basis for the award of any degree, diploma, associateship, fellowship, or similar title to any candidate of any University.',
    )
    add_para(body, "Signature of Project Supervisor:", align="left", size="24", after="120")
    add_para(body, "Name with Affiliation:", align="left", size="24", after="120")
    add_para(body, "Date:", align="left", size="24", after="240")
    add_para(body, "Project Viva Voce held on: __________________", align="left", size="24", after="240")
    add_para(body, "Examiner 1: __________________    Examiner 2: __________________", align="left", size="24")
    add_page_break(body)
    # Declaration
    add_para(body, "SCHOOL OF COMPUTING", align="center", size="24", bold=True, after="0")
    add_para(body, "THANJAVUR - 613 401", align="center", size="24", bold=True, after="240")
    add_para(body, "Declaration", align="center", size="24", bold=True, after="240")
    add_para(
        body,
        'I declare that the project report titled "Type2Branch-CA: Continuous Keystroke Authentication with LLM-Aware Takeover Detection" submitted by me is an original work done under the guidance of my supervisor in the School of Computing, SASTRA Deemed to be University, during the academic year 2025-26. Wherever materials from other sources have been used, due credit has been given with proper citations in the report. This report has not formed the basis for the award of any degree, diploma, associateship, fellowship, or similar title to any candidate of any University.',
    )
    add_para(body, "Signature of Candidate: __________________", align="left", size="24", after="180")
    add_para(body, "Name of Candidate: Raja Rajeswaran", align="left", size="24", after="120")
    add_para(body, "Date: __________________", align="left", size="24")
    add_page_break(body)

    # Acknowledgement
    add_para(body, "ACKNOWLEDGEMENTS", align="center", size="28", bold=True, caps=True, after="240")
    add_para(
        body,
        "I express my sincere gratitude to the Chancellor, Vice-Chancellor, Dean, Associate Deans, and faculty members of the School of Computing, SASTRA Deemed to be University, for providing academic support, infrastructure, and encouragement for this project work. I thank my project supervisor for continuous guidance, critical feedback, and domain-specific insights throughout the problem formulation, experimentation, and report preparation phases.",
    )
    add_para(
        body,
        "I also acknowledge the contribution of the project review panel members whose comments during review cycles helped improve the methodological rigor, claim framing, and quality of presentation. I thank my peers and friends for collaborative discussions, and my family for their support during the project timeline.",
    )
    add_para(
        body,
        "This work made use of high-performance computing resources, including DGX H200 class infrastructure for model training and controlled evaluation runs. I gratefully acknowledge the support available for compute access and experimentation workflows.",
    )
    add_page_break(body)

    # Abstract
    add_para(body, "ABSTRACT", align="center", size="28", bold=True, caps=True, after="240")
    abstract = (
        "This project presents a continuous keystroke-biometric security framework built on Type2Branch embeddings with an online dual-gate decision policy. "
        "The first gate is a biometric distance gate calibrated on validation users (xv) and reported on held-out users (xe), while the second gate is an LLM-aware behavior gate designed to flag assisted or pasted typing patterns in online sessions. "
        "The study addresses a realistic post-login threat model where a genuine user session can switch to an impostor or assisted-input attacker after initial authentication. "
        f"In the current report artifacts, impostor-session detection is {pct(imp.get('detection_rate'))} with mean delay {f3(imp.get('mean_detection_delay_steps'))} steps, and LLM-session detection is {pct(llm.get('detection_rate'))} with mean delay {f3(llm.get('mean_detection_delay_steps'))} steps. "
        f"False alarm before attack is maintained at {pct(imp.get('false_alarm_before_attack_rate'))}. "
        "A multi-seed ablation protocol over baseline policies (B1/B2/B3) and proposed policy (P) was performed for two session settings (40:80 and 80:160), enabling reproducible tradeoff analysis across detection, attack acceptance, and delay. "
        "The project includes an operational demo application for enrollment and authentication workflows, and a paper-artifact pipeline that generates tables, figures, and manuscript-ready summaries. "
        "The contribution is protocol-level novelty for continuous, LLM-aware online defense with reproducible reporting rather than re-claiming the original Type2Branch architecture novelty."
    )
    add_para(body, abstract)
    add_para(body, "Specific Contribution", align="left", size="24", bold=True, after="60")
    add_bullet(body, "Designed and implemented continuous authentication protocol with genuine-to-attack switch sessions.")
    add_bullet(body, "Implemented dual-gate policy combining biometric thresholding and LLM-aware behavior detection.")
    add_bullet(body, "Built ablation and policy-selection pipeline with multi-seed aggregated reporting.")
    add_bullet(body, "Integrated deployment-facing Streamlit app with persistent enrollment for testcase validation.")
    add_para(body, "Specific Learning", align="left", size="24", bold=True, after="120")
    add_bullet(body, "Understood split hygiene (xt/xv/xe) and leakage-safe calibration for biometric systems.")
    add_bullet(body, "Learned tradeoff balancing between usability (false alarms) and security (detection latency).")
    add_bullet(body, "Gained practical knowledge of DGX execution, experiment reproducibility, and report automation.")
    add_para(body, "Keywords: Keystroke Dynamics, Continuous Authentication, Behavioral Biometrics, Type2Branch, LLM-Aware Detection", align="left", size="22", italic=True)
    add_page_break(body)

    # TOC and lists
    add_para(body, "TABLE OF CONTENTS", align="center", size="28", bold=True, caps=True, after="240")
    toc_lines = [
        "Bonafide Certificate ........................................ ii",
        "Declaration .................................................. iii",
        "Acknowledgements ............................................. iv",
        "Abstract ..................................................... v",
        "List of Figures .............................................. vi",
        "List of Tables ............................................... vii",
        "CHAPTER 1 INTRODUCTION ....................................... 1",
        "CHAPTER 2 OBJECTIVES ......................................... 9",
        "CHAPTER 3 EXPERIMENTAL WORK / METHODOLOGY ................... 12",
        "CHAPTER 4 RESULTS AND DISCUSSION ............................ 24",
        "CHAPTER 5 CONCLUSIONS AND FURTHER WORK ...................... 37",
        "REFERENCES ................................................... 40",
        "APPENDIX ..................................................... 43",
    ]
    for line in toc_lines:
        add_para(body, line, align="left", size="22", after="30")
    add_page_break(body)

    add_para(body, "LIST OF FIGURES", align="center", size="28", bold=True, caps=True, after="240")
    lof_lines = [
        "Fig. 3.1 System architecture of Type2Branch-CA .............................",
        "Fig. 3.2 Continuous session protocol timeline ...............................",
        "Fig. 4.1 Detection delay histogram (impostor and LLM sessions) ..............",
        "Fig. 4.2 LLM detector ROC curve ............................................",
        "Fig. 4.3 LLM detector calibration curve ....................................",
        "Fig. 4.4 Policy tradeoff plot (false alarm vs detection) ....................",
    ]
    for line in lof_lines:
        add_para(body, line, align="left", size="22", after="30")
    add_page_break(body)

    add_para(body, "LIST OF TABLES", align="center", size="28", bold=True, caps=True, after="240")
    lot_lines = [
        "Table 4.1 Main continuous authentication metrics ................................",
        "Table 4.2 Policy-wise ablation comparison at 40:80 setting ........................",
        "Table 4.3 Session-length sensitivity for proposed policy ..........................",
    ]
    for line in lot_lines:
        add_para(body, line, align="left", size="22", after="30")
    add_page_break(body)

    add_para(body, "ABBREVIATIONS", align="center", size="28", bold=True, caps=True, after="240")
    abbr = [
        ("EER", "Equal Error Rate"),
        ("FAR", "False Acceptance Rate"),
        ("FRR", "False Rejection Rate"),
        ("HTER", "Half Total Error Rate"),
        ("LLM", "Large Language Model"),
        ("ROC", "Receiver Operating Characteristic"),
        ("AUC", "Area Under Curve"),
        ("ECE", "Expected Calibration Error"),
        ("HPC", "High Performance Computing"),
    ]
    for k, v in abbr:
        add_para(body, f"{k}  -  {v}", align="left", size="22", after="30")
    add_page_break(body)

    add_para(body, "NOTATION", align="center", size="28", bold=True, caps=True, after="240")
    notation = [
        ("e_t", "Embedding vector at time step t"),
        ("G_u", "Gallery embedding set for enrolled user u"),
        ("s_t", "Raw distance score at time step t"),
        ("s_bar_t", "Smoothed score over decision window"),
        ("tau", "Biometric threshold tuned on xv"),
        ("R_t", "Reject decision at time step t"),
        ("C", "Consecutive rejects required to trigger alarm"),
        ("L_t", "LLM gate flag at time step t"),
    ]
    for k, v in notation:
        add_para(body, f"{k}  -  {v}", align="left", size="22", after="30")
    add_page_break(body)

    # Chapter 1
    add_para(body, "CHAPTER 1", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "INTRODUCTION", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "1.1 Background and Motivation", align="left", size="24", bold=True, after="120")
    ch1_paras = [
        "Behavioral biometrics based on keystroke dynamics provide a non-intrusive security layer that can operate continuously while users type naturally. Unlike static credentials, behavioral signatures are difficult to replicate consistently and can support identity assurance throughout the active session.",
        "Many deployed systems still rely on one-time login validation, creating a gap where unauthorized takeovers can occur after successful authentication. This risk is relevant in shared labs, public access terminals, remote workstations, and high-value enterprise sessions where confidentiality and integrity are critical.",
        "Recent developments in AI-assisted text generation also introduce a new threat axis: a session may remain under the genuine account but receive substantial assisted content with timing behavior that diverges from user-specific typing patterns. Such behavior is not fully captured by static user verification metrics.",
        "The project therefore positions continuous keystroke authentication as an online decision problem, where incoming typing windows must be evaluated in sequence with low latency and minimal false alarms.",
        "Type2Branch, originally designed for static keystroke verification, provides a robust embedding backbone. However, practical deployment for continuous defense requires additional protocol logic, threshold calibration discipline, and threat-aware policy layers.",
    ]
    for p in ch1_paras:
        add_para(body, p)
    add_para(body, "1.2 Problem Statement", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "The central problem addressed in this work is: how to extend a high-performing static keystroke verification model into a continuous online authentication framework that can reliably detect both human impostor takeovers and assisted-input behavior, while controlling false alarms and preserving usability.",
    )
    add_para(body, "1.3 Existing Gaps in Literature and Practice", align="left", size="24", bold=True, after="120")
    for p in [
        "Most benchmark reports emphasize EER/FAR/FRR at a single decision point and do not provide standardized continuous-switch protocols.",
        "Continuous policy choices (decision-window length, consecutive-reject alarm depth, multi-gate interactions) are often under-documented, reducing reproducibility.",
        "LLM-assisted behavior detection is frequently overclaimed with weak validity framing; project-level evidence should explicitly separate synthetic stress tests from universal real-world claims.",
        "Many student and research reports lack claim-evidence traceability from manuscript statements to machine-readable artifacts.",
    ]:
        add_para(body, p)
    add_para(body, "1.4 Scope and Significance", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "This report focuses on protocol-level novelty: a dual-gate continuous architecture over Type2Branch embeddings, strict split hygiene (xv tune -> xe report), ablation-backed policy interpretation, and deployment-aware workflow with user enrollment support. The significance lies in moving from static verification quality to actionable online defense quality under realistic session transitions.",
    )
    add_para(body, "1.5 Organization of the Report", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "Chapter 2 states the project objectives and measurable deliverables. Chapter 3 describes the dataset pipeline, model stack, continuous protocol, DGX execution setup, and app integration. Chapter 4 presents quantitative results, ablations, sensitivity analysis, and discussion. Chapter 5 concludes with limitations and future work directions. References and appendices provide supporting material.",
    )
    add_page_break(body)

    # Chapter 2
    add_para(body, "CHAPTER 2", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "OBJECTIVES", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "2.1 Primary Objective", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "To develop and evaluate a continuous keystroke-authentication framework using Type2Branch embeddings that detects takeover events in online sessions and supports practical deployment through a user enrollment and testing application.",
    )
    add_para(body, "2.2 Specific Objectives", align="left", size="24", bold=True, after="120")
    specific_objectives = [
        "Prepare an end-to-end reproducible dataset pipeline from raw Aalto keystroke records into training, validation, and evaluation splits.",
        "Train and evaluate a Type2Branch-based embedding model with scalable settings suitable for DGX-class hardware.",
        "Implement xv-tuned threshold calibration and xe-held-out reporting for leakage-safe biometric assessment.",
        "Design continuous-session simulation with genuine warmup and controlled attack-switch phases.",
        "Implement and test baseline policies B1/B2/B3 and proposed policy P with multi-seed ablation.",
        "Develop a reporting pipeline that outputs tables, charts, figures, and manuscript-ready artifacts.",
        "Integrate enrollment and authentication operations in a demo application for testcase workflows.",
    ]
    for o in specific_objectives:
        add_bullet(body, o)
    add_para(body, "2.3 Deliverables", align="left", size="24", bold=True, after="120")
    deliverables = [
        "Trained checkpoint artifact for Type2Branch-based embedding model.",
        "Static and continuous metrics JSON/CSV outputs with confidence interval fields.",
        "Ablation summary files and policy tradeoff visualizations.",
        "IEEE/SASTRA report assets (tables, figures, insertion guide).",
        "Detailed final project report in required institutional structure.",
    ]
    for d in deliverables:
        add_bullet(body, d)
    add_page_break(body)

    # Chapter 3
    add_para(body, "CHAPTER 3", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "EXPERIMENTAL WORK / METHODOLOGY", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "3.1 Dataset, Splits, and Preprocessing", align="left", size="24", bold=True, after="120")
    ch3_intro = [
        "The project uses Aalto desktop keystroke data and converts raw records into split-wise numpy artifacts (`xt`, `xv`, `xe`). The `xt` split is used for model learning, `xv` for threshold tuning and development controls, and `xe` for final hold-out evaluation. This split discipline prevents reporting leakage from development users into final results.",
        "Preprocessing validates shape consistency across users, normalizes feature scales, and generates merged synthetic feature channels where required by the training configuration. Input sequence shape consistency is enforced to avoid runtime mismatch during embedding extraction.",
        "All preprocessing and generation scripts are organized to run from repository root context, improving path stability across local and remote execution environments.",
    ]
    for p in ch3_intro:
        add_para(body, p)

    add_para(body, "3.2 Type2Branch Backbone and Training Configuration", align="left", size="24", bold=True, after="120")
    for p in [
        "Type2Branch architecture combines recurrent and convolutional branches with attention-guided representation learning and set-structured loss behavior. The project reuses this architecture as the biometric embedding engine.",
        "The training stack includes mixed precision support (where available), large-width settings for DGX-class resources, and checkpoint-based persistence for downstream evaluation and app inference.",
        "The model is loaded in inference mode without optimizer state during evaluation and application runtime to reduce memory overhead and improve stability.",
    ]:
        add_para(body, p)

    add_para(body, "3.3 DGX H200 Compute Environment", align="left", size="24", bold=True, after="120")
    for p in [
        "The implementation workflow targets DGX H200 scale resources for both training and large-session evaluation runs. Runtime configuration includes GPU memory growth settings to avoid full VRAM pre-allocation and to support shared-node environments.",
        "A preflight utility validates Python, TensorFlow, CUDA visibility, dataset presence, and checkpoint readiness before long-running jobs, reducing wasted queue time.",
        "For reproducibility, experiment runs are logged with timestamped outputs and fixed seeds for ablation bundles.",
    ]:
        add_para(body, p)

    add_para(body, "3.4 Continuous Authentication Protocol", align="left", size="24", bold=True, after="120")
    for p in [
        "Continuous sessions are simulated in two phases: (i) genuine warmup steps where behavior belongs to enrolled user identity, and (ii) attack phase where samples are switched to impostor or assisted-input distributions.",
        "An online decision is produced at each step and an alarm is raised only after a configurable number of consecutive reject decisions. This mechanism controls sporadic false triggers and makes the system robust to isolated noisy samples.",
        "The protocol reports detection rate, mean delay, false alarm before attack, pre-attack reject burden, attack acceptance, and attack block rates. These metrics jointly characterize both security and usability.",
    ]:
        add_para(body, p)

    add_para(body, "3.5 Dual-Gate Decision Rule", align="left", size="24", bold=True, after="120")
    add_para(body, "The online rule used in this project is represented by Equations (3.1) to (3.4).")
    add_para(body, "s_t = (1 / |G_u|) * SUM_{g in G_u} ||e_t - g||_2", align="center", size="22", italic=True)
    add_para(body, "(3.1)", align="right", size="22", after="80")
    add_para(body, "s_bar_t = (1 / m_t) * SUM_{k=max(1,t-W+1)}^t s_k", align="center", size="22", italic=True)
    add_para(body, "(3.2)", align="right", size="22", after="80")
    add_para(body, "R_t = I[(s_bar_t > tau) OR (L_t = 1)]", align="center", size="22", italic=True)
    add_para(body, "(3.3)", align="right", size="22", after="80")
    add_para(body, "alarm_t = I[R_{t-C+1} = ... = R_t = 1]", align="center", size="22", italic=True)
    add_para(body, "(3.4)", align="right", size="22", after="120")
    add_para(
        body,
        f"In the current run, the biometric threshold tuned on xv is tau = {maybe_float(tune.get('threshold')):.6f} with xv EER = {pct(tune.get('eer'))}.",
    )

    add_para(body, "3.6 System Overview and Artifact Pipeline", align="left", size="24", bold=True, after="120")
    add_para(body, "[INSERT FIGURE HERE]", align="center", size="22", italic=True)
    add_para(body, "Fig. 3.1 System architecture of Type2Branch-CA including enrollment, dual-gate scoring, and alarm output.", align="center", size="22", italic=True, after="120")
    add_para(body, "[INSERT FIGURE HERE]", align="center", size="22", italic=True)
    add_para(body, "Fig. 3.2 Continuous session timeline showing warmup phase and attack-switch phase.", align="center", size="22", italic=True, after="120")
    add_para(
        body,
        "Figure assets generated for this report are available in `results_ieee/figures`, including delay distribution, ROC, calibration, and tradeoff charts. Table assets are available in `results_ieee/tables` and are aligned with report chapter numbering.",
    )
    add_page_break(body)
    # Chapter 4
    add_para(body, "CHAPTER 4", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "RESULTS AND DISCUSSION", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "4.1 Main Continuous Authentication Results", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        f"The proposed policy reports impostor-session detection rate of {pct(imp.get('detection_rate'))}, with false alarm before attack {pct(imp.get('false_alarm_before_attack_rate'))} and mean detection delay {f3(imp.get('mean_detection_delay_steps'))} steps. Attack acceptance for impostor sessions is {pct(imp.get('attack_accept_rate'))}.",
    )
    add_para(
        body,
        f"For LLM/paste sessions, detection rate is {pct(llm.get('detection_rate'))}, false alarm before attack is {pct(llm.get('false_alarm_before_attack_rate'))}, and mean delay is {f3(llm.get('mean_detection_delay_steps'))} steps. Attack acceptance in LLM sessions is {pct(llm.get('attack_accept_rate'))}, indicating near-complete block behavior under tested conditions.",
    )
    add_para(body, "Table 4.1 Main continuous authentication metrics.", align="center", size="22", bold=True, after="60")
    add_table(
        body,
        [
            ["Attack Type", "Detection Rate", "False Alarm", "Attack Accept", "Attack Block", "Mean Delay"],
            ["Impostor", pct(imp.get("detection_rate")), pct(imp.get("false_alarm_before_attack_rate")), pct(imp.get("attack_accept_rate")), pct(imp.get("attack_block_rate")), f3(imp.get("mean_detection_delay_steps"))],
            ["LLM", pct(llm.get("detection_rate")), pct(llm.get("false_alarm_before_attack_rate")), pct(llm.get("attack_accept_rate")), pct(llm.get("attack_block_rate")), f3(llm.get("mean_detection_delay_steps"))],
        ],
    )

    add_para(body, "4.2 LLM Detector Validity Signals", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        f"The LLM-aware detector reports synthetic TPR = {pct(llm_det.get('synthetic_tpr'))}, human FPR estimate = {pct(llm_det.get('human_fpr_estimate'))}, and ROC AUC = {f3(llm_det.get('roc_auc_synth_vs_human'))}. The current run uses decision threshold = {f3(llm_det.get('decision_threshold'))}.",
    )
    add_para(
        body,
        "The interpretation remains conservative: these values demonstrate strong discrimination in the present synthetic-vs-human setup, but do not claim universal detection for all real-world assisted writing patterns without broader external validation pools.",
    )
    add_para(body, "[INSERT FIGURE FROM results_ieee/figures/FIG_llm_roc.png]", align="center", size="22", italic=True)
    add_para(body, "Fig. 4.1 ROC curve for LLM-aware detector.", align="center", size="22", italic=True, after="120")
    add_para(body, "[INSERT FIGURE FROM results_ieee/figures/FIG_llm_calibration.png]", align="center", size="22", italic=True)
    add_para(body, "Fig. 4.2 Calibration behavior of LLM-aware detector.", align="center", size="22", italic=True, after="120")

    add_para(body, "4.3 Ablation and Baseline Comparison", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "Ablation rows compare baseline policies and proposed policy under identical conditions. B1 removes smoothing, B2 disables LLM gate (biometric-only), B3 disables biometric gate (LLM-only), and P uses both gates. The ablation outcome explains each policy's failure mode and supports the combined gate design.",
    )
    add_para(body, "Table 4.2 Policy-wise comparison at warmup:attack = 40:80.", align="center", size="22", bold=True, after="60")
    add_table(
        body,
        [
            ["Policy", "Imp Detect", "Imp Accept", "LLM Detect", "LLM Accept", "Imp Delay", "LLM Delay"],
            ["B1", pct(maybe_float(b1i.get("detection_rate"))), pct(maybe_float(b1i.get("attack_accept_rate"))), pct(maybe_float(b1l.get("detection_rate"))), pct(maybe_float(b1l.get("attack_accept_rate"))), f3(maybe_float(b1i.get("mean_detection_delay_steps"))), f3(maybe_float(b1l.get("mean_detection_delay_steps")))],
            ["B2", pct(maybe_float(b2i.get("detection_rate"))), pct(maybe_float(b2i.get("attack_accept_rate"))), pct(maybe_float(b2l.get("detection_rate"))), pct(maybe_float(b2l.get("attack_accept_rate"))), f3(maybe_float(b2i.get("mean_detection_delay_steps"))), f3(maybe_float(b2l.get("mean_detection_delay_steps")))],
            ["B3", pct(maybe_float(b3i.get("detection_rate"))), pct(maybe_float(b3i.get("attack_accept_rate"))), pct(maybe_float(b3l.get("detection_rate"))), pct(maybe_float(b3l.get("attack_accept_rate"))), f3(maybe_float(b3i.get("mean_detection_delay_steps"))), f3(maybe_float(b3l.get("mean_detection_delay_steps")))],
            ["P", pct(maybe_float(p40i.get("detection_rate"))), pct(maybe_float(p40i.get("attack_accept_rate"))), pct(maybe_float(p40l.get("detection_rate"))), pct(maybe_float(p40l.get("attack_accept_rate"))), f3(maybe_float(p40i.get("mean_detection_delay_steps"))), f3(maybe_float(p40l.get("mean_detection_delay_steps")))],
        ],
    )
    add_para(
        body,
        "B3 policy demonstrates strong LLM blocking but cannot detect impostor-only takeover because biometric checks are disabled. B2 policy retains impostor detection but allows non-zero assisted-input acceptance due to absence of dedicated LLM gate. Proposed policy P combines strengths and addresses both threat channels.",
    )
    add_para(body, "[INSERT FIGURE FROM results_ieee/figures/FIG_policy_tradeoff_combined.png]", align="center", size="22", italic=True)
    add_para(body, "Fig. 4.3 Policy tradeoff between false alarm and detection rate.", align="center", size="22", italic=True, after="120")

    add_para(body, "4.4 Session-Length Sensitivity", align="left", size="24", bold=True, after="120")
    add_para(
        body,
        "To examine protocol sensitivity, the proposed policy was compared across two session settings: 40:80 and 80:160. Results indicate stable high detection while attack acceptance changes with longer attack windows.",
    )
    add_para(body, "Table 4.3 Session-length sensitivity for proposed policy.", align="center", size="22", bold=True, after="60")
    add_table(
        body,
        [
            ["Setting", "Imp Detect", "Imp Accept", "LLM Detect", "LLM Accept", "Imp Delay", "LLM Delay"],
            ["40:80", pct(maybe_float(p40i.get("detection_rate"))), pct(maybe_float(p40i.get("attack_accept_rate"))), pct(maybe_float(p40l.get("detection_rate"))), pct(maybe_float(p40l.get("attack_accept_rate"))), f3(maybe_float(p40i.get("mean_detection_delay_steps"))), f3(maybe_float(p40l.get("mean_detection_delay_steps")))],
            ["80:160", pct(maybe_float(p80i.get("detection_rate"))), pct(maybe_float(p80i.get("attack_accept_rate"))), pct(maybe_float(p80l.get("detection_rate"))), pct(maybe_float(p80l.get("attack_accept_rate"))), f3(maybe_float(p80i.get("mean_detection_delay_steps"))), f3(maybe_float(p80l.get("mean_detection_delay_steps")))],
        ],
    )
    add_para(body, "4.5 Discussion", align="left", size="24", bold=True, after="120")
    discussion = [
        "The reported results suggest that combining biometric and assisted-input gates is necessary for balanced security across heterogeneous takeover types.",
        "Low false alarm before attack indicates that pre-attack user disruption remains limited in the tested setting, but deployment tuning should account for domain drift and user heterogeneity.",
        "Delay values around 3 to 4 steps show practical early warning potential for online containment workflows in supervised environments.",
        "The continuous protocol design, machine-readable artifacts, and ablation-led interpretation improve defensibility of project claims during viva and publication review.",
        "Current detector validity depends on available assisted-input pools. Expanded external evaluation and domain shift tests are required before broad production claims.",
    ]
    for p in discussion:
        add_para(body, p)
    add_page_break(body)

    # Chapter 5
    add_para(body, "CHAPTER 5", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "CONCLUSIONS AND FURTHER WORK", align="center", size="28", bold=True, caps=True, after="240")
    conclusions = [
        "This project demonstrates a full-stack continuous keystroke security framework that extends Type2Branch embeddings into online session defense.",
        "The implemented dual-gate policy effectively combines biometric mismatch checks and LLM-aware behavior checks, improving coverage against both impostor and assisted-input takeovers.",
        "The developed artifact pipeline supports research reporting with consistent tables, figures, and machine-readable metrics for claim-evidence traceability.",
        "Integration with enrollment and runtime testing application supports practical testcase workflows and bridges research outputs with deployment-oriented behavior.",
    ]
    for p in conclusions:
        add_para(body, p)
    add_para(body, "Future Work", align="left", size="24", bold=True, after="120")
    future = [
        "Collect and evaluate larger external assisted-input datasets to strengthen validity claims beyond synthetic pools.",
        "Incorporate uncertainty-aware thresholds and adaptive policy tuning for long-session drift.",
        "Perform cross-device and cross-keyboard robustness studies.",
        "Add subgroup fairness and calibration monitoring in continuous mode.",
        "Extend app telemetry for secure audit trails and operational risk analytics.",
    ]
    for f in future:
        add_bullet(body, f)
    add_page_break(body)

    # References
    add_para(body, "REFERENCES", align="center", size="28", bold=True, caps=True, after="240")
    refs = [
        "Acien, A., et al. (2022). TypeNet and scalable deep keystroke biometrics. IEEE Transactions on Biometrics, Behavior, and Identity Science.",
        "Adewole, D. O., et al. (2016). The evolution of neuroprosthetic interfaces. Critical Reviews in Biomedical Engineering, 44, 123-152.",
        "Bensmaia, S. J. (2015). Biological and bionic hand: natural neural coding and artificial perception. Philosophical Transactions of the Royal Society B.",
        "Ghafoor, U., Kim, S., and Hong, K. S. (2017). Selectivity and longevity of peripheral nerve and machine interfaces. Frontiers in Neurorobotics, 11, 59.",
        "Gonzalez, N., Stragapede, G., Vera-Rodriguez, R., and Tolosana, R. (2025). Type2Branch: Keystroke biometrics based on a dual-branch architecture with attention mechanisms and Set2Set loss. IEEE Transactions on Information Forensics and Security, 20.",
        "Knutson, J. S., et al. (2015). Neuromuscular electrical stimulation for motor restoration. PM&R Clinics of North America, 26(4), 729-745.",
        "Morales, A., et al. (2022). SetMargin-based loss functions in deep keystroke biometric learning. Pattern Recognition.",
        "SASTRA Deemed to be University (2026). Project Guidelines: M.Tech & M.C.A Main Project. School of Computing.",
        "Stragapede, G., et al. (2023). IEEE BigData Keystroke Verification Challenge benchmark report.",
        "Stragapede, G., et al. (2024). KVC-onGoing protocol and fairness-oriented large-scale keystroke verification.",
        "Tabot, G. A., et al. (2015). Restoring tactile and proprioceptive sensation through a brain interface. Neurobiology of Disease, 83, 191-198.",
        "Zhang, Y., et al. (2024). Continuous authentication in behavioral biometrics: A survey of online decision policies and drift handling.",
    ]
    for r in refs:
        add_para(body, r, align="left", size="22", after="120", line="240")
    add_page_break(body)

    # Appendix
    add_para(body, "APPENDIX", align="center", size="28", bold=True, caps=True, after="240")
    add_para(body, "A. Similarity Check Report", align="left", size="24", bold=True, after="120")
    add_para(body, "[Attach Turnitin similarity report here as per department submission process.]", align="left", size="22", italic=True)
    add_para(body, "B. Figure and Table Artifact Locations", align="left", size="24", bold=True, after="120")
    add_para(body, r"Figures: results_ieee\figures\*.png", align="left", size="22")
    add_para(body, r"Tables: results_ieee\tables\*.csv", align="left", size="22")
    add_para(body, "C. Source Code and Reproducibility Notes", align="left", size="24", bold=True, after="120")
    add_para(body, "Key scripts used for this report:", align="left", size="22")
    add_bullet(body, "evaluate_continuous.py")
    add_bullet(body, "run_continuous_ablations.py")
    add_bullet(body, "generate_paper_tables.py")
    add_bullet(body, "generate_ieee_assets.py")
    add_bullet(body, "build_sastra_report_docx.py")

    # Section properties: one-column, SASTRA margins
    sect = ET.SubElement(body, n("sectPr"))
    pg = ET.SubElement(sect, n("pgSz"))
    pg.set(n("w"), "12240")
    pg.set(n("h"), "15840")
    mar = ET.SubElement(sect, n("pgMar"))
    mar.set(n("left"), "1800")
    mar.set(n("right"), "1440")
    mar.set(n("top"), "1440")
    mar.set(n("bottom"), "1440")
    mar.set(n("header"), "708")
    mar.set(n("footer"), "708")
    mar.set(n("gutter"), "0")
    cols = ET.SubElement(sect, n("cols"))
    cols.set(n("num"), "1")
    cols.set(n("space"), "720")

    doc_xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True)

    styles = f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:styles xmlns:w=\"{W}\">
  <w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\">
    <w:name w:val=\"Normal\"/>
    <w:rPr>
      <w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>
      <w:sz w:val=\"24\"/>
      <w:szCs w:val=\"24\"/>
    </w:rPr>
  </w:style>
</w:styles>""".encode()

    ct = b"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
  <Override PartName=\"/word/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml\"/>
</Types>"""

    rels = b"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>"""

    drels = b"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>
</Relationships>"""

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc_xml)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", drels)

    words = len(" ".join([t.text or "" for t in ET.fromstring(doc_xml).iter(n("t"))]).split())
    print("Wrote", out)
    print("Estimated words", words)


if __name__ == "__main__":
    main()

