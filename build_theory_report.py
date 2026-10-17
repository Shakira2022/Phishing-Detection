from pathlib import Path
import json
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "ITRI625_Theory_Report_Updated.docx"
RESULTS = json.loads((ROOT / "artifacts" / "results.json").read_text(encoding="utf-8"))


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def borders(table, color="D9D9D9"):
    tbl_pr = table._tbl.tblPr
    borders_el = tbl_pr.first_child_found_in("w:tblBorders")
    if borders_el is None:
        borders_el = OxmlElement("w:tblBorders")
        tbl_pr.append(borders_el)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        el = borders_el.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            borders_el.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)


def set_cell_text(cell, text, bold=False, color="000000", size=9.5):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_table_widths(table, widths):
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = width
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(int(width.inches * 1440)))
            tc_w.set(qn("w:type"), "dxa")


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.12
    return p


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.75)
section.bottom_margin = Inches(0.7)
section.left_margin = Inches(0.85)
section.right_margin = Inches(0.85)

styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"]._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
styles["Normal"]._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
styles["Normal"].font.size = Pt(10.5)
for style_name, size in (("Title", 23), ("Heading 1", 15), ("Heading 2", 12)):
    styles[style_name].font.name = "Aptos Display"
    styles[style_name]._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    styles[style_name]._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    styles[style_name].font.size = Pt(size)
    styles[style_name].font.color.rgb = RGBColor(0, 0, 0)

title = doc.add_paragraph(style="Title")
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.add_run("ITRI625 Theory Report")
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("Context Aware Phishing Email Detection")
run.bold = True
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(31, 78, 121)
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("Machine Learning Project | Theory Component | 30 marks").italic = True

add_heading(doc, "Executive summary", 1)
add_body(doc, "This report presents a supervised machine-learning system for detecting phishing emails from their textual content and structural characteristics. The system was trained on the Kaggle Phishing Email Dataset, using 82,486 labelled messages. It combines TF-IDF word unigrams, bigrams and trigrams with twelve email-level features, including URL frequency, urgency language, credential requests, call-to-action terms, monetary language, punctuation, character ratios and message length. A linear online classifier is trained in a Jupyter Notebook with a stratified train, validation and test split and patience-based early stopping.")
add_body(doc, f"The held-out test set contains {RESULTS['split_sizes']['test']:,} messages. The current run achieved accuracy {RESULTS['test_metrics']['accuracy']:.2%}, precision {RESULTS['test_metrics']['precision']:.2%}, recall {RESULTS['test_metrics']['recall']:.2%}, F1-score {RESULTS['test_metrics']['f1']:.2%} and ROC-AUC {RESULTS['test_metrics']['roc_auc']:.4f}. These results indicate strong performance on the same distribution as the training data, but they do not prove that the model will generalise to new institutions, languages, campaigns or attacker strategies. Human verification remains necessary for deployment.")

add_heading(doc, "3.1 Model scenario", 1)
add_body(doc, "The scenario is an email-security assistant that analyses an email before a user follows a link, opens an attachment or responds to a request. The user pastes the email into a Tkinter desktop application. The application sends the text to a FastAPI endpoint, which returns a predicted class, phishing probability and the most influential features. The system is designed as a decision-support tool: it can prioritise suspicious messages for review, but it should not be the sole control for blocking email or requesting user credentials.")
add_body(doc, "This scenario is useful in cybersecurity because phishing is a social-engineering attack that exploits urgency, trust, authority and familiar services. A detector can reduce exposure by identifying recurring linguistic and structural cues before a user interacts with the message. It is particularly useful as a first-pass filter for security awareness training, help-desk triage and mailbox review. The system can also support explainability by showing why a prediction was produced rather than presenting only an unexplained label.")

add_heading(doc, "3.2 Model architecture", 1)
add_body(doc, "The architecture is a sparse, context-aware text-classification pipeline implemented in Python and executed from the Jupyter Notebook. The data preparation and prediction stages are as follows:")
architecture = [
    ("Input", "Email text from the Kaggle combined text field; labels are 0 for legitimate and 1 for phishing."),
    ("Text representation", "TF-IDF with word unigrams, bigrams and trigrams. N-grams preserve short phrase context, such as 'verify account' or 'click here', rather than treating every word as independent."),
    ("Structural representation", "Twelve numeric signals: log-scaled message length, log-scaled word count, URL count, exclamation and question counts, digit ratio, uppercase ratio, urgency terms, credential terms, call-to-action terms, money terms and HTML markers."),
    ("Feature combination", "The sparse TF-IDF matrix and structural feature matrix are horizontally concatenated. This gives the classifier both language context and message-level behaviour."),
    ("Classifier", "SGDClassifier with log-loss and averaging. The model is updated one training epoch at a time with partial_fit, which makes validation logging and early stopping explicit."),
    ("Output", "A binary class, a probability-like score from the logistic loss model, and the highest-weight features used for a local explanation."),
]
table = doc.add_table(rows=1, cols=2)
table.autofit = False
table.columns[0].width = Inches(1.55)
table.columns[1].width = Inches(5.95)
borders(table)
for i, h in enumerate(("Stage", "Implementation and purpose")):
    set_cell_text(table.rows[0].cells[i], h, bold=True, color="FFFFFF", size=9.5)
    shade(table.rows[0].cells[i], "1F4E79")
