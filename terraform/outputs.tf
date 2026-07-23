output "model_bucket_name" {
  description = "S3 bucket name used for storing model.joblib"
  value       = aws_s3_bucket.model_bucket.bucket
}
