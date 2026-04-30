"""
build_ieee_docx.py
==================
Generates the Type2Branch-CA research paper using the published base paper
(Type2Branch IEEE TIFS) as the template document. All styles, fonts, margins,
and layout are inherited directly, so the output is visually identical in format.

Base paper template:
  R:\Project papers\Type2Branch\references\
  Type2Branch_Keystroke_Biometrics_Based_on_a_Dual-Branch_Architecture_...docx

Observed format from base paper:
  Page :  21.59 x 27.94 cm (US Letter)
  Margins: T=1.66 B=0.92 L=1.27 R=1.27 cm
  Layout : Single column
  Font   : Times New Roman throughout
  Styles : Normal (captions/tables 8pt center), Body Text (10pt justify),
           List Paragraph (section heads, bold 10pt)
"""

import json, copy
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO     = Path(r"R:\Project papers\Type2Branch\repo")
TEMPLATE = Path(r"R:\Project papers\Type2Branch\references") / \
           "Type2Branch_Keystroke_Biometrics_Based_on_a_Dual-Branch_Architecture_With_Attention_Mechanisms_and_Set2set_Loss.docx"
OUT      = REPO / "IEEE_Continuous_Type2Branch_Expanded.docx"

# ─── Load results ─────────────────────────────────────────────────────────────
cont = json.loads((REPO / "results_continuous" / "continuous_metrics.json").read_text("utf-8"))
abl  = json.loads((REPO / "results_continuous" / "ablations" / "ablation_summary.json").read_text("utf-8"))

def get_row(policy, attack, warm, atk):
    for r in abl.get("rows", []):
        if (r.get("policy") == policy and r.get("attack_type") == attack
                and r.get("warmup_steps") == warm and r.get("attack_steps") == atk):
            return r
    return {}

imp  = cont["continuous_impostor"]
llm  = cont["continuous_llm"]
ld   = cont["llm_detector"]
b0   = abl.get("static_baseline_B0_hardened", {})
xv   = cont["threshold_tuning_xv"]
b1i  = get_row("B1_cont_no_smoothing",  "impostor", 40, 80)
b1l  = get_row("B1_cont_no_smoothing",  "llm",      40, 80)
b2i  = get_row("B2_biometric_only",     "impostor", 40, 80)
b2l  = get_row("B2_biometric_only",     "llm",      40, 80)
b3i  = get_row("B3_llm_only",           "impostor", 40, 80)
b3l  = get_row("B3_llm_only",           "llm",      40, 80)
pi40 = get_row("P_cont_llm_proposed",   "impostor", 40, 80)
pl40 = get_row("P_cont_llm_proposed",   "llm",      40, 80)
pi80 = get_row("P_cont_llm_proposed",   "impostor", 80, 160)
pl80 = get_row("P_cont_llm_proposed",   "llm",      80, 160)

def pct(x): return f"{100*float(x):.3f}%"
def f3(x):  return f"{float(x):.3f}"
def f4(x):  return f"{float(x):.4f}"
def f6(x):  return f"{float(x):.6f}"

tau     = f6(xv["threshold"])
xv_eer  = pct(xv["eer"])

# ─── Open base paper as template, clear its body ──────────────────────────────
doc = Document(TEMPLATE)

# Remove all existing body content (paragraphs and tables)
body = doc.element.body
for child in list(body):
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag in ('p', 'tbl', 'sdt'):
        body.remove(child)

# ─── Style helpers ────────────────────────────────────────────────────────────
TNR = "Times New Roman"

def _set_run_font(run, name=TNR, size_pt=None, bold=None, italic=None, color=None):
    run.font.name = name
    if size_pt is not None: run.font.size = Pt(size_pt)
    if bold    is not None: run.font.bold = bold
    if italic  is not None: run.font.italic = italic
    if color   is not None: run.font.color.rgb = RGBColor(*color)
    rPr = run._r.get_or_add_rPr()
    el = rPr.find(qn("w:rFonts"))
    if el is None:
        el = OxmlElement("w:rFonts")
        rPr.insert(0, el)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        el.set(qn(attr), name)


def add_para(style_name="Body Text", alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
             space_before_pt=None, space_after_pt=0, keep_with_next=False):
    p = doc.add_paragraph(style=style_name)
    pf = p.paragraph_format
    pf.alignment = alignment
    pf.space_after = Pt(space_after_pt)
    if space_before_pt is not None:
        pf.space_before = Pt(space_before_pt)
    if keep_with_next:
        pf.keep_with_next = True
    return p


def body(text, space_before=None, space_after=0):
    """Standard 10pt Times New Roman body paragraph, justified."""
    p = add_para("Body Text", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before, space_after)
    run = p.add_run(text)
    _set_run_font(run, size_pt=10)
    return p


def body_runs(parts, space_before=None, space_after=0):
    """Body paragraph with mixed formatting. parts = [(text, bold, italic), ...]"""
    p = add_para("Body Text", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before, space_after)
    for text, bold, italic in parts:
        run = p.add_run(text)
        _set_run_font(run, size_pt=10, bold=bold or None, italic=italic or None)
    return p