for stage, desc in architecture:
    cells = table.add_row().cells
    set_cell_text(cells[0], stage, bold=True, size=9.2)
    set_cell_text(cells[1], desc, size=9.2)
    shade(cells[0], "EAF2F8")
set_table_widths(table, [Inches(1.55), Inches(5.95)])

add_body(doc, "TF-IDF is appropriate for this project because email classification produces high-dimensional sparse vectors, and linear models are computationally efficient and interpretable in this setting. The use of n-grams provides limited local context while retaining a lightweight desktop deployment. The structural features address a limitation of text-only classification by recording patterns such as multiple URLs, credential language and urgent calls to action. The model is therefore more informative than a bag of isolated words, although it is not a deep semantic language model.")
add_body(doc, "The bonus explainable-AI feature uses the model coefficients and the non-zero features of an individual message. Positive contributions support the phishing class and negative contributions support the legitimate class. The desktop app displays the most influential terms or structural signals. This is useful for review, but feature contribution is not proof that a message is malicious; it explains the model's reasoning, not the sender's identity.")

add_heading(doc, "3.3 Model result analysis", 1)
metrics = RESULTS["test_metrics"]
add_body(doc, "The dataset was divided into training, validation and testing subsets using stratification so that both classes were represented in each subset. The validation set was used after every epoch to monitor F1-score, select the best model and control early stopping. The test set was kept separate for the final evaluation and was not used to update model weights.")
mt = doc.add_table(rows=1, cols=3)
mt.autofit = False
mt.columns[0].width = Inches(2.7); mt.columns[1].width = Inches(1.5); mt.columns[2].width = Inches(3.3)
borders(mt)
for i, h in enumerate(("Metric", "Test result", "Interpretation")):
    set_cell_text(mt.rows[0].cells[i], h, bold=True, color="FFFFFF")
    shade(mt.rows[0].cells[i], "1F4E79")
metric_rows = [
    ("Accuracy", f"{metrics['accuracy']:.2%}", "Overall proportion of correct classifications."),
    ("Precision", f"{metrics['precision']:.2%}", "Most messages flagged as phishing were phishing in this test set."),
    ("Recall", f"{metrics['recall']:.2%}", "The model detected most phishing messages; missed attacks remain possible."),
    ("F1-score", f"{metrics['f1']:.2%}", "Balances precision and recall."),
    ("ROC-AUC", f"{metrics['roc_auc']:.4f}", "Strong ranking separation on the held-out test distribution."),
    ("Log loss", f"{metrics['loss']:.4f}", "Penalises incorrect and overconfident probability estimates."),
]
for row in metric_rows:
    cells = mt.add_row().cells
    for i, value in enumerate(row): set_cell_text(cells[i], value, bold=(i == 0), size=9.2)
    shade(cells[0], "EAF2F8")
set_table_widths(mt, [Inches(2.15), Inches(1.35), Inches(4.0)])
add_heading(doc, "Figures from the experiment", 2)
for caption, filename in [
    ("Figure 1. Validation metrics logged during training.", "training_metrics.png"),
    ("Figure 2. ROC and precision-recall curves on the test set.", "roc_pr_curves.png"),
    ("Figure 3. Test-set confusion matrix.", "confusion_matrix.png"),
]:
    p = doc.add_paragraph(caption)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    image_p = doc.add_paragraph()
    image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_p.add_run().add_picture(str(ROOT / "artifacts" / filename), width=Inches(6.45))
add_body(doc, "The confusion matrix and ROC/precision-recall graphs should be read together with these values. High recall is valuable because a missed phishing email can lead to credential theft or malware execution. High precision is also important because excessive false positives can cause users to ignore warnings or overwhelm security teams. The current results are strong, but they are measured on a dataset drawn from the same general distribution as the training data. The model's false-positive response to a legitimate university finance-and-wellness invitation demonstrates the practical limitation: a legitimate message can contain words such as 'financial', 'registration' and 'click' that resemble learned phishing patterns.")
add_body(doc, "The strongest conclusion is therefore conditional: the model is effective as a text-based classifier on the Kaggle test distribution, but it is not sufficient as a stand-alone real-world phishing decision system. A stronger evaluation would include a time-separated test set, institution-specific legitimate newsletters, current phishing campaigns, sender/header features and calibration analysis. Monitoring should track false positives and false negatives after deployment.")

