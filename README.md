# 💰 Multi-Cloud Cost Optimizer

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow?style=flat-square)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=flat-square&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=flat-square&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python&logoColor=white)

> **Automated cloud cost monitoring and optimization platform** that reduces cloud waste by identifying idle resources, enforcing tagging policies, and providing real-time spending insights.

## 🎯 What This Project Demonstrates

- **FinOps Best Practices**: Cost awareness, budget enforcement, waste reduction
- **Infrastructure as Code**: Complete Terraform modules with best practices
- **Serverless Architecture**: AWS Lambda for cost-effective data ingestion
- **Policy as Code**: OPA policies for governance and compliance
- **Observability**: Grafana dashboards for actionable insights
- **CI/CD**: Automated testing and validation with GitHub Actions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Account                             │
│                                                              │
│  ┌──────────────┐         ┌─────────────┐                  │
│  │ EventBridge  │────────▶│   Lambda    │                  │
│  │ (Daily Cron) │         │  Ingestion  │                  │
│  └──────────────┘         └──────┬──────┘                  │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │  Cost Explorer  │                │
│                          │      API        │                │
│                          └────────┬────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │   S3 Bucket     │                │
│                          │  (Cost Data)    │                │
│                          └────────┬────────┘                │
└───────────────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │   Prometheus     │
                          │   Pushgateway    │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Grafana Cloud    │
                          │   Dashboard      │
                          └──────────────────┘
```

## 📁 Project Structure

```
.
├── README.md
├── .gitignore
├── terraform/
│   ├── main.tf                 # Main infrastructure
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Output values
│   ├── providers.tf            # Provider configuration
│   ├── lambda.tf               # Lambda configuration
│   ├── s3.tf                   # S3 bucket for data storage
│   ├── iam.tf                  # IAM roles and policies
│   └── modules/
│       └── cost-lambda/        # Reusable Lambda module
├── lambda/
│   ├── cost_ingestion/
│   │   ├── handler.py          # Lambda entry point
│   │   ├── requirements.txt    # Python dependencies
│   │   └── utils/
│   │       ├── cost_explorer.py
│   │       ├── resource_scanner.py
│   │       └── s3_writer.py
├── policies/
│   ├── tagging.rego            # OPA tagging policies
│   ├── resource-limits.rego    # Resource size policies
│   └── tests/
│       └── tagging_test.rego   # Policy tests
├── dashboards/
│   └── cost-overview.json      # Grafana dashboard
├── .github/
│   └── workflows/
│       └── terraform-ci.yml    # CI/CD pipeline
└── docs/
    ├── SETUP.md                # Setup instructions
    └── ARCHITECTURE.md         # Detailed architecture
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with Cost Explorer enabled
- Terraform >= 1.5
- Python 3.11+
- AWS CLI configured

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-cloud-cost-optimizer.git
cd multi-cloud-cost-optimizer
```

### 2. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 4. Test Lambda Function Locally

```bash
cd lambda/cost_ingestion
pip install -r requirements.txt
python -m pytest tests/
```

## 🔑 Key Features

### ✅ Implemented

- [x] AWS Lambda cost ingestion from Cost Explorer API
- [x] Daily automated data collection via EventBridge
- [x] S3 storage for historical cost data
- [x] Idle resource detection (stopped EC2, unattached EBS)
- [x] IAM roles with least privilege principle

### 🚧 In Progress

- [ ] OPA policy enforcement
- [ ] Grafana dashboard with cost trends
- [ ] GitHub Actions CI/CD pipeline
- [ ] Multi-account support

### 📋 Planned

- [ ] GCP cost integration
- [ ] Slack notifications for cost anomalies
- [ ] Automated resource cleanup (dry-run mode)
- [ ] Cost allocation recommendations

## 📊 Sample Output

**Lambda Ingestion Output (S3):**

```json
{
  "date": "2025-02-04",
  "total_cost": 245.32,
  "services": {
    "EC2": 123.45,
    "RDS": 67.89,
    "S3": 23.98
  },
  "idle_resources": {
    "ec2_stopped": ["i-abc123", "i-def456"],
    "ebs_unattached": ["vol-xyz789"],
    "eip_unassociated": ["eipalloc-123abc"]
  },
  "cost_delta": {
    "vs_yesterday": "+3.2%",
    "vs_last_month": "-12.5%"
  }
}
```

## 🔐 Security

- All secrets managed via AWS Secrets Manager
- IAM roles follow least privilege principle
- S3 bucket encrypted at rest (AES-256)
- Lambda execution logs in CloudWatch
- No hardcoded credentials

## 💡 Cost Breakdown

**Monthly AWS Costs (Estimated):**

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | ~30 invocations/month | $0.00 (free tier) |
| S3 | < 1GB storage | $0.02 |
| CloudWatch Logs | 1GB/month | $0.50 |
| Cost Explorer API | 30 requests/month | $0.30 |
| **Total** | | **~$0.82/month** |

**Grafana Cloud:** Free tier (10k metrics, 14 days retention)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 📬 Contact

Created by [Nicola Bartolini](https://github.com/yourusername)

- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

⭐ **If you find this project useful, please star the repository!**
