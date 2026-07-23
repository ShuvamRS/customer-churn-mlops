output "model_bucket_name" {
  description = "S3 bucket name used for storing model.joblib"
  value       = aws_s3_bucket.model_bucket.bucket
}

output "ecr_repository_url" {
  description = "URL of the ECR repository used for the Docker image"
  value       = aws_ecr_repository.customer_churn_api.repository_url
}