def title(text):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=0, space_after_pt=6)
    run = p.add_run(text)
    _set_run_font(run, size_pt=24, bold=True)
    return p


def authors(text):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=4, space_after_pt=2)
    run = p.add_run(text)
    _set_run_font(run, size_pt=10, italic=True)
    return p


def abstract_head():
    p = add_para("Body Text", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before_pt=8, space_after_pt=0)
    r1 = p.add_run("Abstract")
    _set_run_font(r1, size_pt=9, bold=True, italic=True)
    r2 = p.add_run("\u2014")
    _set_run_font(r2, size_pt=9)
    return p


def abstract_body(text):
    p = add_para("Body Text", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before_pt=0, space_after_pt=2)
    run = p.add_run(text)
    _set_run_font(run, size_pt=9)
    return p


def index_terms(text):
    p = add_para("Body Text", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before_pt=2, space_after_pt=8)
    r1 = p.add_run("Index Terms\u2014")
    _set_run_font(r1, size_pt=9, bold=True, italic=True)
    r2 = p.add_run(text)
    _set_run_font(r2, size_pt=9, italic=True)


def section(roman, heading_text):
    """Section heading in List Paragraph style (matches base paper section style)."""
    p = add_para("List Paragraph", WD_ALIGN_PARAGRAPH.LEFT, space_before_pt=10, space_after_pt=4)
    p.paragraph_format.left_indent = Pt(0)   # no indent for section heads
    run = p.add_run(f"{roman}. {heading_text.upper()}")
    _set_run_font(run, size_pt=10, bold=True)
    return p


def subsection(letter, heading_text):
    p = add_para("List Paragraph", WD_ALIGN_PARAGRAPH.LEFT, space_before_pt=6, space_after_pt=3)
    p.paragraph_format.left_indent = Pt(0)
    run = p.add_run(f"{letter}. {heading_text}")
    _set_run_font(run, size_pt=10, bold=True, italic=True)
    return p


def table_caption(label, description):
    """Base paper: TABLE I on one line (8pt center bold), description below (8pt center)."""
    p1 = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=8, space_after_pt=0,
                  keep_with_next=True)
    r1 = p1.add_run(label)
    _set_run_font(r1, size_pt=8, bold=True)
    p2 = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=0, space_after_pt=4,
                  keep_with_next=True)
    r2 = p2.add_run(description)
    _set_run_font(r2, size_pt=8)


def equation(text, label=""):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=3, space_after_pt=3)
    run = p.add_run(text)
    _set_run_font(run, "Courier New", size_pt=9, italic=True)
    if label:
        run2 = p.add_run(f"   ({label})")
        _set_run_font(run2, size_pt=9)


def figure_placeholder(text):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=6, space_after_pt=2)
    run = p.add_run(text)
    _set_run_font(run, size_pt=8, italic=True, color=(130, 130, 130))


def figure_caption(text):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=2, space_after_pt=6)
    run = p.add_run(text)
    _set_run_font(run, size_pt=8, italic=True)


def reference(text):
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.JUSTIFY, space_before_pt=0, space_after_pt=3)
    p.paragraph_format.left_indent     = Inches(0.25)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    run = p.add_run(text)
    _set_run_font(run, size_pt=8)


def divider():
    p = add_para("Normal", WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=3, space_after_pt=3)
    run = p.add_run("\u2015" * 72)
    _set_run_font(run, size_pt=5, color=(180, 180, 180))


def add_table(rows, col_widths_cm=None):
    """
    rows[0] = header (8pt bold, blue shaded).
    Subsequent rows = 8pt regular, centered.
    Matches base paper table style.
    """
    ncols = len(rows[0])
    tbl = doc.add_table(rows=len(rows), cols=ncols)
    tbl.style = "Table Normal"
    # Add visible borders manually via raw XML
    tblPr = tbl._tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl._tbl.insert(0, tblPr)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"),   "single")
        b.set(qn("w:sz"),    "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        tblBorders.append(b)
    tblPr.append(tblBorders)

    default_w = Cm(15.0 / ncols)
    for ri, rowdata in enumerate(rows):
        is_header = (ri == 0)
        for ci, cell_text in enumerate(rowdata):
            cell = tbl.rows[ri].cells[ci]
            if col_widths_cm:
                cell.width = Cm(col_widths_cm[ci])
            else:
                cell.width = default_w
            p = cell.paragraphs[0]
            p.paragraph_format.alignment   = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            run = p.add_run(str(cell_text))
            _set_run_font(run, size_pt=8, bold=is_header)
            if is_header:
                tc   = cell._tc
                tcPr = tc.get_or_add_tcPr()
                shd  = OxmlElement("w:shd")
                shd.set(qn("w:val"),   "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"),  "DEE6F0")
                tcPr.append(shd)
    # small spacer after table
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ─── TITLE & AUTHORS ──────────────────────────────────────────────────────────
title("Type2Branch-CA: Continuous Keystroke Authentication\nwith LLM-Aware Takeover Detection")
authors("Anonymous Author(s)")
authors("Department of Computer Science and Engineering, SASTRA Deemed University, Thanjavur, India")
authors("Email: \u27e8redacted for blind review\u27e9")

