# ITRI625 Phishing Email Detection Project

This project implements the practical requirements in the ITRI625 brief:

- cybersecurity classification model for safe vs phishing email
- stratified train/validation/test split
- per-epoch accuracy, precision, recall, F1, ROC-AUC and log loss
- Matplotlib metric, ROC/PR and confusion-matrix figures
- patience-based early stopping
- FastAPI prediction endpoint
- Tkinter desktop application
- lightweight explainability using the most influential TF-IDF terms
- context-aware feature engineering using word trigrams and email-structure signals

## Run it

```powershell
python -m pip install -r requirements.txt
# First run every cell in the Jupyter notebook.
# It downloads the dataset, trains the model, logs metrics, plots figures,
# applies early stopping, and exports models/phishing_model.joblib.
# Then start the API:
python api.py
```

In a second terminal:

```powershell
python desktop_app.py
```

The trained context-aware model and figures are written to `models/` and `artifacts/`.

The notebook also exports `artifacts/test_set.csv`. In the desktop app, click **Load held-out test CSV**, select that file, browse with **Previous** and **Next**, and click **Test selected record**. The GUI displays the actual label, prediction, probability, and whether the prediction was correct.

## Dataset

The project uses the Kaggle [Phishing Email Dataset](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset/data). Extract `phishing_email.csv` into `data/`. It contains `text_combined` and `label` columns, where `0` is legitimate and `1` is phishing. The Kaggle download also includes several source-corpus CSV files; the notebook uses the combined `phishing_email.csv` file.

## Notebook

Open `notebooks/phishing_detection.ipynb` in Jupyter or VS Code and run every cell from top to bottom. It is the primary model-training submission: it downloads the dataset, prepares the data, trains the model, displays per-epoch metrics, shows the required figures, evaluates the test set, demonstrates explainability, and exports the model used by the API. `train_model.py` is retained as an optional command-line helper, but is not required for the notebook workflow.

## Git/version control

Recommended commands:

```powershell
git init
git add .
git commit -m "Implement ITRI625 phishing detection project"
```

This is an educational classifier and should support, not replace, human review. It has been trained on a small research dataset and should not be used as the sole control for real email security decisions.
