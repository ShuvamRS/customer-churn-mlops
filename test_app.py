"""
test_app.py — the tests Jenkins runs before building the image.

Two flavors of test, which is the whole point of ML CI:
  1. Normal app tests: does the endpoint work, is the response shaped right.
  2. Behavioral test: does the model make *sensible* predictions
     (a clearly high-risk customer should score higher than a low-risk one).

Run:  pytest -q
"""
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

HIGH_RISK = {
    "gender": "Female",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 2,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "Yes",
    "StreamingMovies": "Yes",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 95.0,
    "TotalCharges": 190.0,
}
LOW_RISK = {
    "gender": "Male",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "Yes",
    "tenure": 60,
    "PhoneService": "Yes",
    "MultipleLines": "Yes",
    "InternetService": "DSL",
    "OnlineSecurity": "Yes",
    "OnlineBackup": "Yes",
    "DeviceProtection": "Yes",
    "TechSupport": "Yes",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Two year",
    "PaperlessBilling": "No",
    "PaymentMethod": "Credit card (automatic)",
    "MonthlyCharges": 40.0,
    "TotalCharges": 2400.0,
}


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "model_metrics" in body


def test_predict_response_shape():
    r = client.post("/predict", json=HIGH_RISK)
    assert r.status_code == 200
    body = r.json()
    assert "churn" in body
    assert "churn_probability" in body
    assert "threshold" in body
    assert isinstance(body["churn"], bool)
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert 0.0 <= body["threshold"] <= 1.0


def test_validation_rejects_bad_input():
    bad = dict(HIGH_RISK, tenure=-1)
    assert client.post("/predict", json=bad).status_code == 422


def test_model_behaves_sensibly():
    high = client.post("/predict", json=HIGH_RISK).json()["churn_probability"]
    low = client.post("/predict", json=LOW_RISK).json()["churn_probability"]
    assert high > low, "high-risk customer should out-score low-risk one"
