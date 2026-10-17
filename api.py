from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from features import build_features

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "phishing_model.joblib"
app = FastAPI(title="ITRI625 Phishing Email Detector", version="1.0")


class EmailRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Email subject/body text")


def get_bundle():
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model not trained. Run python train_model.py first.")
    return joblib.load(MODEL_PATH)


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": MODEL_PATH.exists()}


@app.post("/predict")
def predict(payload: EmailRequest):
    bundle = get_bundle()
    x = build_features(bundle["vectorizer"], [payload.text])
    model = bundle["model"]
    probability = float(model.predict_proba(x)[0, 1])
    label = "Phishing" if probability >= 0.5 else "Safe"
    coef = model.coef_[0]
    terms = list(bundle["vectorizer"].get_feature_names_out()) + bundle.get("structural_feature_names", [])
    contributions = sorted(zip(terms, (x.toarray()[0] * coef)), key=lambda pair: abs(pair[1]), reverse=True)
    explanation = [{"term": term, "contribution": round(float(value), 4)} for term, value in contributions[:5] if value != 0]
    return {"label": label, "phishing_probability": round(probability, 4), "confidence": round(max(probability, 1 - probability), 4), "top_terms": explanation}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
