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

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "customer-churn-eks"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.36"
}

variable "vpc_cidr" {
  description = "CIDR block for the project VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "node_instance_type" {
  description = "EC2 instance type for the EKS worker nodes"
  type        = string
  default     = "t3.small"
}

variable "node_group_min_size" {
  description = "Minimum number of EKS worker nodes"
  type        = number
  default     = 1
}

variable "node_group_desired_size" {
  description = "Desired number of EKS worker nodes"
  type        = number
  default     = 2
}

variable "node_group_max_size" {
  description = "Maximum number of EKS worker nodes"
  type        = number
  default     = 3
}
