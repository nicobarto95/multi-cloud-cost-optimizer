# S3 bucket for storing cost reports
resource "aws_s3_bucket" "cost_data" {
  bucket = "${var.s3_bucket_prefix}-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "Cost Optimizer Data Bucket"
  }
}

# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "cost_data" {
  bucket = aws_s3_bucket.cost_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "cost_data" {
  bucket = aws_s3_bucket.cost_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "cost_data" {
  bucket = aws_s3_bucket.cost_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy to transition old reports to cheaper storage
resource "aws_s3_bucket_lifecycle_configuration" "cost_data" {
  bucket = aws_s3_bucket.cost_data.id

  rule {
    id     = "transition-old-reports"
    status = "Enabled"

    filter {
     prefix = "reports/"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 365
    }
  }
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}
