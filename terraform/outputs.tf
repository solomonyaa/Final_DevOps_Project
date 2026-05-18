# ───────────────────────────────────────────
# VPC Outputs
# ───────────────────────────────────────────

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "private_subnets" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

# ───────────────────────────────────────────
# EKS Outputs
# ───────────────────────────────────────────

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_version" {
  description = "Kubernetes version of the EKS cluster"
  value       = module.eks.cluster_version
}

# ───────────────────────────────────────────
# RDS Outputs
# ───────────────────────────────────────────

output "rds_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_db_name" {
  description = "Name of the PostgreSQL database"
  value       = aws_db_instance.postgres.db_name
}

# ───────────────────────────────────────────
# Security Hardening Outputs
# ───────────────────────────────────────────

output "rds_kms_key_arn" {
  description = "ARN of the KMS key used for RDS encryption"
  value       = aws_kms_key.rds_key.arn
}

output "rds_monitoring_role_arn" {
  description = "ARN of the IAM role used for RDS enhanced monitoring"
  value       = aws_iam_role.rds_monitoring_role.arn
}

output "vpc_endpoint_s3_id" {
  description = "ID of the S3 VPC endpoint"
  value       = aws_vpc_endpoint.s3.id
}

output "vpc_endpoint_cloudwatch_id" {
  description = "ID of the CloudWatch Logs VPC endpoint"
  value       = aws_vpc_endpoint.cloudwatch_logs.id
}

output "vpc_endpoint_kms_id" {
  description = "ID of the KMS VPC endpoint"
  value       = aws_vpc_endpoint.kms.id
}

output "bastion_public_ip" {
  description = "Public IP of the bastion host"
  value       = aws_instance.bastion.public_ip
}
