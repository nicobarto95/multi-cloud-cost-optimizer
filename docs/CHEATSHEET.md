# ⚡ Quick Reference Cheatsheet

## 🚀 Setup Iniziale (Una volta sola)

```bash
# 1. Clone/Download del progetto
cd /path/to/your/projects
# [scarica la cartella multi-cloud-cost-optimizer]

# 2. Configura AWS CLI
aws configure
# Inserisci: Access Key, Secret Key, Region (eu-west-1), Format (json)

# 3. Abilita Cost Explorer su AWS Console
# AWS Console → Billing → Cost Explorer → Enable
# ⚠️ Attendi 24 ore prima di deployare!

# 4. Configura Terraform
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Cambia 'owner' con il tuo nome

# 5. Initialize Terraform
terraform init
```

---

## 📦 Deploy & Update

```bash
# Preview modifiche
terraform plan

# Deploy infrastructure
terraform apply
# Type: yes

# Vedere output
terraform output

# Get bucket name
terraform output -raw s3_bucket_name
```

---

## 🧪 Test & Debug

```bash
# Invoke Lambda manualmente
aws lambda invoke \
  --function-name cost-ingestion-dev \
  --payload '{}' \
  response.json && cat response.json | jq .

# Vedere logs in real-time
aws logs tail /aws/lambda/cost-ingestion-dev --follow

# Verificare S3 bucket
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/reports/latest/

# Scaricare ultimo report
aws s3 cp s3://$(terraform output -raw s3_bucket_name)/reports/latest/cost-report.json ./report.json
cat report.json | jq '.summary'
```

---

## 🛠️ Makefile Commands

```bash
# Show all commands
make help

# Common workflows
make init       # Initialize Terraform
make plan       # Preview changes
make apply      # Deploy
make test       # Run Python tests
make logs       # View Lambda logs
make invoke     # Manual Lambda invoke
make clean      # Clean temp files
make destroy    # ⚠️ Delete everything

# Useful utilities
make check-bucket        # Check S3 contents
make download-latest     # Download latest report
make status              # Show deployment status
make cost-estimate       # Show monthly cost
```

---

## 📊 CloudWatch Queries

```bash
# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=cost-ingestion-dev \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum

# Query logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/cost-ingestion-dev \
  --filter-pattern "ERROR" \
  --max-items 10
```

---

## 🗂️ S3 Structure

```
s3://cost-optimizer-dev-123456789012/
├── reports/
│   ├── year=2025/month=02/day=04/cost-report-2025-02-04.json
│   └── latest/cost-report.json
└── summaries/
    └── year=2025/month=02/monthly-summary-2025-02.json
```

```bash
# List all reports
aws s3 ls s3://YOUR_BUCKET/reports/ --recursive

# Download specific date
aws s3 cp s3://YOUR_BUCKET/reports/year=2025/month=02/day=04/cost-report-2025-02-04.json ./
```

---

## 🔧 Common Modifications

### Change schedule (ogni 6 ore invece di daily)
```hcl
# In terraform.tfvars
schedule_expression = "rate(6 hours)"
```

### Increase Lambda timeout
```hcl
# In terraform.tfvars
lambda_timeout = 600  # 10 minutes
```

### Change log retention
```hcl
# In terraform.tfvars
log_retention_days = 30
```

### Deploy in different region
```hcl
# In terraform.tfvars
aws_region = "us-east-1"
```

---

## 🆘 Troubleshooting Quick Fixes

### "Cost Explorer not enabled"
```bash
# 1. Go to AWS Console → Billing → Cost Explorer
# 2. Click "Enable Cost Explorer"
# 3. Wait 24 hours
```

### "Access Denied" errors
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions
# User needs: Lambda, S3, IAM, EventBridge, CloudWatch permissions
```

### Lambda timeout
```hcl
# Increase timeout in terraform.tfvars
lambda_timeout = 600
```

```bash
terraform apply
```

### No data in S3
```bash
# 1. Check logs
make logs

# 2. Manually invoke
make invoke

# 3. Check EventBridge rule
aws events describe-rule --name cost-ingestion-schedule-dev
```

### Terraform state locked
```bash
# If using local state
rm -f terraform/.terraform.tfstate.lock.info

