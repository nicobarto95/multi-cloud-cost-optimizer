variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "nicola-bartolini"
}

variable "lambda_runtime" {
  description = "Python runtime version for Lambda"
  type        = string
  default     = "python3.11"
}

variable "lambda_memory" {
  description = "Memory allocation for Lambda function (MB)"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (seconds)"
  type        = number
  default     = 300
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for Lambda invocation"
  type        = string
  default     = "cron(0 2 * * ? *)" # Every day at 2 AM UTC
}

variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket name"
  type        = string
  default     = "cost-optimizer"
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logs for Lambda"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch logs retention period (days)"
  type        = number
  default     = 7
}
