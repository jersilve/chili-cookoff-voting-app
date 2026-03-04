# Chili Cook-Off Voting Application

[![Tests](https://github.com/jersilve/chili-cookoff-voting-app/workflows/Tests/badge.svg)](https://github.com/jersilve/chili-cookoff-voting-app/actions)
[![Lint](https://github.com/jersilve/chili-cookoff-voting-app/workflows/Lint/badge.svg)](https://github.com/jersilve/chili-cookoff-voting-app/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB-orange.svg)](https://aws.amazon.com/)

A serverless web application for running chili competitions with ranked voting and real-time leaderboards. Deploy from anywhere with a single command - no S3 buckets, no local packaging, just pure GitHub-to-AWS magic.

## Quick Start

Deploy from anywhere (phone, CloudShell, laptop) with one command:

```bash
curl -s https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/quick-deploy.sh | bash
```

Or clone and run:

```bash
git clone https://github.com/jersilve/chili-cookoff-voting-app.git
cd chili-cookoff-voting-app
./quick-deploy.sh
```

Teardown when finished:

```bash
./quick-teardown.sh
```

**See [QUICK_START.md](QUICK_START.md) for detailed deployment options.**

## Features

- **One-Command Deploy**: Deploy directly from GitHub with zero local setup
- **Deploy from Anywhere**: Phone, CloudShell, laptop - if it has AWS CLI, it works
- **No S3 Buckets**: Code downloads directly from GitHub during deployment
- **Setup Interface**: Configure competition entries with custom names
- **Voting Interface**: Cast ranked votes for top 3 entries
- **Leaderboard Interface**: View real-time rankings with automatic updates
- **Multi-Voter Support**: Multiple voters per device (great for families)
- **Security Hardened**: Input validation, security headers, DynamoDB encryption
- **Comprehensive Testing**: Unit tests and property-based tests included

## How It Works

Traditional serverless deployment requires:
1. Clone repo locally
2. Package Lambda functions
3. Upload to S3
4. Deploy CloudFormation
5. Update Lambda functions

This app does it differently:
1. Run one command
2. CloudFormation creates infrastructure
3. Custom Resource Lambda downloads code from GitHub
4. Lambda functions automatically updated
5. Done!

## Architecture

- **Frontend**: Static HTML/CSS/JavaScript served via Lambda
- **Backend**: Python Lambda functions for API endpoints
- **Database**: DynamoDB for data persistence
- **Load Balancer**: Application Load Balancer for routing
- **Infrastructure**: CloudFormation with GitHub direct deploy

## Usage

After deployment, you'll get three URLs:

1. **Setup URL**: Configure your chili entries (organizers only)
2. **Voting URL**: Share with participants to cast votes
3. **Leaderboard URL**: Display real-time rankings during your event

Each voter selects their top 3 entries:
- 1st choice: 3 points
- 2nd choice: 2 points  
- 3rd choice: 1 point

The leaderboard updates automatically every 5 seconds.

## Cost

For a typical 2-hour event with 50 participants:
- **Lambda**: ~$0.01 (free tier eligible)
- **DynamoDB**: ~$0.01 (free tier eligible)
- **Application Load Balancer**: ~$1.00 (charged hourly)

**Total**: ~$1.02 per event

**Important**: Run `./quick-teardown.sh` after your event to avoid ongoing ALB charges (~$360/month).

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions

## Advanced Usage

### Deploy from a Different Branch

```bash
GITHUB_BRANCH=develop ./quick-deploy.sh
```

### Custom Stack Name

```bash
STACK_NAME=my-chili-event ./quick-deploy.sh
```

### Fork and Customize

1. Fork this repository
2. Make your changes
3. Deploy from your fork:
   ```bash
   curl -s https://raw.githubusercontent.com/YOUR-USERNAME/chili-cookoff-voting-app/main/infrastructure/template.yaml -o template.yaml
   aws cloudformation create-stack \
     --stack-name my-custom-app \
     --template-body file://template.yaml \
     --parameters ParameterKey=GitHubRepo,ParameterValue=YOUR-USERNAME/chili-cookoff-voting-app \
     --capabilities CAPABILITY_NAMED_IAM
   ```

## Development

### Running Tests

```bash
pip install -r tests/requirements.txt
pytest tests/
```

### Local Development

1. Edit files in `lambda/` or `web/` directories
2. Test locally
3. Commit and push to GitHub
4. Redeploy:
   ```bash
   ./quick-deploy.sh
   ```

## Project Structure

```
.
├── quick-deploy.sh          # One-command deployment
├── quick-teardown.sh        # One-command cleanup
├── QUICK_START.md           # Detailed deployment guide
├── infrastructure/
│   └── template.yaml        # CloudFormation with GitHub deploy
├── lambda/
│   ├── setup_handler.py     # Setup API
│   ├── vote_handler.py      # Vote API
│   ├── leaderboard_handler.py  # Leaderboard API
│   ├── static_handler.py    # Static content
│   └── security_utils.py    # Security utilities
├── web/
│   ├── setup.html          # Setup interface
│   ├── vote.html           # Voting interface
│   ├── leaderboard.html    # Leaderboard interface
│   └── styles.css          # Shared styles
└── tests/                   # Unit and property-based tests
```

## Security

- Application is publicly accessible via ALB URL
- No authentication (simple event application)
- No PII collected (anonymous voting)
- Input validation and security headers on all endpoints
- DynamoDB encryption at rest
- All data deleted on teardown

**Recommendations**:
- Keep setup URL private (organizers only)
- Share voting/leaderboard URLs with participants
- Deploy just before event, teardown immediately after

## Troubleshooting

### Stack Already Exists

```bash
./quick-teardown.sh
# Then deploy again
./quick-deploy.sh
```

### Deployment Failed

Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name chili-cookoff-voting-app \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### Lambda Functions Not Working

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/ChiliCookoffCodeUpdater --follow
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Support

- Open an [issue](https://github.com/jersilve/chili-cookoff-voting-app/issues)
- Submit a [pull request](https://github.com/jersilve/chili-cookoff-voting-app/pulls)
- Check [QUICK_START.md](QUICK_START.md) for detailed documentation
