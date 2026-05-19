terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket  = "cloudtasks-tfstate"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.region
}

# ───────────────────────────────────────────
# Data sources
# ───────────────────────────────────────────

data "aws_caller_identity" "current" {}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# ───────────────────────────────────────────
# VPC
# ───────────────────────────────────────────

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  public_subnets  = var.public_subnet_cidrs
  private_subnets = var.private_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# EKS
# ───────────────────────────────────────────

data "aws_eks_cluster_versions" "latest" {}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.eks_cluster_name
  cluster_version = data.aws_eks_cluster_versions.latest.cluster_versions[1].cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    default = {
      instance_types = [var.eks_node_instance_type]
      desired_size   = var.eks_desired_nodes
      min_size       = 1
      max_size       = 5
    }
  }

  access_entries = {
    solomon = {
      principal_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_601b9dcf2f404545"
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# KMS Key for RDS encryption at rest
# ───────────────────────────────────────────

resource "aws_kms_key" "rds_key" {
  description             = "${var.project_name} RDS encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAccountRoot"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowRDSMonitoringRole"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.rds_monitoring_role.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_kms_alias" "rds_key_alias" {
  name          = "alias/${var.project_name}-rds"
  target_key_id = aws_kms_key.rds_key.key_id
}

# ───────────────────────────────────────────
# IAM Role for RDS Enhanced Monitoring
# ───────────────────────────────────────────

resource "aws_iam_role" "rds_monitoring_role" {
  name = "${var.project_name}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring_policy" {
  role       = aws_iam_role.rds_monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_iam_role_policy" "rds_least_privilege" {
  name = "${var.project_name}-rds-least-privilege"
  role = aws_iam_role.rds_monitoring_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/rds/*"
      },
      {
        Sid    = "AllowKMSForEncryption"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.rds_key.arn
      }
    ]
  })
}

# ───────────────────────────────────────────
# VPC Endpoint Security Group
# ───────────────────────────────────────────

resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "${var.project_name}-vpc-endpoint-sg"
  description = "Allow HTTPS from RDS security group only"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_security_group_ingress_rule" "vpc_endpoint_ingress_rds" {
  description                  = "HTTPS from RDS only"
  security_group_id            = aws_security_group.vpc_endpoint_sg.id
  referenced_security_group_id = aws_security_group.rds_sg.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

# ───────────────────────────────────────────
# RDS Security Group
# ───────────────────────────────────────────

resource "aws_security_group" "rds_sg" {
  name        = "${var.project_name}-rds-sg"
  description = "Allow PostgreSQL access from EKS nodes and bastion"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_ingress_eks" {
  security_group_id            = aws_security_group.rds_sg.id
  referenced_security_group_id = module.eks.node_security_group_id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "rds_ingress_bastion" {
  description                  = "Allow PostgreSQL from bastion"
  security_group_id            = aws_security_group.rds_sg.id
  referenced_security_group_id = aws_security_group.bastion_sg.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "rds_egress_vpc_endpoints" {
  description                  = "Allow HTTPS to VPC endpoints"
  security_group_id            = aws_security_group.rds_sg.id
  referenced_security_group_id = aws_security_group.vpc_endpoint_sg.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "rds_egress_s3" {
  description       = "Allow HTTPS to S3 via VPC endpoint"
  security_group_id = aws_security_group.rds_sg.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# ───────────────────────────────────────────
# RDS Subnet Group
# ───────────────────────────────────────────

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# RDS Instance
# ───────────────────────────────────────────

resource "aws_db_instance" "postgres" {
  identifier        = "${var.project_name}-db"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = var.rds_instance_class
  allocated_storage = 20

  db_name  = var.rds_db_name
  username = var.rds_username
  password = var.rds_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false
  skip_final_snapshot = true
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.rds_key.arn
  monitoring_role_arn = aws_iam_role.rds_monitoring_role.arn
  monitoring_interval = 60

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# VPC Endpoints
# ───────────────────────────────────────────

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = module.vpc.private_route_table_ids

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowRDSMonitoringRoleOnly"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.rds_monitoring_role.arn
        }
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "arn:aws:s3:::*"
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_endpoint" "cloudwatch_logs" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoint_sg.id]
  private_dns_enabled = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowRDSMonitoringRoleOnly"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.rds_monitoring_role.arn
        }
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/rds/*"
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_endpoint" "kms" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoint_sg.id]
  private_dns_enabled = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowRDSMonitoringRoleOnly"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.rds_monitoring_role.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.rds_key.arn
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# SSM VPC Endpoints (bastion access)
# ───────────────────────────────────────────

resource "aws_security_group" "ssm_endpoint_sg" {
  name        = "${var.project_name}-ssm-endpoint-sg"
  description = "Allow HTTPS from bastion only"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssm_endpoint_ingress_bastion" {
  description                  = "HTTPS from bastion only"
  security_group_id            = aws_security_group.ssm_endpoint_sg.id
  referenced_security_group_id = aws_security_group.bastion_sg.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.ssm_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ssmmessages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.ssm_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_endpoint" "ec2messages" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ec2messages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.ssm_endpoint_sg.id]
  private_dns_enabled = true

  tags = {
    Project = var.project_name
  }
}

# ───────────────────────────────────────────
# Bastion Host (SSM only, no SSH)
# ───────────────────────────────────────────

resource "aws_security_group" "bastion_sg" {
  name        = "${var.project_name}-bastion-sg"
  description = "No inbound ports - SSM access only"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Project = var.project_name
  }
}

resource "aws_vpc_security_group_egress_rule" "bastion_egress_rds" {
  description                  = "Allow PostgreSQL to RDS only"
  security_group_id            = aws_security_group.bastion_sg.id
  referenced_security_group_id = aws_security_group.rds_sg.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "bastion_egress_ssm" {
  description                  = "Allow HTTPS to SSM VPC endpoints only"
  security_group_id            = aws_security_group.bastion_sg.id
  referenced_security_group_id = aws_security_group.ssm_endpoint_sg.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_iam_role" "bastion_role" {
  name = "${var.project_name}-bastion-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  role       = aws_iam_role.bastion_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion_profile" {
  name = "${var.project_name}-bastion-profile"
  role = aws_iam_role.bastion_role.name
}

resource "aws_instance" "bastion" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  subnet_id                   = module.vpc.private_subnets[0]
  vpc_security_group_ids      = [aws_security_group.bastion_sg.id]
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.bastion_profile.name

  tags = {
    Name    = "${var.project_name}-bastion"
    Project = var.project_name
  }
}
