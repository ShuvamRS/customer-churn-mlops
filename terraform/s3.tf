provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "model_bucket" {
  bucket = var.model_bucket_name

  tags = {
    Name    = var.model_bucket_name
    Project = "customer-churn-mlops"
  }
}
