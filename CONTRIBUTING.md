# Contributing to Multi-Cloud Cost Optimizer

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Lambda logs (if applicable)
- AWS region and environment

### Suggesting Features

Feature requests are welcome! Please open an issue with:
- Clear description of the feature
- Use case and benefits
- Implementation ideas (optional)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   make test
   make validate
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "feat: add support for GCP cost analysis"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.11+
- Terraform 1.5+
- AWS CLI configured
- Make (optional)

### Local Setup
```bash
# Clone repository
git clone https://github.com/yourusername/multi-cloud-cost-optimizer.git
cd multi-cloud-cost-optimizer

# Install dependencies
make install-deps

# Run tests
make test
```

### Code Style

**Python**:
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused and small

**Terraform**:
- Use `terraform fmt` before committing
- Add comments for complex logic
- Use variables for configurable values

### Testing

All new features should include tests:

```bash
# Run tests
cd lambda/cost_ingestion
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Documentation

Update documentation when making changes:
- README.md for user-facing changes
- docs/ARCHITECTURE.md for architectural changes
- docs/SETUP.md for setup changes
- Inline code comments for complex logic

## Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding/updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add support for Azure cost tracking
fix: handle missing tags in EC2 scanner
docs: update setup instructions for Cost Explorer
test: add tests for S3Writer module
```

## Code Review Process

1. Automated checks must pass (when CI/CD is set up)
2. At least one maintainer approval required
3. All discussions must be resolved
4. Branch must be up to date with main

## Project Structure

```
.
├── lambda/              # Lambda function code
│   └── cost_ingestion/
│       ├── handler.py
│       └── utils/
├── terraform/           # Infrastructure as Code
├── policies/            # OPA policy files (future)
├── dashboards/          # Grafana dashboards (future)
├── docs/                # Documentation
└── tests/               # Test files
```

## Questions?

Feel free to:
- Open an issue for questions
- Join discussions in existing issues
- Reach out via email

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