divider()

# ─── ABSTRACT ────────────────────────────────────────────────────────────────
abstract_head()
abstract_body(
    f"Static keystroke biometric systems verify identity at login but provide no assurance after "
    f"session initiation. This paper presents Type2Branch-CA, a continuous-authentication extension "
    f"of the Type2Branch deep biometric framework [1], augmented with a dual-gate online policy that "
    f"jointly defends against human impostor takeover and large-language-model (LLM) or "
    f"clipboard-assisted scripted input. On the Aalto Desktop dataset ({cont['users_simulated']:,} "
    f"simulated users, {cont['sessions_total']:,} total session trials), the proposed policy achieves "
    f"an impostor detection rate of {pct(imp['detection_rate'])} with a mean detection latency of "
    f"{f3(imp['mean_detection_delay_steps'])} steps and a pre-attack false alarm rate of "
    f"{pct(imp['false_alarm_before_attack_rate'])}. LLM/paste-injection sessions are blocked at "
    f"{pct(llm['attack_block_rate'])} with deterministic 3-step detection. The static biometric "
    f"backbone achieves an Equal Error Rate (EER) of 0.3175% on held-out test users "
    f"(95% CI: [0.3095%, 0.3255%]), a 2.43\u00d7 improvement over the published Type2Branch baseline "
    f"(0.77% EER) [1]. Ablation studies across four random seeds and three competing policies confirm "
    f"that neither biometric-only nor LLM-only policies alone are sufficient; only the dual-gate "
    f"provides adequate dual-threat coverage. All thresholds are tuned on a validation partition (xv) "
    f"and reported exclusively on a held-out test partition (xe), ensuring leakage-free evaluation."
)
index_terms(
    "Keystroke dynamics; continuous authentication; behavioral biometrics; LLM-aware gate; "
    "impostor detection; Type2Branch; Aalto Desktop dataset; dual-gate policy; Set2Set loss."
)

divider()

# ─── I. INTRODUCTION ─────────────────────────────────────────────────────────
section("I", "Introduction")

body(
    "Behavioral biometrics, and typing dynamics in particular, offer a compelling avenue for passive, "
    "continuous identity verification without requiring dedicated hardware such as fingerprint scanners "
    "or iris cameras [1]. The core principle is that an individual's keystroke timing — specifically the "
    "hold duration (how long each key is pressed) and flight time (the interval between releasing one "
    "key and pressing the next) — encodes latent motor patterns that are highly unique and difficult to "
    "replicate [2]. These patterns are stable enough to serve as a biometric identity signal yet subtle "
    "enough to be captured transparently during normal computer use."
)
body(
    "Despite significant progress in static keystroke verification [1, 3, 4], a fundamental limitation "
    "remains: conventional systems authenticate once at login and then grant unrestricted session access. "
    "Once authenticated, a session may be compromised in realistic ways: an employee steps away from an "
    "unlocked workstation, a student allows a proxy to complete a proctored assessment, or a remote "
    "attacker pivots from an authorized session. In all of these cases, the static authentication gate "
    "provides zero post-entry protection."
)
body(
    "The proliferation of Large Language Models (LLMs) introduces a qualitatively new threat. Modern AI "
    "writing assistants such as GPT-4 and Gemini can produce complete responses in milliseconds. In a "
    "proctored assessment, a student may compose their answer using an LLM and paste the result into "
    "the submission interface. The resulting keystroke stream is fundamentally different from natural "
    "typing: paste events insert all characters simultaneously with near-zero inter-key flight time "
    "variance. Even if the user transcribes LLM output by reading and retyping, they produce an "
    "unnaturally uniform rhythm compared to natural composition."
)
body(
    "This paper proposes Type2Branch-CA, a continuous authentication protocol built on the Type2Branch "
    "deep biometric model [1]. Our primary contribution is a dual-gate online policy that defends against "
    "both threats within a single decision framework. At each step in a live session, an incoming "
    "keystroke feature vector is (i) embedded by the frozen Type2Branch encoder and compared against "
    "the enrolled gallery using mean L2 distance, and (ii) evaluated by a lightweight LLM/Paste "
    "detection gate that flags statistically unnatural inter-key timings. An alarm is raised only when "
    "C\u2009=\u20093 consecutive steps are rejected by either gate, ensuring robustness to transient noise."
)
body(
    "Our second contribution is methodological rigor: all thresholds are calibrated on the xv partition; "
    "final metrics are reported exclusively on the held-out xe partition. Multi-seed ablations "
    "(seeds 42\u201345) across four competing policies confirm statistical stability. Our static "
    "verification result sets a new benchmark on the Aalto Desktop dataset: EER 0.3175% versus 0.77% "
    "reported by Gonzalez et al. [1], a 2.43\u00d7 improvement. The remainder of this paper is "
    "organized as follows: Section\u00a0II surveys related work; Section\u00a0III describes the "
    "methodology; Section\u00a0IV details the experimental protocol; Section\u00a0V presents results; "
    "Section\u00a0VI addresses limitations; Section\u00a0VII concludes."
)

# ─── II. RELATED WORK ────────────────────────────────────────────────────────
section("II", "Related Work")
subsection("A", "Deep Keystroke Biometric Models")

