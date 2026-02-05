# IAM role for Lambda function
resource "aws_iam_role" "lambda_cost_ingestion" {
  name = "lambda-cost-ingestion-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Lambda Cost Ingestion Role"
  }
}

# Policy for Cost Explorer API access
resource "aws_iam_role_policy" "cost_explorer_access" {
  name = "cost-explorer-access"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast",
          "ce:GetTags"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for EC2 read access (for resource scanning)
resource "aws_iam_role_policy" "ec2_read_access" {
  name = "ec2-read-access"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "ec2:DescribeAddresses",
          "ec2:DescribeSnapshots"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for RDS read access
resource "aws_iam_role_policy" "rds_read_access" {
  name = "rds-read-access"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for ELB read access
resource "aws_iam_role_policy" "elb_read_access" {
  name = "elb-read-access"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetHealth"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for S3 write access to cost data bucket
resource "aws_iam_role_policy" "s3_write_access" {
  name = "s3-write-access"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.cost_data.arn,
          "${aws_s3_bucket.cost_data.arn}/*"
        ]
      }
    ]
  })
}

# Policy for CloudWatch metrics
resource "aws_iam_role_policy" "cloudwatch_metrics" {
  name = "cloudwatch-metrics"
  role = aws_iam_role.lambda_cost_ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach AWS managed policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_cost_ingestion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
