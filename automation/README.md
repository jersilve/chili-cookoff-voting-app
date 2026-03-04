# Chili Cook-Off Automation

This directory contains Lambda functions that automate deployment and teardown of the Chili Cook-Off application via simple HTTP URLs.

## Overview

Instead of running `deploy.sh` and `teardown.sh` scripts, you can:
- Visit a URL to deploy the application
- Visit another URL to teardown the application

This is perfect for:
- Mobile deployment (just visit a URL on your phone)
- Sharing with non-technical users
- Quick one-click deployment/teardown
- Integration with other systems

## Setup

### One-Time Setup

Run the automation setup script:

```bash
cd automation
./deploy-automation.sh
```

This will:
1. Create an S3 bucket for source code
2. Upload the CloudFormation template
3. Deploy two Lambda functions with Function URLs
4. Output the deployment and teardown URLs

### Output

After setup, you'll get two URLs:

```
Deploy URL: https://abc123.lambda-url.us-east-1.on.aws/
Teardown URL: https://xyz789.lambda-url.us-east-1.on.aws/
```

## Usage

### Deploy the Application

Simply visit the Deploy URL in your browser or use curl:

```bash
curl https://your-deploy-url.lambda-url.us-east-1.on.aws/
```

Response:
```json
{
  "success": true,
  "message": "Deployment completed successfully!",
  "timestamp": "2024-03-04T12:00:00Z",
  "data": {
    "albUrl": "http://chili-cookoff-alb-123.us-east-1.elb.amazonaws.com",
    "setupUrl": "http://chili-cookoff-alb-123.us-east-1.elb.amazonaws.com/static/setup.html",
    "votingUrl": "http://chili-cookoff-alb-123.us-east-1.elb.amazonaws.com/static/vote.html",
    "leaderboardUrl": "http://chili-cookoff-alb-123.us-east-1.elb.amazonaws.com/static/leaderboard.html"
  }
}
```

### Teardown the Application

Visit the Teardown URL in your browser or use curl:

```bash
curl https://your-teardown-url.lambda-url.us-east-1.on.aws/
```

Response:
```json
{
  "success": true,
  "message": "Teardown completed successfully! All resources have been removed.",
  "timestamp": "2024-03-04T13:00:00Z",
  "data": {
    "stackName": "chili-cookoff-voting-app",
    "s3Bucket": "chili-cookoff-lambda-packages-us-east-1",
    "status": "deleted"
  }
}
```

## How It Works

### Deploy Lambda Function

The deploy Lambda function:
1. Checks if the stack already exists (returns error if it does)
2. Downloads the CloudFormation template from S3
3. Creates the CloudFormation stack
4. Waits for stack creation to complete (up to 10 minutes)
5. Updates Lambda functions with code from S3
6. Updates environment variables with the ALB URL
7. Returns the application URLs

### Teardown Lambda Function

The teardown Lambda function:
1. Checks if the stack exists (returns error if it doesn't)
2. Handles DELETE_FAILED states by retaining problematic resources
3. Initiates stack deletion
4. Waits for deletion to complete (up to 10 minutes)
5. Cleans up the S3 bucket containing Lambda packages
6. Returns success confirmation

## Prerequisites

Before deploying the automation:

1. **Lambda packages must be in S3**: Run the regular `deploy.sh` script once to create and populate the Lambda packages S3 bucket
2. **AWS credentials**: Configured with sufficient permissions
3. **CloudFormation template**: Must be in `infrastructure/template.yaml`

## Security Considerations

### ⚠️ Important: URLs are Public

The Lambda Function URLs are **publicly accessible** by default. Anyone with the URL can:
- Deploy the application (incurring AWS costs)
- Teardown the application (deleting all data)

### Recommendations

1. **Keep URLs private**: Don't share them publicly
2. **Add authentication**: Modify the Lambda functions to require API keys or authentication
3. **Use IAM authorization**: Change `AuthType` from `NONE` to `AWS_IAM` in the CloudFormation template
4. **Monitor usage**: Set up CloudWatch alarms for Lambda invocations
5. **Add rate limiting**: Use AWS WAF or API Gateway to prevent abuse

### Adding Authentication (Optional)

To add simple API key authentication, modify the Lambda functions:

```python
def lambda_handler(event, context):
    # Check for API key in headers
    headers = event.get('headers', {})
    api_key = headers.get('x-api-key', '')
    
    if api_key != os.environ.get('API_KEY'):
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    # Rest of the function...
```

Then set the `API_KEY` environment variable in the Lambda function configuration.

## Costs

### Automation Infrastructure

- **Lambda Functions**: Free tier includes 1M requests/month and 400,000 GB-seconds
- **S3 Storage**: ~$0.023/GB/month for source code (~$0.001/month)
- **CloudFormation**: Free

### Application Deployment

Same costs as manual deployment:
- **ALB**: ~$0.50/hour
- **Lambda**: Minimal (free tier eligible)
- **DynamoDB**: Minimal (free tier eligible)

**Total**: ~$1-2 per event (if you teardown immediately after)

## Troubleshooting

### Deploy URL returns "Stack already exists"

The application is already deployed. Visit the Teardown URL first, then try deploying again.

### Teardown URL returns "Stack does not exist"

The application is not currently deployed. Nothing to teardown.

### Lambda timeout error

The Lambda functions have a 10-minute timeout. If deployment or teardown takes longer:
1. Check CloudFormation console for stack status
2. Check CloudWatch Logs for detailed error messages
3. Manually complete the operation if needed

### "Failed to download template from S3"

The CloudFormation template is not in S3. Run `./deploy-automation.sh` again to upload it.

### Lambda packages not found

Run the regular `deploy.sh` script once to create and populate the Lambda packages S3 bucket.

## Cleanup

To remove the automation infrastructure:

```bash
aws cloudformation delete-stack --stack-name chili-cookoff-automation
aws s3 rm s3://chili-cookoff-automation-source-${AWS_REGION} --recursive
aws s3 rb s3://chili-cookoff-automation-source-${AWS_REGION}
```

## Advanced Usage

### Programmatic Deployment

Use the URLs in scripts or applications:

```bash
#!/bin/bash

# Deploy
DEPLOY_RESPONSE=$(curl -s https://your-deploy-url.lambda-url.us-east-1.on.aws/)
ALB_URL=$(echo $DEPLOY_RESPONSE | jq -r '.data.albUrl')

echo "Application deployed at: $ALB_URL"

# Wait for event to complete...
sleep 7200  # 2 hours

# Teardown
curl https://your-teardown-url.lambda-url.us-east-1.on.aws/
```

### Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Deploy Chili Cook-Off App
  run: |
    curl -f ${{ secrets.DEPLOY_URL }} || exit 1

- name: Run Tests
  run: |
    # Your tests here

- name: Teardown Chili Cook-Off App
  if: always()
  run: |
    curl -f ${{ secrets.TEARDOWN_URL }}
```

## Files

- `deploy_lambda.py`: Lambda function for deployment
- `teardown_lambda.py`: Lambda function for teardown
- `automation-template.yaml`: CloudFormation template for automation infrastructure
- `deploy-automation.sh`: Script to set up the automation infrastructure
- `README.md`: This file

## Support

For issues or questions:
- Check CloudWatch Logs for Lambda function errors
- Review CloudFormation events in the AWS Console
- See the main project README for general troubleshooting