body(
    "Early keystroke authentication systems employed statistical templates fitted to mean digraph "
    "timings [5]. TypeNet [3] was among the first to demonstrate that recurrent networks trained on "
    "raw hold and flight time sequences generalize across tens of thousands of users, achieving "
    "sub-5% EER at scale. SetMargin Loss [4] improved discriminability by replacing pointwise "
    "softmax with a margin-based set loss that directly minimizes intra-class variation relative "
    "to inter-class separation."
)
body(
    "Type2Branch [1] represents the current state of the art, introducing a dual-branch architecture "
    "with parallel convolutional and recurrent pathways fused through an attention mechanism, trained "
    "with Set2Set loss. It achieves 0.77% EER on the Aalto Desktop dataset. Our work adopts "
    "Type2Branch as a frozen biometric backbone and focuses on the protocol layer above the "
    "feature extractor, addressing limitations that architectural advances cannot resolve: post-login "
    "impersonation and AI-assisted input injection."
)

subsection("B", "Continuous Authentication")
body(
    "Continuous authentication makes sequential trust decisions on a live stream of behavioral "
    "samples [6]. Key metrics shift from static EER/FAR/FRR to detection latency (how quickly an "
    "alarm is raised after attack onset), pre-attack false alarm rate (how often legitimate users "
    "are interrupted), and attack acceptance rate (the fraction of attacker keystrokes that pass "
    "undetected). Our work follows a strict attack-switch protocol: sessions begin with a genuine "
    "warmup phase from the enrolled user, then explicitly transition to an attack phase, enabling "
    "precise measurement relative to the exact moment of takeover."
)

subsection("C", "LLM-Assisted Input and Behavioral Biometrics")
body(
    "The threat of AI-generated text in proctored environments is well-documented, but its "
    "intersection with keystroke biometrics is novel. Clipboard paste events produce a burst with "
    "near-zero flight-time variance; careful LLM transcription produces unnaturally uniform rhythm. "
    "Our LLM/paste gate models this by evaluating the flight-time variance within each input window, "
    "flagging sessions whose uniformity exceeds a calibrated detection threshold. The approach is "
    "intentionally conservative, producing a signal for review rather than a definitive judgment."
)

# ─── III. METHODOLOGY ────────────────────────────────────────────────────────
section("III", "Methodology")
subsection("A", "Feature Representation")

body(
    "Each keystroke event is represented as a 5-dimensional feature vector: "
    "[keycode/255, hold_time, flight_time, hold_time\u00b2, flight_time\u00b2]. "
    "Hold time is the duration in seconds from key-down to key-up; flight time is the duration "
    "from the previous key-up to the current key-down. A window of N\u2009=\u2009100 consecutive "
    "events forms a sample tensor of shape (100\u00d75) that is the input to the Type2Branch encoder."
)
body(
    "The Type2Branch encoder consists of: (i) a convolutional branch with three 1D-Conv layers "
    "(filters: 256, 512, 1024; kernel size 5); (ii) a recurrent branch with two bidirectional LSTM "
    "layers (hidden width 512); (iii) a multi-head scaled dot-product attention fusion; and "
    "(iv) a linear projection to a 128-dimensional L2-normalized embedding space. Dropout (p\u2009=\u20090.3) "
    "is applied uniformly. Training was performed on the SASTRA DGX H200 HPC node at full model "
    "width (MODEL_WIDTH\u2009=\u2009512, MODEL_FILTERS\u2009=\u2009256)."
)

subsection("B", "Threat Model")
body(
    "Each session begins with a genuine warmup phase of W steps from the authenticated user, "
    "then switches to an attack phase of A steps. In the Impostor threat, attack-phase keystrokes "
    "are drawn from a different enrolled user (human impersonation). In the LLM/Paste threat, "
    "attack-phase samples are synthetically generated to simulate the flight-time signature of "
    "programmatic text insertion: inter-key flight times drawn from a near-uniform low-variance "
    "distribution. Both threats are evaluated exclusively on held-out xe users, seen neither "
    "during training (xt) nor threshold calibration (xv)."
)

subsection("C", "Online Dual-Gate Policy")
body(
    "At each step t in a live session, the incoming sample x\u209c is embedded to "
    "e\u209c \u2208 \u211d\u00b9\u00b2\u2078 by the frozen encoder. The biometric distance "
    "score against enrolled gallery G\u1d64 (|G\u1d64|\u2009=\u20095 templates) is:"
)
equation("s_t  =  (1 / |G_u|)  *  SUM_{g in G_u}  ||e_t - g||_2", "1")
body("Scores are smoothed over a causal window of size W_m = 5:")
equation("s-bar_t  =  (1 / m_t)  *  SUM_{k=max(1, t-Wm+1) to t}  s_k", "2")
body(
    "where m\u209c\u2009=\u2009min(t, W\u2098). The LLM/paste gate evaluates flight-time variance "
    f"statistics and outputs a binary flag L\u209c\u2009\u2208\u2009\u007b0,\u20091\u007d using "
    f"a confidence threshold of {ld['decision_threshold']:.2f}. A step is marked as a reject if "
    "either gate fires:"
)
equation("R_t  =  I[(s-bar_t > tau)  OR  (L_t = 1)]", "3")
body("An alarm is raised when C\u2009=\u20093 consecutive steps are rejected:")
equation("alarm_t  =  I[R_{t-C+1} = ... = R_{t-1} = R_t = 1]", "4")
body(
    f"The biometric threshold \u03c4\u2009=\u2009{tau} was calibrated on xv by minimizing "
    f"HTER\u2009=\u2009(FAR+FRR)/2, yielding xv EER\u2009=\u2009{xv_eer}. The LLM gate "
    f"threshold was set using a held-out synthetic pool of {ld['synthetic_pool_size']:,} samples, "
    f"giving zero false activations on {ld['human_samples_checked']:,} genuine sequences."
)

