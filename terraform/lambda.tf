# Package Lambda function code
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/cost_ingestion"
  output_path = "${path.module}/lambda_function.zip"
  excludes    = ["__pycache__", "*.pyc", "tests"]
}

# Lambda function
resource "aws_lambda_function" "cost_ingestion" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "cost-ingestion-${var.environment}"
  role            = aws_iam_role.lambda_cost_ingestion.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      COST_DATA_BUCKET = aws_s3_bucket.cost_data.id
      ENVIRONMENT      = var.environment
      LOG_LEVEL        = "INFO"
    }
  }

  tags = {
    Name = "Cost Ingestion Lambda"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/aws/lambda/${aws_lambda_function.cost_ingestion.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "Cost Ingestion Lambda Logs"
  }
}

# EventBridge rule for scheduled execution
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "cost-ingestion-schedule-${var.environment}"
  description         = "Trigger cost ingestion Lambda daily"
  schedule_expression = var.schedule_expression

  tags = {
    Name = "Cost Ingestion Schedule"
  }
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "cost-ingestion-lambda"
  arn       = aws_lambda_function.cost_ingestion.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}

# CloudWatch alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "cost-ingestion-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when Lambda function errors occur"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.cost_ingestion.function_name
  }

  tags = {
    Name = "Cost Ingestion Error Alarm"
  }
}
