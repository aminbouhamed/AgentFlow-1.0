#the terraform config for aws deployment
# basic setup (customizable)

terraform {
    required_version = ">=1.0"
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
}

provider "aws" {
    region = var.AWS_REGION
}

#Variables

variable "AWS_REGION" {
    description = "AWS region"
    default     = "eu-central-1"
}

variable "app_name" {
  description = "Application name"
  default     = "agentflow"
}
variable "environment" {
  description = "Environment (dev/staging/prod)"
  default     = "prod"
}
# ECR Repository for Docker images
resource "aws_ecr_repository" "agentflow" {
  name                 = "${var.app_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = var.app_name
    Environment = var.environment
  } 
}
#ECS Cluster
resource "aws_ecs_cluster" "main"{
    name = "${var.app_name}-cluster-${var.environment}"

    setting {
        name  = "containerInsights"
        value = "enabled"
    }

    tags = {
        Name        = var.app_name
        Environment = var.environment
    }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.app_name}-ecs-task-execution-role"
 assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
# IAM Role for ECS Task (with Bedrock permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_policy" {
  name = "${var.app_name}-bedrock-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# Outputs
output "ecr_repository_url" {
  value = aws_ecr_repository.agentflow.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}