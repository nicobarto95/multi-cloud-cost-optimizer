# Setup Guide

Complete setup instructions for the Multi-Cloud Cost Optimizer.

## Prerequisites

### Required Tools
- **AWS CLI** (v2.x): [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** (>= 1.5.0): [Install Guide](https://developer.hashicorp.com/terraform/downloads)
- **Python** (3.11+): [Download](https://www.python.org/downloads/)
- **Git**: For version control

### AWS Account Requirements
- AWS account with appropriate permissions
- **Cost Explorer enabled** (may take 24 hours after first activation)
- IAM permissions to create:
  - Lambda functions
  - S3 buckets
  - IAM roles and policies
  - EventBridge rules
  - CloudWatch logs and alarms

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-cloud-cost-optimizer.git
cd multi-cloud-cost-optimizer
```

### 2. Configure AWS CLI

Ensure your AWS CLI is configured with credentials:

```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `eu-west-1`)
- Output format (e.g., `json`)

Verify configuration:

```bash
aws sts get-caller-identity
```

### 3. Enable AWS Cost Explorer

**Important**: Cost Explorer must be enabled before deploying.

1. Go to AWS Console → Billing → Cost Explorer
2. Click "Enable Cost Explorer"
3. Wait 24 hours for data to populate

Verify with AWS CLI:

```bash
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

### 4. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region  = "eu-west-1"          # Your AWS region
environment = "dev"                 # dev, staging, or prod
owner       = "your-name"          # Your name or team

# Adjust if needed
lambda_memory  = 256               # MB
lambda_timeout = 300               # seconds
```

### 5. Initialize Terraform

```bash
terraform init
```

This will:
- Download required providers (AWS, Archive)
- Initialize backend
- Create `.terraform` directory

### 6. Plan Infrastructure

Review what will be created:

```bash
terraform plan
```

Expected resources:
- 1 Lambda function
- 1 S3 bucket
- 1 IAM role with 6 policies
- 1 EventBridge rule
- 1 CloudWatch log group
- 1 CloudWatch alarm

### 7. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

Deployment takes ~2 minutes.

### 8. Verify Deployment

Check Lambda function:

```bash
aws lambda get-function \
  --function-name cost-ingestion-dev
```

Check S3 bucket:

```bash
aws s3 ls | grep cost-optimizer
```

### 9. Test Lambda Function

Invoke manually for testing:

```bash
aws lambda invoke \
  --function-name cost-ingestion-dev \
  --payload '{}' \
  response.json

cat response.json
```

Check S3 for generated report:

```bash
aws s3 ls s3://cost-optimizer-dev-YOUR_ACCOUNT_ID/reports/latest/
```

### 10. Monitor Execution

View Lambda logs:

```bash
aws logs tail /aws/lambda/cost-ingestion-dev --follow
```

Check CloudWatch metrics:
- Go to AWS Console → CloudWatch → Metrics → CostOptimizer

## Local Development

### Testing Lambda Locally

```bash
cd lambda/cost_ingestion

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export COST_DATA_BUCKET="your-bucket-name"
export ENVIRONMENT="dev"

# Run tests (if you add them)
python -m pytest tests/
```

### Updating Lambda Code

After making changes:

```bash
cd terraform
terraform apply
```

Terraform will detect code changes and redeploy the Lambda.

## Troubleshooting

### Issue: "Cost Explorer API is not enabled"

**Solution**: 
1. Enable Cost Explorer in AWS Console
2. Wait 24 hours for data
3. Retry deployment

### Issue: "Access Denied" errors

**Solution**:
1. Check IAM permissions
2. Ensure AWS CLI credentials are correct
3. Verify Cost Explorer API access

### Issue: Lambda times out

**Solution**:
Increase timeout in `terraform/variables.tf`:

```hcl
variable "lambda_timeout" {
  default     = 600  # Increase to 10 minutes
}
```

Then `terraform apply`.

### Issue: No data in S3

**Solution**:
1. Check Lambda logs for errors
2. Verify EventBridge rule is enabled
3. Manually invoke Lambda to test

## Cost Estimation

### Monthly AWS Costs

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30 executions/month, 256MB, 60s avg | $0.00 (free tier) |
| S3 Standard | < 1GB storage | $0.02 |
| S3 Requests | ~100 PUT/GET per month | $0.01 |
| CloudWatch Logs | 1GB/month | $0.50 |
| Cost Explorer API | 30 requests/month | $0.30 |
| **Total** | | **~$0.83/month** |

### Cost Optimization Tips

1. **Reduce log retention**: Set to 3 days instead of 7
2. **Use S3 Lifecycle**: Archive old reports to Glacier (already configured)
3. **Optimize Lambda memory**: Test with 128MB if data volume is small

## Next Steps

1. ✅ Deploy infrastructure
2. ⏳ Wait for first automated run (next 2 AM UTC)
3. 📊 Set up Grafana dashboard (see docs/GRAFANA_SETUP.md)
4. 🔒 Implement OPA policies (see policies/README.md)
5. 🚀 Set up CI/CD pipeline (see .github/workflows/README.md)

## Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review CloudWatch logs
3. Open a GitHub issue with logs attached

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning**: This will delete:
- Lambda function
- S3 bucket (and all data)
- IAM roles
- CloudWatch logs
- EventBridge rules

Type `yes` to confirm.
