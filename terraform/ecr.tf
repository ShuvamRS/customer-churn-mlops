resource "aws_ecr_repository" "customer_churn_api" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = "customer-churn-mlops"
  }
}