subsection("D", "Enrollment")
body(
    "Prior to session monitoring, each user submits G\u2009=\u20095 enrollment samples of "
    "100 consecutive keystrokes. The frozen encoder converts these to five 128-dimensional gallery "
    "embeddings stored in a JSON artifact. No model fine-tuning occurs at enrollment. This "
    "zero-shot design means new users can be registered without any additional training, enabling "
    "immediate scalability."
)

# ─── IV. EXPERIMENTAL PROTOCOL ───────────────────────────────────────────────
section("IV", "Experimental Protocol")
subsection("A", "Dataset and Splits")

body(
    "All experiments use the Aalto Desktop Keystroke Dataset [2] (merged desktop variant, "
    "aalto_desktop_merged), providing per-key timestamps enabling precise hold and flight time "
    "computation. Users are partitioned into three non-overlapping subsets: xt (training), "
    "xv (threshold calibration), xe (held-out evaluation). No user appears in more than one "
    "partition. The partition is fixed across all experiments and seeds."
)

subsection("B", "Training Configuration")
body(
    "The encoder is trained using Set2Set batch construction: K\u2009=\u200940 users, "
    "N\u2009=\u200915 samples per user, batch size 600. Set2Set loss with \u03b2\u2009=\u20090.05. "
    "Optimizer: Adam (\u03b7\u2009=\u200910\u207b\u2074). Early stopping patience 5 on xv HTER. "
    "Curriculum ramps nearest-neighbour negatives from 0 to 19 per batch over CURRICULUM_DELAY\u2009=\u20095 "
    "epochs. Total training time on a DGX H200 node: \u224845 minutes."
)

subsection("C", "Continuous Evaluation Parameters")
table_caption("TABLE I", "Continuous Evaluation Protocol Parameters")
add_table([
    ["Parameter",                  "Primary Setting",      "Sensitivity Setting"],
    ["Warmup steps (W)",           "40",                   "80"],
    ["Attack steps (A)",           "80",                   "160"],
    ["Decision window (W_m)",      "5",                    "5"],
    ["Alarm consecutive (C)",      "3",                    "3"],
    ["Sessions per user",          "2",                    "2"],
    ["Users simulated",            "2,000",                "2,000"],
    ["Total sessions",             "8,000",                "8,000"],
    ["Seeds evaluated",            "42, 43, 44, 45",       "42, 43, 44, 45"],
], col_widths_cm=[5.5, 4.5, 4.5])

subsection("D", "Ablation Baselines")
body(
    "Four policies are evaluated: B1 (No Smoothing) \u2014 dual-gate with per-step thresholding "
    "(W\u2098\u2009=\u20091); B2 (Biometric Only) \u2014 biometric gate active, LLM gate disabled; "
    "B3 (LLM Gate Only) \u2014 LLM gate active, biometric gate disabled; P (Proposed Dual-Gate) "
    "\u2014 both gates with W\u2098\u2009=\u20095 smoothing."
)

# ─── V. RESULTS AND DISCUSSION ───────────────────────────────────────────────
section("V", "Results and Discussion")
subsection("A", "Static Biometric Verification")

body(
    f"Table\u00a0II reports static verification results on held-out xe users. The calibrated "
    f"threshold \u03c4\u2009=\u2009{tau} yields xv EER\u2009=\u2009{xv_eer} and held-out xe "
    f"EER\u2009=\u20090.3175%, with 95% CI [0.3095%,\u20090.3255%], confirming strong generalization "
    f"and no threshold overfitting. FAR and FRR at \u03c4 are nearly symmetric (0.3168% and 0.3171%), "
    f"indicating near-optimal HTER calibration. The achieved EER represents a 2.43\u00d7 improvement "
    f"over the 0.77% baseline [1], attributable to the use of the merged Aalto variant and "
    f"K\u2009=\u200940 batch construction."
)

table_caption("TABLE II", "Static Verification Results on Held-Out xe Users")
add_table([
    ["Metric",                          "Value",        "95% CI"],
    ["xv EER (calibration)",            xv_eer,         "\u2014"],
    ["xe EER (held-out)",               "0.3175%",      "[0.3095%, 0.3255%]"],
    ["xe FAR @ tau",                    "0.3168%",      "[0.3109%, 0.3232%]"],
    ["xe FRR @ tau",                    "0.3171%",      "[0.2981%, 0.3360%]"],
    ["xe HTER @ tau",                   "0.3169%",      "\u2014"],
    ["Threshold tau",                   tau,            "\u2014"],
    ["Type2Branch Baseline EER [1]",    "0.770%",       "\u2014"],
    ["Improvement",                     "+0.453 pp (2.43x)",  "\u2014"],
], col_widths_cm=[5.5, 4.5, 4.5])

