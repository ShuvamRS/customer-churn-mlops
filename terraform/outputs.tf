output "model_bucket_name" {
  description = "S3 bucket name used for storing model.joblib"
  value       = aws_s3_bucket.model_bucket.bucket
}

output "ecr_repository_url" {
  description = "URL of the ECR repository used for the Docker image"
  value       = aws_ecr_repository.customer_churn_api.repository_url
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "eks_update_kubeconfig_command" {
  description = "Command to configure kubectl for this EKS cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}