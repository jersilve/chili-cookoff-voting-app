# Quick Start - Deploy from Anywhere

This guide shows you how to deploy the Chili Cook-Off application with a single command, directly from GitHub.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions

## One-Command Deploy

### Option 1: Using the Quick Deploy Script

```bash
curl -s https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/quick-deploy.sh | bash
```

Or clone the repo and run:

```bash
./quick-deploy.sh
```

### Option 2: Direct CloudFormation Deploy

```bash
aws cloudformation create-stack \
  --stack-name chili-cookoff-voting-app \
  --template-url https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/infrastructure/template-github.yaml \
  --parameters \
      ParameterKey=GitHubRepo,ParameterValue=jersilve/chili-cookoff-voting-app \
      ParameterKey=GitHubBranch,ParameterValue=main \
  --capabilities CAPABILITY_NAMED_IAM
```

## What Happens During Deployment

1. **CloudFormation creates infrastructure** (5-10 minutes):
   - VPC, subnets, and networking
   - Application Load Balancer
   - DynamoDB table
   - Lambda functions (with placeholder code)
   - IAM roles and permissions

2. **Custom Resource downloads code from GitHub**:
   - Downloads Lambda function code from your GitHub repo
   - Downloads static HTML/CSS files
   - Updates all Lambda functions with actual code
   - No S3 buckets or manual packaging needed!

3. **Stack outputs application URLs**:
   - Setup page
   - Voting page
   - Leaderboard page

## One-Command Teardown

```bash
curl -s https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/quick-teardown.sh | bash
```

Or:

```bash
./quick-teardown.sh
```

Or directly with AWS CLI:

```bash
aws cloudformation delete-stack --stack-name chili-cookoff-voting-app
```

## Deploy from CloudShell

1. Open AWS CloudShell in your browser
2. Run:
   ```bash
   curl -s https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/quick-deploy.sh | bash
   ```
3. Wait 5-10 minutes
4. Get your URLs from the output!

## Deploy from Your Phone

1. Open AWS Console on your phone
2. Open CloudShell
3. Paste the deploy command
4. Done!

## Custom Stack Name

```bash
STACK_NAME=my-chili-event ./quick-deploy.sh
```

Or:

```bash
aws cloudformation create-stack \
  --stack-name my-chili-event \
  --template-url https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/main/infrastructure/template-github.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

## Deploy from a Different Branch

```bash
GITHUB_BRANCH=develop ./quick-deploy.sh
```

Or:

```bash
aws cloudformation create-stack \
  --stack-name chili-cookoff-voting-app \
  --template-url https://raw.githubusercontent.com/jersilve/chili-cookoff-voting-app/develop/infrastructure/template-github.yaml \
  --parameters \
      ParameterKey=GitHubBranch,ParameterValue=develop \
  --capabilities CAPABILITY_NAMED_IAM
```

## How It Works

### Traditional Approach (Old Way)
1. Clone repo locally
2. Package Lambda functions into zip files
3. Upload zip files to S3
4. Deploy CloudFormation with S3 references
5. Update Lambda functions after stack creation

### GitHub Direct Deploy (New Way)
1. Run one command
2. CloudFormation creates infrastructure
3. Custom Resource Lambda downloads code from GitHub
4. Lambda functions are automatically updated
5. Done!

### Benefits
- ✅ No S3 buckets to manage
- ✅ No local packaging required
- ✅ Deploy from anywhere (phone, CloudShell, any computer)
- ✅ Code always comes from GitHub (single source of truth)
- ✅ Easy to deploy different branches
- ✅ Automatic code updates on stack updates

## Troubleshooting

### "Stack already exists"

Teardown first:
```bash
./quick-teardown.sh
```

Or use a different stack name:
```bash
STACK_NAME=my-event ./quick-deploy.sh
```

### "Failed to download from GitHub"

Check that:
- The GitHub repo is public
- The branch name is correct
- The file paths in the template match your repo structure

### Stack creation failed

Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name chili-cookoff-voting-app \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### Lambda functions not working

The Custom Resource should automatically update them. Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/ChiliCookoffCodeUpdater --follow
```

## Cost Considerations

Same as before:
- **ALB**: ~$0.50/hour
- **Lambda**: Free tier eligible
- **DynamoDB**: Free tier eligible
- **Total**: ~$1-2 per event (if you teardown immediately after)

## Comparison with Old Approach

| Feature | Old (deploy.sh) | New (quick-deploy.sh) |
|---------|----------------|----------------------|
| **S3 Buckets** | Required | Not needed |
| **Local Packaging** | Required | Not needed |
| **Deploy from Phone** | No | Yes |
| **Deploy from CloudShell** | Complex | Simple |
| **Code Source** | Local files | GitHub (single source of truth) |
| **Commands** | Multiple steps | One command |
| **Maintenance** | S3 cleanup needed | Automatic |

## Next Steps

After deployment:
1. Visit the Setup URL to configure your event
2. Share the Voting URL with participants
3. Display the Leaderboard URL during your event
4. Run teardown when finished to avoid charges

## Advanced Usage

### Fork and Customize

1. Fork the repository
2. Make your changes
3. Deploy from your fork:
   ```bash
   aws cloudformation create-stack \
     --stack-name my-custom-app \
     --template-url https://raw.githubusercontent.com/YOUR-USERNAME/chili-cookoff-voting-app/main/infrastructure/template-github.yaml \
     --parameters \
         ParameterKey=GitHubRepo,ParameterValue=YOUR-USERNAME/chili-cookoff-voting-app \
     --capabilities CAPABILITY_NAMED_IAM
   ```

### Update Running Stack

To update code without redeploying:

```bash
aws cloudformation update-stack \
  --stack-name chili-cookoff-voting-app \
  --use-previous-template \
  --capabilities CAPABILITY_NAMED_IAM
```

This triggers the Custom Resource to re-download code from GitHub.

### CI/CD Integration

Add to your GitHub Actions:

```yaml
- name: Deploy to AWS
  run: |
    aws cloudformation create-stack \
      --stack-name chili-cookoff-${{ github.sha }} \
      --template-url https://raw.githubusercontent.com/${{ github.repository }}/main/infrastructure/template-github.yaml \
      --capabilities CAPABILITY_NAMED_IAM
```

## Support

For issues:
- Check [README.md](README.md) for detailed documentation
- Review [TROUBLESHOOTING.md](README.md#troubleshooting) section
- Open an issue on GitHub
