# main.tf — Arquitetura Arkhe Base
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    snowflake = { source = "Snowflake-Labs/snowflake", version = "~> 0.86" }
  }
  backend "s3" {
    bucket = "arkhe-terraform-state"
    key    = "data-platform/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

# Variáveis de Coerência
variable "lambda_target" {
  default = 0.95
  description = "Meta de coerência para pipelines críticos"
}

# Kinesis Stream com monitoramento de λ₂
resource "aws_kinesis_stream" "arkhe_stream" {
  name             = "arkhe-data-stream"
  shard_count      = 10

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    ArkheLambdaTarget = var.lambda_target
    Environment       = "production"
  }
}

# Snowflake Warehouse com auto-suspend otimizado
resource "snowflake_warehouse" "arkhe_wh" {
  name           = "ARKHE_COMPUTE_WH"
  warehouse_size = "X-LARGE"

  auto_suspend = 300  # 5 minutos (balance entre custo e latência)
  auto_resume  = true
}

# Resource Monitor (Circuit Breaker de custo)
resource "snowflake_resource_monitor" "arkhe_rm" {
  name         = "ARKHE_COHERENCE_RM"
  credit_quota = 1000  # Daily limit

  frequency       = "DAILY"
  start_timestamp = "2026-04-08 00:00:00"

  notify_triggers   = [75, 90]
  suspend_trigger   = 100  # Circuit breaker imediato
}

# Lambda Function: Controlador SBM
resource "aws_lambda_function" "sbm_controller" {
  filename         = "sbm_controller.zip"
  function_name    = "arkhe-sbm-controller"
  role             = "arn:aws:iam::123456789012:role/lambda-role"
  handler          = "controller.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      LAMBDA_TARGET       = var.lambda_target
      HYSTERESIS          = "0.02"
    }
  }
}

# CloudWatch Alarm para λ₂ crítico
resource "aws_cloudwatch_metric_alarm" "coherence_critical" {
  alarm_name          = "arkhe-coherence-critical"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Lambda2DataCoherence"
  namespace           = "Arkhe/DataPlatform"
  period              = "60"
  statistic           = "Average"
  threshold           = 0.90
  alarm_description   = "Coerência do pipeline abaixo do limiar crítico"
}
