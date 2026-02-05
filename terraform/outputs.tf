output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.cost_ingestion.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.cost_ingestion.arn
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for cost data"
  value       = aws_s3_bucket.cost_data.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.cost_data.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_cost_ingestion.arn
}

output "schedule_expression" {
  description = "EventBridge schedule expression"
  value       = var.schedule_expression
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.lambda_logs[0].name : "disabled"
}

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}
