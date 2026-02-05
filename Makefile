.PHONY: help init plan apply destroy test clean logs invoke

# Variables
FUNCTION_NAME := cost-ingestion-dev
AWS_REGION := eu-west-1

help: ## Show this help message
	@echo "Multi-Cloud Cost Optimizer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	cd terraform && terraform init

plan: ## Run Terraform plan
	@echo "Planning infrastructure changes..."
	cd terraform && terraform plan

apply: ## Apply Terraform changes
	@echo "Applying infrastructure changes..."
	cd terraform && terraform apply

destroy: ## Destroy all infrastructure
	@echo "Destroying infrastructure..."
	cd terraform && terraform destroy

test: ## Run Python tests
	@echo "Running tests..."
	cd lambda/cost_ingestion && python -m pytest tests/ -v

clean: ## Clean temporary files
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf terraform/.terraform 2>/dev/null || true
	rm -f terraform/lambda_function.zip 2>/dev/null || true
	rm -f terraform/*.tfstate* 2>/dev/null || true
	@echo "Cleanup complete"

logs: ## View Lambda logs
	@echo "Fetching Lambda logs..."
	aws logs tail /aws/lambda/$(FUNCTION_NAME) --follow --region $(AWS_REGION)

invoke: ## Manually invoke Lambda function
	@echo "Invoking Lambda function..."
	aws lambda invoke \
		--function-name $(FUNCTION_NAME) \
		--region $(AWS_REGION) \
		--payload '{}' \
		response.json
	@echo "\nResponse:"
	@cat response.json | jq .
	@rm -f response.json

validate: ## Validate Terraform configuration
	@echo "Validating Terraform configuration..."
	cd terraform && terraform validate

fmt: ## Format Terraform files
	@echo "Formatting Terraform files..."
	cd terraform && terraform fmt -recursive

package: ## Package Lambda function
	@echo "Packaging Lambda function..."
	cd lambda/cost_ingestion && \
	zip -r ../../terraform/lambda_function.zip . \
		-x "tests/*" \
		-x "__pycache__/*" \
		-x "*.pyc"
	@echo "Package created: terraform/lambda_function.zip"

install-deps: ## Install Python dependencies
	@echo "Installing Python dependencies..."
	cd lambda/cost_ingestion && pip install -r requirements.txt

check-bucket: ## Check S3 bucket contents
	@echo "Checking S3 bucket contents..."
	@BUCKET=$$(cd terraform && terraform output -raw s3_bucket_name 2>/dev/null || echo "bucket-not-deployed"); \
	echo "Bucket: $$BUCKET"; \
	aws s3 ls s3://$$BUCKET/reports/latest/ --region $(AWS_REGION)

download-latest: ## Download latest cost report
	@echo "Downloading latest cost report..."
	@BUCKET=$$(cd terraform && terraform output -raw s3_bucket_name 2>/dev/null || echo "bucket-not-deployed"); \
	aws s3 cp s3://$$BUCKET/reports/latest/cost-report.json ./latest-report.json --region $(AWS_REGION)
	@echo "Report downloaded to: latest-report.json"
	@cat latest-report.json | jq '.summary'

setup: init ## Complete initial setup
	@echo "Running complete setup..."
	@echo "1. Copying example variables..."
	@cp terraform/terraform.tfvars.example terraform/terraform.tfvars 2>/dev/null || true
	@echo "2. Please edit terraform/terraform.tfvars with your values"
	@echo "3. Then run: make apply"

status: ## Show deployment status
	@echo "Deployment Status:"
	@echo ""
	@cd terraform && terraform output 2>/dev/null || echo "Infrastructure not deployed"

cost-estimate: ## Estimate monthly AWS costs
	@echo "Monthly Cost Estimate:"
	@echo "  Lambda:        $0.00 (free tier)"
	@echo "  S3:            ~$0.02"
	@echo "  CloudWatch:    ~$0.50"
	@echo "  Cost Explorer: ~$0.30"
	@echo "  ----------------------"
	@echo "  Total:         ~$0.82/month"
