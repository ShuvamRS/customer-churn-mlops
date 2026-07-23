"""
app.py — the prediction service. Downloads model.joblib from S3 and serves predictions.

This is the thing that gets containerized, automated, and deployed. It is
intentionally stateless: no database, no cache. It downloads a model into
memory when the app starts and answers requests.

Run locally:  uvicorn app:app --reload --port 8000
Interactive docs:  http://localhost:8000/docs
"""

import os

import boto3
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field


MODEL_PATH = os.getenv("MODEL_PATH", "model.joblib")


def get_required_env(name):
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


def download_model_from_s3():
    s3_bucket_name = get_required_env("S3_BUCKET_NAME")
    model_s3_key = get_required_env("MODEL_S3_KEY")
    aws_region = get_required_env("AWS_REGION")

    s3_client = boto3.client("s3", region_name=aws_region)
    s3_client.download_file(s3_bucket_name, model_s3_key, MODEL_PATH)

    print(f"Downloaded model from s3://{s3_bucket_name}/{model_s3_key}")


app = FastAPI(title="Churn Prediction API", version="1.0.0")

download_model_from_s3()

# Load once at startup, not per-request.
_bundle = joblib.load(MODEL_PATH)
_model = _bundle["model"]
_features = _bundle["features"]
_threshold = _bundle["threshold"]
_metrics = _bundle["metrics"]


class Customer(BaseModel):
    gender: str = Field(..., examples=["Female"])
    SeniorCitizen: int = Field(..., ge=0, le=1, examples=[0])
    Partner: str = Field(..., examples=["Yes"])
    Dependents: str = Field(..., examples=["No"])
    tenure: int = Field(..., ge=0, examples=[2])
    PhoneService: str = Field(..., examples=["Yes"])
    MultipleLines: str = Field(..., examples=["No"])
    InternetService: str = Field(..., examples=["Fiber optic"])
    OnlineSecurity: str = Field(..., examples=["No"])
    OnlineBackup: str = Field(..., examples=["Yes"])
    DeviceProtection: str = Field(..., examples=["No"])
    TechSupport: str = Field(..., examples=["No"])
    StreamingTV: str = Field(..., examples=["Yes"])
    StreamingMovies: str = Field(..., examples=["Yes"])
    Contract: str = Field(..., examples=["Month-to-month"])
    PaperlessBilling: str = Field(..., examples=["Yes"])
    PaymentMethod: str = Field(..., examples=["Electronic check"])
    MonthlyCharges: float = Field(..., ge=0, examples=[95.0])
    TotalCharges: float = Field(..., ge=0, examples=[190.0])


@app.get("/health")
def health():
    """Liveness/readiness probe target for Kubernetes."""
    return {
        "status": "ok",
        "model_metrics": _metrics,
    }


@app.post("/predict")
def predict(customer: Customer):
    customer_data = customer.model_dump()
    row = pd.DataFrame([{feature: customer_data[feature] for feature in _features}])

    proba = float(_model.predict_proba(row)[0][1])

    return {
        "churn": bool(proba >= _threshold),
        "churn_probability": round(proba, 4),
        "threshold": _threshold,
    }
