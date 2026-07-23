variable "aws_region" {
  description = "AWS region for project resources"
  type        = string
  default     = "us-west-1"
}

variable "model_bucket_name" {
  description = "S3 bucket used to store the trained model artifact"
  type        = string
  default     = "customer-churn-mlops-models-shuvamrs"
}
