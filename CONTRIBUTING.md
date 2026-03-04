# Contributing to Chili Cook-Off Voting Application

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

Be respectful and constructive in all interactions. We're here to build something useful together.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots if applicable
- Your environment (AWS region, browser, deployment method)
- Relevant CloudWatch logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- Detailed description of the proposed functionality
- Why this enhancement would be useful
- Possible implementation approach

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** for any new functionality
4. **Update documentation** as needed
5. **Ensure tests pass** by running `pytest tests/`
6. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured
- Git

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/chili-cookoff-voting-app.git
cd chili-cookoff-voting-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements.txt

# Run tests
pytest tests/
```

## Coding Standards

### Python Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Maximum line length: 127 characters

### Testing

- Write unit tests for all new functions
- Write property-based tests for complex logic
- Aim for >80% code coverage
- Test both success and failure cases

### Security

- Never commit AWS credentials or secrets
- Validate all user inputs
- Use parameterized queries for DynamoDB
- Follow security best practices in SECURITY.md

### Documentation

- Update README.md for user-facing changes
- Update inline comments for code changes
- Update CloudFormation template comments
- Add examples for new features

## Project Structure

```
.
├── lambda/              # Lambda function handlers
├── web/                 # Web interface files
├── infrastructure/      # CloudFormation templates
├── tests/              # Unit and property-based tests
├── .github/            # GitHub workflows and templates
└── docs/               # Additional documentation
```

## Testing Your Changes

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_vote_handler_unit.py

# Run with coverage
pytest --cov=lambda tests/
```

### Manual Testing

1. Deploy to AWS using `./deploy.sh`
2. Test all three interfaces (setup, voting, leaderboard)
3. Verify CloudWatch logs for errors
4. Test edge cases and error handling
5. Run `./teardown.sh` when done

## Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in present tense (Add, Fix, Update, Remove)
- Reference issue numbers when applicable
- Examples:
  - `Add voter ID validation to vote handler`
  - `Fix leaderboard ranking for tied scores`
  - `Update README with CloudShell instructions`

## Review Process

1. All pull requests require review before merging
2. Address review feedback promptly
3. Keep pull requests focused on a single change
4. Ensure CI checks pass before requesting review

## Questions?

Feel free to open an issue with the `question` label if you need help or clarification.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
