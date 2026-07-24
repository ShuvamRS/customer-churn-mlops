# Customer Churn MLOps Pipeline

This project implements an end-to-end MLOps pipeline for a scikit-learn customer churn model on AWS.

A key design choice is that the trained model is stored separately from the Docker image. Jenkins trains the model and uploads `model.joblib` to S3. The Docker image contains only the FastAPI serving code. When the container starts on EKS, the app downloads the model from S3 and serves predictions.

## Architecture

```text
GitHub push
    ↓
GitHub webhook
    ↓
Jenkins pipeline
    ↓
Train model and upload model.joblib to S3
    ↓
Run tests
    ↓
Build serving-only FastAPI Docker image
    ↓
Push image to Amazon ECR
    ↓
Deploy image to Amazon EKS
    ↓
EKS pod downloads model.joblib from S3
    ↓
LoadBalancer exposes /health and /predict
```

## Tech Stack

| Area | Tools |
|---|---|
| Machine learning | Python, pandas, scikit-learn |
| API serving | FastAPI, Uvicorn |
| Testing | pytest |
| Model artifact storage | Amazon S3 |
| Containerization | Docker |
| Image registry | Amazon ECR |
| Infrastructure | Terraform |
| Orchestration | Kubernetes, Amazon EKS |
| CI/CD | Jenkins, GitHub webhook |

## What This Project Builds

### 1. Model training and S3 artifact storage

`train.py` trains the churn model, evaluates it, applies quality checks, saves the trained model as `model.joblib`, and uploads that artifact to S3.

```text
train.py → model.joblib → Amazon S3
```

<p align="center">
  <img src="screenshots/09_s3_model_joblib_uploaded.png" alt="S3 bucket containing model.joblib" width="850">
</p>

This keeps the model artifact separate from the application image.

### 2. FastAPI prediction service

`app.py` is the API service. At startup, it reads the S3 configuration from environment variables, downloads `model.joblib`, loads the model, and exposes:

```text
GET  /health
POST /predict
```

Example `/health` response:

```json
{
  "status": "ok",
  "model_metrics": {
    "accuracy": 0.7672,
    "precision": 0.5479,
    "recall": 0.7032,
    "f1": 0.6159,
    "roc_auc": 0.8426
  }
}
```

Example `/predict` response:

```json
{
  "churn": true,
  "churn_probability": 0.8121,
  "threshold": 0.61
}
```

### 3. Serving-only Docker image

The Docker image is intentionally focused on serving the API.

It contains:

```text
app.py
requirements.txt
installed Python dependencies
```

It does not contain:

```text
training dataset
train.py
model.joblib
```

This separates model training from model serving. Jenkins trains the model first, uploads the model to S3, and then builds the API image.

### 4. Amazon ECR image registry

Jenkins pushes the Docker image to Amazon ECR with two tags:

```text
latest
<JENKINS_BUILD_NUMBER>
```

The numbered tag identifies the Jenkins build that produced the image, while `latest` points to the most recent image.

<p align="center">
  <img src="screenshots/11_ecr_latest_and_build_tags.png" alt="ECR image tags showing latest and Jenkins build number" width="850">
</p>

### 5. Kubernetes deployment on EKS

Terraform creates the EKS cluster, and Kubernetes runs the FastAPI container.

The Kubernetes setup includes:

```text
ConfigMap  → passes S3 bucket, model key, and AWS region to the app
Deployment → runs the FastAPI container
Service    → exposes the API through a LoadBalancer
```

The deployment also includes CPU/memory requests and `/health` probes for readiness and liveness.

<p align="center">
  <img src="screenshots/06_eks_cluster_active.png" alt="Active EKS cluster" width="850">
</p>

### 6. Jenkins CI/CD pipeline

Jenkins automates the full workflow after a GitHub push.

Pipeline stages:

```text
Setup
Train Model and Upload to S3
Run Tests
Build Image
Test Container
Push Image
Deploy to EKS
```

<p align="center">
  <img src="screenshots/10_jenkins_webhook_s3_ecr_eks_pipeline_success.png" alt="Successful Jenkins pipeline" width="850">
</p>

## Key Design Choices

- The trained model is stored in S3 instead of being packaged with the Docker image.
- The Docker image contains only the FastAPI serving application.
- Jenkins trains and tests before building and deploying the image.
- ECR stores both `latest` and build-number image tags.
- Kubernetes uses a ConfigMap for non-secret S3 settings.
- The EKS worker nodes have permission to read the model artifact from S3.
- Terraform creates the AWS infrastructure before Jenkins deploys the application.