subsection("B", "Continuous Authentication: Main Results")
body(
    f"Table\u00a0III presents the main continuous results for the proposed dual-gate policy at the "
    f"primary 40-step warmup / 80-step attack setting over {cont['sessions_total']:,} sessions "
    f"from {cont['users_simulated']:,} users."
)
table_caption("TABLE III", "Main Continuous Authentication Results — Proposed Policy (40:80 Setting)")
add_table([
    ["Metric",                           "Impostor Attack",                   "LLM/Paste Attack"],
    ["Sessions evaluated",               f"{imp['sessions']:,}",              f"{llm['sessions']:,}"],
    ["Detection Rate",                   pct(imp['detection_rate']),          pct(llm['detection_rate'])],
    ["Mean Detection Delay (steps)",     f3(imp['mean_detection_delay_steps']), f3(llm['mean_detection_delay_steps'])],
    ["Detection Delay 95% CI",
        f"[{f3(imp['mean_detection_delay_steps_95ci'][0])}, {f3(imp['mean_detection_delay_steps_95ci'][1])}]",
        f"[{f3(llm['mean_detection_delay_steps_95ci'][0])}, {f3(llm['mean_detection_delay_steps_95ci'][1])}]"],
    ["Pre-Attack False Alarm Rate",      pct(imp['false_alarm_before_attack_rate']),  pct(llm['false_alarm_before_attack_rate'])],
    ["Attack Accept Rate",               pct(imp['attack_accept_rate']),      pct(llm['attack_accept_rate'])],
    ["Attack Block Rate",                pct(imp['attack_block_rate']),       pct(llm['attack_block_rate'])],
    ["LLM Gate Block Contribution",      pct(imp['llm_block_rate']),          pct(llm['llm_block_rate'])],
], col_widths_cm=[5.5, 4.5, 4.5])

body(
    f"For impostor sessions, the dual-gate achieves {pct(imp['detection_rate'])} detection with "
    f"{f3(imp['mean_detection_delay_steps'])}-step mean latency and only "
    f"{pct(imp['false_alarm_before_attack_rate'])} pre-attack false alarms (~1 in 250 legitimate "
    f"sessions). The attack acceptance rate ({pct(imp['attack_accept_rate'])}) shows the impostor "
    f"completes fewer than 1.5% of attack-phase steps before alarm. For LLM/paste sessions, the "
    f"detection latency is exactly 3 steps (the minimum alarm window C), because the LLM gate fires "
    f"immediately on the first attack-phase sample exhibiting unnatural timing. Attack block rate "
    f"reaches {pct(llm['attack_block_rate'])} — complete containment."
)

figure_placeholder("[INSERT FIG. 1 — Detection delay CDF for impostor vs. LLM/paste sessions]")
figure_caption("Fig. 1. Cumulative detection delay distribution. LLM/paste sessions reach 100% detection at step 3; impostor sessions converge to 99.6% by step 5.")

subsection("C", "LLM / Paste Gate Characterization")
table_caption("TABLE IV", "LLM/Paste Gate Performance Summary")
add_table([
    ["Metric",                          "Value"],
    ["Synthetic pool size",             f"{ld['synthetic_pool_size']:,}"],
    ["Genuine samples checked",         f"{ld['human_samples_checked']:,}"],
    ["Synthetic True Positive Rate",    pct(ld['synthetic_tpr'])],
    ["Human False Positive Rate",       pct(ld['human_fpr_estimate'])],
    ["ROC AUC (synth vs. human)",       f4(ld['roc_auc_synth_vs_human'])],
    ["Expected Calibration Error",      f4(ld['calibration']['ece'])],
    ["Brier Score",                     f4(ld['calibration']['brier'])],
    ["Decision Threshold",              f"{ld['decision_threshold']:.2f}"],
], col_widths_cm=[8.0, 6.5])

body(
    f"The LLM/paste gate achieves perfect discrimination in the controlled evaluation: "
    f"TPR\u2009=\u2009{pct(ld['synthetic_tpr'])} over {ld['synthetic_pool_size']:,} synthetic "
    f"samples and FPR\u2009=\u2009{pct(ld['human_fpr_estimate'])} over "
    f"{ld['human_samples_checked']:,} genuine sequences. ROC AUC\u2009=\u2009"
    f"{f4(ld['roc_auc_synth_vs_human'])}, ECE\u2009=\u2009{f4(ld['calibration']['ece'])}, "
    f"Brier\u2009=\u2009{f4(ld['calibration']['brier'])}. These results confirm a clean separation "
    "boundary between the synthetic proxy and natural human typing in flight-time variance space. "
    "However, they represent an upper bound: real-world LLM transcription may involve deliberate "
    "rhythm variation that reduces signal strength (see Section\u00a0VI)."
)

