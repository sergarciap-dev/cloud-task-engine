terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. DynamoDB Table para metadatos de tareas
resource "aws_dynamodb_table" "tasks_table" {
  name         = "TasksTable-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "taskId"

  attribute {
    name = "taskId"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = "cloud-task-engine"
  }
}

# 2. S3 Bucket para almacenamiento de reportes
resource "aws_s3_bucket" "reports_bucket" {
  bucket_prefix = "task-engine-reports-${var.environment}-"
  force_destroy = true

  tags = {
    Environment = var.environment
    Project     = "cloud-task-engine"
  }
}

# Bloqueo de acceso público S3
resource "aws_s3_bucket_public_access_block" "reports_bucket_block" {
  bucket = aws_s3_bucket.reports_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 3. SQS Queue para procesamiento asíncrono
resource "aws_sqs_queue" "tasks_queue" {
  name                      = "tasks-processing-queue-${var.environment}"
  message_retention_seconds = 86400
  visibility_timeout_seconds = 60

  tags = {
    Environment = var.environment
    Project     = "cloud-task-engine"
  }
}