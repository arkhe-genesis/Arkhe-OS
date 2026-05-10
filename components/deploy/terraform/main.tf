# terraform/main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    snowflake = { source = "Snowflake-Labs/snowflake", version = "~> 0.86" }
    random = { source = "hashicorp/random", version = "~> 3.5" }
  }
}

locals {
  environment = var.environment
  common_tags = {
    Project     = "Arkhe-SCA"
    Environment = local.environment
    Lambda2Target = "0.95"
    ManagedBy   = "Terraform"
  }
}

# KMS Key para criptografia em trânsito e repouso
resource "aws_kms_key" "arkhe_key" {
  description             = "Arkhe Data Platform Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = local.common_tags
}

# Kinesis Data Stream (Camada de Fase)
resource "aws_kinesis_stream" "arkhe_stream" {
  name             = "arkhe-events-${local.environment}"
  shard_count      = local.environment == "prod" ? 20 : 4
  retention_period = 24

  stream_mode_details {
    stream_mode = local.environment == "prod" ? "PROVISIONED" : "ON_DEMAND"
  }

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.arkhe_key.arn

  tags = merge(local.common_tags, {
    CoherenceLayer = "Phase-Domain-C"
    ThroughputTarget = "40Hz"
  })
}

# S3 Data Lake (Bronze/Silver/Gold)
resource "aws_s3_bucket" "arkhe_lake" {
  bucket = "arkhe-datalake-${local.environment}-${random_id.bucket_suffix.hex}"
  tags = local.common_tags
}

# IAM Role para Lambda SBM Controller
resource "aws_iam_role" "sbm_lambda_role" {
  name = "arkhe-sbm-controller-${local.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = local.common_tags
}

# Lambda Function: SBM Controller (Stabilized by Memory)
resource "aws_lambda_function" "sbm_controller" {
  filename         = "sbm_controller.zip"
  function_name    = "arkhe-sbm-controller-${local.environment}"
  role             = aws_iam_role.sbm_lambda_role.arn
  handler          = "controller.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      LAMBDA_TARGET         = "0.95"
      HYSTERESIS            = "0.02"
      MEMORY_WINDOW_MINUTES = "5"
      ENVIRONMENT           = local.environment
    }
  }

  tags = local.common_tags
}

# CloudWatch Alarm: λ₂ Crítico (< 0.90)
resource "aws_cloudwatch_metric_alarm" "coherence_critical" {
  alarm_name          = "arkhe-coherence-critical-${local.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Lambda2DataCoherence"
  namespace           = "Arkhe/DataPlatform"
  period              = 60
  statistic           = "Average"
  threshold           = 0.90
  alarm_description   = "Pipeline coherence below critical threshold"

  dimensions = {
    Environment = local.environment
  }

  tags = local.common_tags
}

# Snowflake Warehouse (Camada Z - Estrutura)
resource "snowflake_warehouse" "arkhe_wh" {
  name                = "ARKHE_WH_${upper(local.environment)}"
  warehouse_size      = local.environment == "prod" ? "X-LARGE" : "MEDIUM"
  auto_suspend        = 300
  auto_resume         = true

  tags = {
    Environment = local.environment
    CoherenceLayer = "Structure-Domain-Z"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

variable "environment" {
  default = "dev"
}