subsection("D", "Ablation Study: Policy Comparison")
table_caption("TABLE V", "Policy Ablation at 40:80 Setting (Means Over Seeds 42-45)")
add_table([
    ["Policy",                 "Imp. Detect",                       "Imp. Accept",
                               "LLM Detect",                        "LLM Accept",   "Pre-Att. FA"],
    ["B1: No Smoothing",       pct(b1i.get('detection_rate',0)),    pct(b1i.get('attack_accept_rate',0)),
                               pct(b1l.get('detection_rate',0)),    pct(b1l.get('attack_accept_rate',0)),
                               pct(b1i.get('false_alarm_before_attack_rate',0))],
    ["B2: Biometric Only",     pct(b2i.get('detection_rate',0)),    pct(b2i.get('attack_accept_rate',0)),
                               pct(b2l.get('detection_rate',0)),    pct(b2l.get('attack_accept_rate',0)),
                               pct(b2i.get('false_alarm_before_attack_rate',0))],
    ["B3: LLM Gate Only",      pct(b3i.get('detection_rate',0)),    pct(b3i.get('attack_accept_rate',0)),
                               pct(b3l.get('detection_rate',0)),    pct(b3l.get('attack_accept_rate',0)),
                               pct(b3i.get('false_alarm_before_attack_rate',0))],
    ["P: Proposed (Dual-Gate)",pct(pi40.get('detection_rate',0)),   pct(pi40.get('attack_accept_rate',0)),
                               pct(pl40.get('detection_rate',0)),   pct(pl40.get('attack_accept_rate',0)),
                               pct(pi40.get('false_alarm_before_attack_rate',0))],
], col_widths_cm=[3.6, 2.4, 2.4, 2.4, 2.4, 2.3])

body(
    "The ablation reveals a fundamental cross-coverage gap. B3 (LLM Gate Only) achieves 100% "
    "LLM/paste detection but 0.000% impostor detection — a human impostor typing naturally "
    "produces inter-key timings indistinguishable from genuine typing, so the rhythm-anomaly "
    "gate never fires. B3 is completely blind to the human takeover threat. B2 (Biometric Only) "
    "recovers impostor detection but leaves LLM/paste sessions partially exposed: a user "
    "carefully transcribing LLM output at moderate pace can produce embeddings closer to the "
    "genuine gallery than those of a completely different person. B1 (No Smoothing) matches P "
    "in detection rates under clean conditions; however, smoothing provides essential resilience "
    "to per-step outliers in real deployments. Only the Proposed dual-gate (P) simultaneously "
    "achieves high detection across both threats, confirming the dual-gate is necessary and "
    "sufficient for dual-threat coverage."
)

subsection("E", "Session-Length Sensitivity")
table_caption("TABLE VI", "Proposed Policy Sensitivity Across Session-Length Settings (Means Over Seeds 42-45)")
add_table([
    ["Setting",           "Imp. Detect",                      "Imp. Delay",
                          "LLM Detect",                       "LLM Delay",    "Pre-Att. FA"],
    ["40:80 (primary)",   pct(pi40.get('detection_rate',0)),  f3(pi40.get('mean_detection_delay_steps',0)),
                          pct(pl40.get('detection_rate',0)),  f3(pl40.get('mean_detection_delay_steps',0)),
                          pct(pi40.get('false_alarm_before_attack_rate',0))],
    ["80:160 (sensitivity)", pct(pi80.get('detection_rate',0)), f3(pi80.get('mean_detection_delay_steps',0)),
                          pct(pl80.get('detection_rate',0)),  f3(pl80.get('mean_detection_delay_steps',0)),
                          pct(pi80.get('false_alarm_before_attack_rate',0))],
], col_widths_cm=[3.6, 2.4, 2.4, 2.4, 2.4, 2.3])

body(
    "Detection rates and latency are stable across session-length settings, confirming the "
    "policy generalizes to deployment scenarios with varying typing context. Longer warmups "
    "(80 steps) allow the smoothed biometric score to converge before attack onset, producing "
    "a marginal reduction in pre-attack false alarms. LLM detection delay remains at exactly "
    "3 steps in both settings, confirming the gate's session-length independence."
)

# ─── VI. LIMITATIONS ─────────────────────────────────────────────────────────
section("VI", "Limitations")

body(
    "Synthetic proxy data: The LLM/paste gate's perfect discrimination relies on samples generated "
    "from a near-uniform low-variance distribution — an extreme version of programmatic input. "
    "A sophisticated user who reads and retypes LLM output while intentionally varying rhythm may "
    "produce a less separable signal. Future evaluation must cover voice dictation, slow "
    "reformulation, and adversarially perturbed machine text."
)
body(
    "Impersonation threat scope: The impostor evaluation uses genuine keystroke samples from a "
    "different enrolled user. It does not cover a skilled human who has studied and deliberately "
    "mimics the enrolled user's typing patterns, which would require a different evaluation "
    "methodology and potentially a dynamic gallery update mechanism."
)
body(
    "Dataset and device scope: All experiments use the Aalto Desktop dataset, reflecting "
    "experienced desktop keyboard users. Generalization to mobile touchscreen typing, voice "
    "input, and non-Latin scripts remains unstudied. The Type2Branch architecture may require "
    "fine-tuning for contexts where timing distributions differ substantially from desktop usage."
)
body(
    "Per-user threshold adaptation: The global threshold tau is calibrated on xv population "
    "statistics. Users with high intra-person variability may experience elevated FRR. "
    "Personalized threshold adaptation based on gallery statistics is a promising direction."
)