# If using remote state (S3)
terraform force-unlock LOCK_ID
```

---

## 🧹 Cleanup

```bash
# Delete everything
cd terraform
terraform destroy
# Type: yes

# Verify deletion
aws lambda list-functions | grep cost-ingestion
aws s3 ls | grep cost-optimizer
```

---

## 📝 Git Workflow

```bash
# Initial commit
git init
git add .
git commit -m "feat: initial commit - Lambda cost ingestion"

# Create GitHub repo, then:
git remote add origin https://github.com/YOUR_USERNAME/multi-cloud-cost-optimizer.git
git branch -M main
git push -u origin main

# Create issues
# Go to GitHub → Issues → New Issue
# Create 3 issues: OPA Policies, CI/CD, Grafana Dashboard

# Feature branch workflow
git checkout -b feature/opa-policies
# [make changes]
git add .
git commit -m "feat: add OPA tagging policies"
git push origin feature/opa-policies
# Create Pull Request on GitHub
```

---

## 📊 Useful AWS CLI Commands

```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[].FunctionName'

# Get Lambda configuration
aws lambda get-function --function-name cost-ingestion-dev

# List S3 buckets
aws s3 ls

# S3 bucket size
aws s3 ls s3://YOUR_BUCKET --recursive --summarize --human-readable

# CloudWatch log groups
aws logs describe-log-groups --query 'logGroups[].logGroupName'

# EventBridge rules
aws events list-rules

# Cost Explorer query (last 7 days)
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "UnblendedCost"
```

---

## 🎯 Daily Workflow

### Morning check (vedere risultati notturni):
```bash
make logs              # Check execution logs
make download-latest   # Get latest report
cat latest-report.json | jq '.summary'
```

### Dopo modifiche al codice:
```bash
make test              # Run tests
make apply             # Deploy changes
make invoke            # Test manually
```

### Review settimanale:
```bash
# Download all reports from last week
aws s3 sync s3://YOUR_BUCKET/reports/year=2025/month=02/ ./reports/

# Analyze with jq
cat reports/*/cost-report-*.json | jq '.summary'
```

---

## 📈 Metrics to Track

```bash
# Total cost trend
cat latest-report.json | jq '.summary.total_cost'

# Idle resources count
cat latest-report.json | jq '.summary.idle_resources_count'

# Potential savings
cat latest-report.json | jq '.summary.potential_savings'

# Top 5 services by cost
cat latest-report.json | jq '.service_breakdown.top_5_services'

# Recommendations
cat latest-report.json | jq '.recommendations[] | {priority, title, impact}'
```

---

## 🔗 Useful Links

- [AWS Cost Explorer Docs](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [jq Manual](https://stedolan.github.io/jq/manual/)

---

## ⚡ One-Liner Helpers

```bash
# Get Lambda ARN
terraform output -raw lambda_function_arn

# Get bucket name
terraform output -raw s3_bucket_name

# Quick invoke
aws lambda invoke --function-name $(terraform output -raw lambda_function_name) --payload '{}' /tmp/out.json && cat /tmp/out.json | jq .

# Latest cost
aws s3 cp s3://$(terraform output -raw s3_bucket_name)/reports/latest/cost-report.json - | jq '.summary.total_cost'

# Count idle resources
aws s3 cp s3://$(terraform output -raw s3_bucket_name)/reports/latest/cost-report.json - | jq '.summary.idle_resources_count'

# Check if Lambda is running
aws lambda get-function --function-name $(terraform output -raw lambda_function_name) --query 'Configuration.State'
```

---

## 💡 Pro Tips

1. **Alias utili da aggiungere a .bashrc/.zshrc**:
```bash
alias tf='terraform'
alias tfa='terraform apply'
alias tfp='terraform plan'
alias tfo='terraform output'
alias awsl='aws lambda'
alias awss='aws s3'
```

2. **jq filters per report analysis**:
```bash
# Services over $50/month
jq '.service_breakdown.services | to_entries | map(select(.value > 50))' report.json

# High priority recommendations
jq '.recommendations[] | select(.priority == "HIGH")' report.json

# Stopped EC2 instances
jq '.idle_resources.ec2_stopped[].id' report.json
```

3. **Watch mode per logs**:
```bash
watch -n 5 'aws s3 ls s3://$(terraform output -raw s3_bucket_name)/reports/latest/'
```

---

**Salva questo file per reference rapido! 📌**
