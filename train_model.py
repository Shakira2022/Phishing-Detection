from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from features import STRUCTURAL_FEATURE_NAMES, build_features

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "phishing_email.csv"
MODEL_DIR = ROOT / "models"
ARTIFACT_DIR = ROOT / "artifacts"
RANDOM_STATE = 42


def load_dataset(path: Path = DATA_PATH) -> tuple[pd.Series, np.ndarray]:
    df = pd.read_csv(path)
    text_col = next((c for c in ["text_combined", "Email Text", "text", "body", "message", "content"] if c in df.columns), None)
    label_col = next((c for c in ["Email Type", "label", "class", "target", "category"] if c in df.columns), None)
    if not text_col or not label_col:
        raise ValueError(f"Could not find text/label columns in {list(df.columns)}")
    texts = df[text_col].fillna("").astype(str)
    raw = df[label_col].astype(str).str.strip().str.lower()
    labels = raw.map(lambda x: 1 if x in {"1", "phishing", "phishing email", "malicious", "yes", "true"} else 0).to_numpy()
    if len(np.unique(labels)) != 2:
        raise ValueError("The dataset must contain both safe and phishing labels.")
    return texts, labels


def metrics_for(model: SGDClassifier, x, y) -> dict[str, float]:
    pred = model.predict(x)
    prob = model.predict_proba(x)[:, 1]
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, prob)),
        "loss": float(log_loss(y, model.predict_proba(x), labels=[0, 1])),
    }


def save_plots(history: list[dict[str, float]], model, x_test, y_test) -> None:
    ARTIFACT_DIR.mkdir(exist_ok=True)
    h = pd.DataFrame(history)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, col in zip(axes.ravel(), ["accuracy", "precision", "recall", "f1", "roc_auc", "loss"]):
        ax.plot(h["epoch"], h[col], marker="o", linewidth=1.8)
        ax.set_title(col.replace("_", " ").title())
        ax.set_xlabel("Epoch")
        ax.grid(alpha=0.25)
    fig.suptitle("Validation metrics during training", fontsize=15)
    fig.tight_layout()
    fig.savefig(ARTIFACT_DIR / "training_metrics.png", dpi=160)
    plt.close(fig)

    prob = model.predict_proba(x_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, prob)
    pr, rec, _ = precision_recall_curve(y_test, prob)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(fpr, tpr, label=f"AUC = {roc_auc_score(y_test, prob):.3f}")
    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5)
    axes[0].set(title="ROC curve", xlabel="False positive rate", ylabel="True positive rate")
    axes[0].legend()
    axes[1].plot(rec, pr)
    axes[1].set(title="Precision-recall curve", xlabel="Recall", ylabel="Precision")
    fig.tight_layout()
    fig.savefig(ARTIFACT_DIR / "roc_pr_curves.png", dpi=160)
    plt.close(fig)

    disp = ConfusionMatrixDisplay(confusion_matrix(y_test, model.predict(x_test)), display_labels=["Safe", "Phishing"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Test confusion matrix")
    plt.tight_layout()
    plt.savefig(ARTIFACT_DIR / "confusion_matrix.png", dpi=160)
    plt.close()


def train() -> dict:
    MODEL_DIR.mkdir(exist_ok=True)
    ARTIFACT_DIR.mkdir(exist_ok=True)
    texts, y = load_dataset()
    x_train, x_temp, y_train, y_temp = train_test_split(texts, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE)
    x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE)
    pd.DataFrame({"text": x_test, "label": y_test}).to_csv(ARTIFACT_DIR / "test_set.csv", index=False)
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 3), min_df=3, max_features=20000, sublinear_tf=True)
    x_train_v = build_features(vectorizer, x_train, fit=True)
    x_val_v = build_features(vectorizer, x_val)
    x_test_v = build_features(vectorizer, x_test)
    model = SGDClassifier(loss="log_loss", alpha=1e-5, random_state=RANDOM_STATE, average=True)
    history, best_f1, best_epoch, stale = [], -1.0, 0, 0
    for epoch in range(1, 31):
        order = np.random.default_rng(RANDOM_STATE + epoch).permutation(x_train_v.shape[0])
        model.partial_fit(x_train_v[order], y_train[order], classes=np.array([0, 1]))
        row = {"epoch": epoch, **metrics_for(model, x_val_v, y_val)}
        history.append(row)
        if row["f1"] > best_f1 + 1e-4:
            best_f1, best_epoch, stale = row["f1"], epoch, 0
            joblib.dump({"vectorizer": vectorizer, "model": model, "label_names": {0: "Safe", 1: "Phishing"}, "structural_feature_names": STRUCTURAL_FEATURE_NAMES}, MODEL_DIR / "phishing_model.joblib")
        else:
            stale += 1
        if stale >= 5:
            break
    bundle = joblib.load(MODEL_DIR / "phishing_model.joblib")
    best_model = bundle["model"]
    test_metrics = metrics_for(best_model, x_test_v, y_test)
    report = classification_report(y_test, best_model.predict(x_test_v), target_names=["Safe", "Phishing"], output_dict=True, zero_division=0)
    result = {"dataset_rows": int(len(texts)), "split_sizes": {"train": len(x_train), "validation": len(x_val), "test": len(x_test)}, "best_epoch": best_epoch, "stopped_after_epoch": len(history), "patience": 5, "test_metrics": test_metrics, "classification_report": report}
    (ARTIFACT_DIR / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (ARTIFACT_DIR / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(history).to_csv(ARTIFACT_DIR / "metrics.csv", index=False)
    save_plots(history, best_model, x_test_v, y_test)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    train()