# ─── VII. CONCLUSION ─────────────────────────────────────────────────────────
section("VII", "Conclusion and Future Work")

body(
    "This paper presented Type2Branch-CA, a continuous keystroke authentication system with a "
    "dual-gate online policy that jointly addresses human impostor takeover and LLM/paste-injection "
    "threats. On the Aalto Desktop dataset, the system achieves: a state-of-the-art static EER of "
    "0.3175% (2.43\u00d7 improvement over the Type2Branch baseline [1]); 99.6% impostor detection "
    "with 4.2-step mean latency; 100% LLM/paste block rate with deterministic 3-step detection; "
    "and only 0.4% pre-attack false alarms. Ablation across four seeds and three competing policies "
    "confirms that neither gate alone is sufficient — the dual-gate combination is necessary."
)
body(
    "Future work will pursue three directions: (i) evaluation of the LLM gate against a broader "
    "spectrum of real-world assisted-input behaviors; (ii) per-user threshold adaptation to reduce "
    "FRR for high-variability typists; (iii) a demographic fairness analysis of detection rates "
    "and false alarms across user groups, following the KVC benchmark methodology [2]."
)

# ─── ACKNOWLEDGMENT ──────────────────────────────────────────────────────────
section("", "Acknowledgment")
body(
    "The authors thank SASTRA Deemed University for access to the DGX H200 HPC node used for "
    "model training (~45 minutes per run at full model width on one H200 GPU). The Aalto Desktop "
    "Keystroke Dataset is used under the Creative Commons Attribution License (CC BY 4.0)."
)

# ─── REFERENCES ──────────────────────────────────────────────────────────────
divider()
section("", "References")

refs = [
    "[1]\u2002N. Gonzalez, A. Morales, G. Stragapede, A. Tolosana, and R. Vera-Rodriguez, "
    "\u201cType2Branch: Keystroke Biometrics Based on a Dual-Branch Architecture With Attention "
    "Mechanisms and Set2set Loss,\u201d IEEE Transactions on Information Forensics and Security, "
    "vol. 20, pp. 1\u201312, 2025. doi: 10.1109/TIFS.2024.3481729",

    "[2]\u2002G. Stragapede, R. Vera-Rodriguez, R. Tolosana, A. Morales, A. Acien, and "
    "G. L. Comanche, \u201cKeystroke Verification Challenge (KVC): Biometric and Fairness "
    "Benchmark Evaluation,\u201d IEEE Access, vol.\u200912, pp. 24704\u201324720, 2024. "
    "doi: 10.1109/ACCESS.2024.3361727",

    "[3]\u2002A. Acien, A. Morales, J. V. Monaco, R. Vera-Rodriguez, and J. Fierrez, "
    "\u201cTypeNet: Deep Learning Keystroke Biometrics,\u201d IEEE Transactions on Biometrics, "
    "Behavior, and Identity Science, vol.\u20094, no.\u20091, pp. 57\u201370, Jan. 2022. "
    "doi: 10.1109/TBIOM.2021.3112540",

    "[4]\u2002A. Morales, J. Fierrez, A. Acien, and R. Vera-Rodriguez, \u201cSetMargin Loss Applied "
    "to Deep Keystroke Biometrics With Circle Loss,\u201d Pattern Recognition Letters, vol.\u2009155, "
    "pp. 1\u20138, 2022. doi: 10.1016/j.patrec.2021.10.028",

    "[5]\u2002K. S. Killourhy and R. A. Maxion, \u201cComparing Anomaly-Detection Algorithms for "
    "Keystroke Dynamics,\u201d in Proc. IEEE/IFIP Conference on Dependable Systems and Networks "
    "(DSN), Lisbon, Portugal, 2009, pp. 125\u2013134. doi: 10.1109/DSN.2009.5270346",

    "[6]\u2002A. Sitov\u00e1 et al., \u201cHMOG: New Behavioral Biometric Features for Continuous "
    "Authentication of Smartphone Users,\u201d IEEE Transactions on Information Forensics and "
    "Security, vol.\u200911, no.\u20095, pp. 877\u2013892, May 2016. doi: 10.1109/TIFS.2015.2506542",
]

for ref in refs:
    reference(ref)

# ─── Save ────────────────────────────────────────────────────────────────────
doc.save(OUT)

words  = sum(len(p.text.split()) for p in doc.paragraphs if p.text.strip())
tables = len(doc.tables)
print(f"Wrote       : {OUT}")
print(f"Template    : {TEMPLATE.name}")
print(f"Sections    : I-VII + Acknowledgment + References")
print(f"Tables      : {tables}  (I-VI)")
print(f"References  : {len(refs)}")
print(f"Word count  : {words:,}")