add_heading(doc, "3.4 Real-world use of models in cybersecurity", 1)
add_body(doc, "Machine-learning models are used across cybersecurity for intrusion detection, threat classification, anomaly detection and risk assessment. In intrusion detection, models learn relationships among network flows, ports, protocols, byte counts, timing and known attack labels. In threat classification, models categorise emails, URLs, malware reports or incident descriptions. In anomaly detection, a model learns a baseline of normal behaviour and highlights deviations. In risk assessment, multiple signals can be combined into a prioritised score for analyst review rather than a simple allow-or-block decision.")
add_body(doc, "For phishing email detection, a layered deployment is more realistic than a single classifier. A content model can analyse text and wording; a separate reputation layer can evaluate domains, URLs, sender authentication and attachment types; and a policy layer can apply organisational context. The resulting risk score can route messages to quarantine, user warnings or security analysts. The model in this project represents the content layer and should be integrated with these additional controls before production use.")
add_body(doc, "The main strengths of machine learning are scale, speed and the ability to identify combinations of signals that are difficult to review manually across thousands of messages. A well-designed model can provide consistent triage and support analysts with explanations. The main limitations are data dependence, distribution shift, adversarial adaptation and calibration. Attackers can alter wording, domains, layout or delivery patterns. Legitimate communications can also resemble phishing because modern organisations use links, forms, cloud services and financial language. Research on phishing detection identifies concept drift and false positives as continuing challenges, particularly when datasets are limited or mixed across sources [1, 2].")
add_body(doc, "Data quality is another practical challenge. Labels may confuse spam, advertising and phishing; duplicate messages can leak between train and test sets; and a random split may overestimate performance when near-duplicate campaigns occur in both subsets. The Kaggle dataset is useful for a reproducible student project, but operational systems require broader sources, temporal validation and regular relabelling. Academic reviews identify TF-IDF, word embeddings and supervised classifiers as common approaches, while newer work explores transformers and semantic representations for paraphrase and context [1, 3].")
add_body(doc, "False positives have an operational cost: they interrupt legitimate work and reduce trust in security warnings. False negatives can be more severe because the user may interact with the malicious message. Thresholds should therefore be chosen according to organisational risk, with a middle 'review' band for uncertain cases. The desktop application follows this principle by showing the probability and influential features and warning that human verification is required. Explainable AI can improve analyst understanding, but explanations must be treated as evidence about the model rather than proof of malicious intent [4].")
add_body(doc, "Concept drift requires monitoring after deployment. The system should record reviewed outcomes, measure precision and recall over time, detect changes in message vocabulary and retrain using newly labelled examples. NIST's adversarial machine-learning guidance also highlights threats such as poisoning and evasion, which means training data and model updates need access control, provenance and review [5]. In practice, the best use of this model is as one layer in a defence-in-depth programme that includes email authentication, URL scanning, attachment sandboxing, user training, incident reporting and human oversight.")

add_heading(doc, "Conclusion", 1)
add_body(doc, "The project satisfies the theory requirements by defining a relevant cybersecurity scenario, explaining a reproducible context-aware architecture, analysing validation and test results, and evaluating real-world deployment considerations. The model demonstrates strong performance on the selected dataset and adds an interpretable desktop workflow. Its results should nevertheless be presented with appropriate caution: generalisation, concept drift, false positives, false negatives and the difference between model evidence and actual sender authenticity remain central security concerns.")

add_heading(doc, "References", 1)
refs = [
    "[1] Al-Ahmad, A., Kahtan, H., Hameed, S. and others. A Systematic Literature Review on Phishing Email Detection Using Natural Language Processing Techniques. IEEE Access, 2022. DOI: 10.1109/ACCESS.2022.3183083.",
    "[2] Shmalko, M., Abuadbba, A., Gaire, R., Wu, T., Paik, H.-Y. and Nepal, S. Profiler: Profile-Based Model to Detect Phishing Emails. arXiv:2208.08745, 2022.",
    "[3] Vishva, E. S. and Aju, D. Phisher Fighter: Website Phishing Detection System Based on URL and Term Frequency-Inverse Document Frequency Values. Journal of Cyber Security and Mobility, 11(1), 83-104, 2021. DOI: 10.13052/jcsm2245-1439.1114.",
    "[4] Explainable AI for Transparent Phishing Email Detection. IEEE Conference Publication, 2024. DOI: 10.1109/ICATC64549.2024.11025302.",
    "[5] National Institute of Standards and Technology. Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations. NIST AI 100-2e2023, 2023.",
    "[6] Kaggle. Phishing Email Dataset, naserabdullahalam. Available at: https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset/data.",
]
for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.05

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run("ITRI625 Theory Report | Phishing Email Detection").font.size = Pt(8)

doc.core_properties.title = "ITRI625 Theory Report Context Aware Phishing Email Detection"
doc.core_properties.subject = "Theory component for the ITRI625 machine learning project"
doc.core_properties.author = "ITRI625 Project"
doc.save(OUT)
print(OUT)
