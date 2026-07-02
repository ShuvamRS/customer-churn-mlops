"""
train.py — trains the churn prediction model and saves it to model.joblib.

This script uses a locally downloaded Telco Customer Churn dataset, trains a
scikit-learn pipeline, evaluates the model with classification metrics, and
saves the trained model artifact for the prediction API.

Run:  python train.py
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DATA_PATH = Path("data/Telco-Customer-Churn.csv")
MODEL_PATH = "model.joblib"
RANDOM_STATE = 42

ROC_AUC_THRESHOLD = 0.80
RECALL_THRESHOLD = 0.60
THRESHOLD_CANDIDATES = [x / 100 for x in range(20, 81)]

NUMERIC_FEATURES = [
    "SeniorCitizen",
    "tenure",
    "MonthlyCharges",
    "TotalCharges",
]

CATEGORICAL_FEATURES = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "Churn"


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # TotalCharges is stored as text in the raw CSV and has a few blank values.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    return df


def build_model():
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipeline, NUMERIC_FEATURES),
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
    ])

    # class_weight helps because churn datasets usually have fewer churners.
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ])

    return model


def evaluate_model(y_true, y_pred, y_prob):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, y_prob), 4),
    }


def find_best_threshold(y_true, y_prob):
    best_threshold = 0.50
    best_f1 = 0

    for threshold in THRESHOLD_CANDIDATES:
        y_pred = (y_prob >= threshold).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)

        if score > best_f1:
            best_f1 = score
            best_threshold = threshold

    return best_threshold


def print_feature_weights(model, top_n=8):
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["model"]

    feature_names = preprocessor.get_feature_names_out()
    weights = classifier.coef_[0]

    importance = pd.DataFrame({
        "feature": feature_names,
        "weight": weights,
    })

    print("\nTop churn risk factors:")
    print(
        importance.sort_values("weight", ascending=False)
        .head(top_n)
        .to_string(index=False)
    )

    print("\nTop retention factors:")
    print(
        importance.sort_values("weight")
        .head(top_n)
        .to_string(index=False)
    )


def main():
    df = load_data()

    X = df[FEATURES]
    y = (df[TARGET] == "Yes").astype(int)


    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=y_train_full,
    )

    model = build_model()
    model.fit(X_train, y_train)

    val_prob = model.predict_proba(X_val)[:, 1]
    best_threshold = find_best_threshold(y_val, val_prob)

    val_pred = (val_prob >= best_threshold).astype(int)
    val_metrics = evaluate_model(y_val, val_pred, val_prob)

    test_prob = model.predict_proba(X_test)[:, 1]
    test_pred = (test_prob >= best_threshold).astype(int)
    metrics = evaluate_model(y_test, test_pred, test_prob)

    print(f"Rows used      : {len(df)}")
    print(f"Train rows     : {len(X_train)}")
    print(f"Validation rows: {len(X_val)}")
    print(f"Test rows      : {len(X_test)}")
    print(f"Churn rate     : {y.mean():.2%}")
    print(f"Best threshold : {best_threshold}")

    print("\nValidation metrics:")
    print(f"Accuracy       : {val_metrics['accuracy']}")
    print(f"Precision      : {val_metrics['precision']}")
    print(f"Recall         : {val_metrics['recall']}")
    print(f"F1-score       : {val_metrics['f1']}")
    print(f"ROC-AUC        : {val_metrics['roc_auc']}")

    print("\nTest metrics:")
    print(f"Accuracy       : {metrics['accuracy']}")
    print(f"Precision      : {metrics['precision']}")
    print(f"Recall         : {metrics['recall']}")
    print(f"F1-score       : {metrics['f1']}")
    print(f"ROC-AUC        : {metrics['roc_auc']}")

    print_feature_weights(model)

    if metrics["roc_auc"] < ROC_AUC_THRESHOLD:
        raise SystemExit(f"ROC-AUC is below threshold: {metrics['roc_auc']}")

    if metrics["recall"] < RECALL_THRESHOLD:
        raise SystemExit(f"Recall is below threshold: {metrics['recall']}")

    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "threshold": best_threshold,
            "metrics": metrics,
            "accuracy": metrics["accuracy"],
        },
        MODEL_PATH,
    )

    print(f"\nSaved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()