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

variable "ecr_repository_name" {
  description = "Name of the ECR repository used to store the Docker image"
  type        = string
  default     = "customer-churn-mlops"
}
