import csv
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

import requests

API_URL = "http://127.0.0.1:8000"
test_records = []
test_index = 0
csv.field_size_limit(100 * 1024 * 1024)


def api_classify(text, actual_label=None):
    if len(text.strip()) < 3:
        messagebox.showwarning("Missing text", "Paste or load an email message first.")
        return
    try:
        response = requests.post(f"{API_URL}/predict", json={"text": text.strip()}, timeout=10)
        response.raise_for_status()
        result = response.json()
        colour = "#b91c1c" if result["label"] == "Phishing" else "#166534"
        verdict_text = f"Model prediction: {result['label']}  |  phishing probability: {result['phishing_probability']:.2%}"
        if actual_label is not None:
            correct = result["label"] == actual_label
            verdict_text += f"\nActual: {actual_label}  |  {'CORRECT' if correct else 'INCORRECT'}"
            colour = "#166534" if correct else "#b91c1c"
        verdict.config(text=verdict_text + "\nUse human verification before taking action.", fg=colour)
        explanation.delete("1.0", tk.END)
        explanation.insert(tk.END, json.dumps(result["top_terms"], indent=2))
    except requests.RequestException as exc:
        messagebox.showerror("API unavailable", f"Start the API with: python api.py\n\n{exc}")


def classify_manual():
    api_classify(email_box.get("1.0", tk.END))


def classify_selected():
    if not test_records:
        messagebox.showinfo("No test data", "Load artifacts/test_set.csv first.")
        return
    record = test_records[test_index]
    api_classify(record["text"], record["actual"])


def load_test_set():
    global test_records, test_index
    path = filedialog.askopenfilename(title="Select held-out test set", initialdir=str(Path(__file__).resolve().parent / "artifacts"), filetypes=[("CSV files", "*.csv")])
    if not path:
        return
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("The CSV contains no rows.")
        text_key = next((key for key in ("text", "text_combined", "body", "Email Text") if key in rows[0]), None)
        label_key = next((key for key in ("label", "actual_label", "Email Type") if key in rows[0]), None)
        if not text_key or not label_key:
            raise ValueError("Expected text and label columns. Use artifacts/test_set.csv exported by the notebook.")
        def to_label(value):
            value = str(value).strip().lower()
            return "Phishing" if value in {"1", "phishing", "phishing email", "malicious", "true"} else "Legitimate"
        test_records = [{"text": row[text_key], "actual": to_label(row[label_key])} for row in rows]
        test_index = 0
        test_file_label.config(text=f"Loaded {len(test_records):,} held-out test records")
        show_test_record()
    except (OSError, ValueError, KeyError) as exc:
        messagebox.showerror("Could not load test set", str(exc))


def show_test_record():
    if not test_records:
        return
    record = test_records[test_index]
    email_box.delete("1.0", tk.END)
    email_box.insert(tk.END, record["text"])
    test_position.config(text=f"Test record {test_index + 1:,} of {len(test_records):,} | actual label: {record['actual']}")
    verdict.config(text="Ready to test selected record", fg="#1f2937")


def previous_test():
    global test_index
    if test_records:
        test_index = (test_index - 1) % len(test_records)
        show_test_record()


def next_test():
    global test_index
    if test_records:
        test_index = (test_index + 1) % len(test_records)
        show_test_record()


root = tk.Tk()
root.title("ITRI625 Phishing Email Detector")
root.geometry("820x720")
root.minsize(680, 560)
tk.Label(root, text="Phishing Email Detector", font=("Segoe UI", 18, "bold")).pack(pady=(15, 3))
tk.Label(root, text="Manual mode: paste an email. Test-set mode: load the held-out CSV exported by the notebook.").pack()
controls = tk.Frame(root)
controls.pack(pady=10)
tk.Button(controls, text="Load held-out test CSV", command=load_test_set).grid(row=0, column=0, padx=4)
tk.Button(controls, text="Previous", command=previous_test).grid(row=0, column=1, padx=4)
tk.Button(controls, text="Next", command=next_test).grid(row=0, column=2, padx=4)
tk.Button(controls, text="Test selected record", command=classify_selected, bg="#7c3aed", fg="white").grid(row=0, column=3, padx=4)
test_file_label = tk.Label(root, text="No held-out test CSV loaded", fg="#4b5563")
test_file_label.pack()
test_position = tk.Label(root, text="", fg="#4b5563")
test_position.pack(pady=(2, 5))
tk.Label(root, text="Email text", anchor="w").pack(fill="x", padx=24, pady=(8, 4))
email_box = scrolledtext.ScrolledText(root, height=14, wrap=tk.WORD, font=("Segoe UI", 10))
email_box.pack(fill="both", expand=True, padx=24)
tk.Button(root, text="Analyse manually entered email", command=classify_manual, bg="#1d4ed8", fg="white", padx=20, pady=8).pack(pady=12)
verdict = tk.Label(root, text="No result yet", font=("Segoe UI", 13, "bold"))
verdict.pack()
tk.Label(root, text="Top influential terms (XAI bonus feature)", anchor="w").pack(fill="x", padx=24, pady=(14, 4))
explanation = scrolledtext.ScrolledText(root, height=7, wrap=tk.WORD, font=("Consolas", 9))
explanation.pack(fill="both", expand=True, padx=24, pady=(0, 16))
root.mainloop()
