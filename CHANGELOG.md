# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- OPA policy enforcement for resource tagging
- Grafana dashboard for cost visualization
- GitHub Actions CI/CD pipeline
- Multi-account AWS Organizations support
- GCP cost integration
- Slack notifications for cost anomalies

## [0.2.0] - 2025-02-04

### Added
- Complete Lambda ingestion function
- Cost Explorer API integration
- Resource scanner for idle resources (EC2, EBS, EIP, RDS, ELB)
- S3 data storage with date partitioning
- CloudWatch metrics and alarms
- Comprehensive documentation (SETUP.md, ARCHITECTURE.md)
- Unit tests for core modules
- Makefile for common operations
- Example cost report output

### Infrastructure
- Terraform modules for full deployment
- IAM roles with least privilege
- S3 bucket with encryption and lifecycle policies
- EventBridge scheduler for daily execution
- CloudWatch log groups with retention

### Documentation
- Architecture documentation
- Setup guide
- Contributing guidelines
- Sample outputs

## [0.1.0] - 2025-02-01

### Added
- Initial project structure
- README with project overview
- Basic Terraform configuration
- Lambda function skeleton

---

## Version History

### [0.2.0] - Current Version
**Focus**: Complete Lambda ingestion implementation

**Key Features**:
- ✅ AWS Cost Explorer integration
- ✅ Idle resource detection
- ✅ Daily automated execution
- ✅ S3 report storage
- ✅ CloudWatch monitoring

**What's Missing**:
- ⏳ OPA policies
- ⏳ Grafana dashboards
- ⏳ CI/CD pipeline
- ⏳ Multi-cloud support

**Next Steps**: Issue #1 (OPA Policies) or Issue #4 (Grafana Dashboard)

---

## Migration Guide

### From 0.1.0 to 0.2.0

No breaking changes. Fresh deployment recommended:

```bash
# Backup old state (if exists)
cd terraform
terraform state pull > backup-state.json

# Deploy new version
terraform init -upgrade
terraform plan
terraform apply
```

---

## Contributors

- Nicola Bartolini - Initial development

---

## Links

- [GitHub Repository](https://github.com/yourusername/multi-cloud-cost-optimizer)
- [Issue Tracker](https://github.com/yourusername/multi-cloud-cost-optimizer/issues)
- [Documentation](./docs/)
