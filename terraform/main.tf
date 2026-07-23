data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  project_tags = {
    Project = "customer-churn-mlops"
  }

  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_dns_support   = true
  enable_dns_hostnames = true

  enable_nat_gateway = true
  single_nat_gateway = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = local.project_tags
}

data "aws_iam_policy_document" "s3_model_read" {
  statement {
    sid    = "ListModelBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.model_bucket.arn,
    ]
  }

  statement {
    sid    = "ReadModelObject"
    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.model_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "s3_model_read" {
  name        = "${var.cluster_name}-s3-model-read"
  description = "Allows EKS worker nodes to read model artifacts from the project S3 bucket"
  policy      = data.aws_iam_policy_document.s3_model_read.json

  tags = local.project_tags
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access = true

  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    default = {
      name = "workers"

      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"

      min_size     = var.node_group_min_size
      desired_size = var.node_group_desired_size
      max_size     = var.node_group_max_size

      iam_role_additional_policies = {
        s3_model_read = aws_iam_policy.s3_model_read.arn
      }
    }
  }

  tags = local.project_tags
}
