# Chili Cook-Off Voting Application

A serverless web application for running chili competitions with ranked voting and real-time leaderboards. Built on AWS using Lambda, DynamoDB, and Application Load Balancer.

## Features

- **Setup Interface**: Configure competition entries with custom names
- **Voting Interface**: Cast ranked votes for top 3 chili entries
- **Leaderboard Interface**: View real-time rankings with automatic updates
- **Automated Deployment**: One-command deployment to AWS
- **Automated Teardown**: Clean removal of all AWS resources
- **Email Notifications**: Automatic email with URLs and QR codes after deployment

## Architecture

The application uses a serverless architecture:
- **Frontend**: Static HTML/CSS/JavaScript served via Lambda
- **Backend**: Python Lambda functions for API endpoints
- **Database**: DynamoDB for data persistence
- **Load Balancer**: Application Load Balancer for routing
- **Infrastructure**: CloudFormation for automated provisioning

## Prerequisites

Before deploying the application, ensure you have:

1. **AWS Account**: An active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured on your Mac
3. **AWS Credentials**: Configured with sufficient permissions

### Installing AWS CLI

If you don't have AWS CLI installed:

```bash
# Using Homebrew (recommended for Mac)
brew install awscli

# Or download from AWS
# Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
```

### Configuring AWS Credentials

Configure your AWS credentials:

```bash
aws configure
```

You'll need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### Required AWS Permissions

Your AWS credentials must have permissions for:
- CloudFormation (create/delete stacks)
- DynamoDB (create/delete tables)
- Lambda (create/update/delete functions)
- Application Load Balancer (create/delete ALB, target groups, listeners)
- IAM (create/delete roles and policies)
- S3 (create/delete buckets, upload objects)

## Deployment

### Quick Start

Deploy the application with a single command:

```bash
./deploy.sh
```

### Deploy from Anywhere (CloudShell)

You can deploy from your phone or any web browser using AWS CloudShell:

1. **Upload project to S3** (one-time setup from your computer):
   ```bash
   ./upload-to-s3.sh
   ```

2. **Open AWS CloudShell** in your browser

3. **Download and run deploy script**:
   ```bash
   aws s3 cp s3://YOUR-BUCKET-NAME/quick-deploy.sh .
   chmod +x quick-deploy.sh
   ./quick-deploy.sh
   ./deploy.sh
   ```

4. **Check your email** for URLs and QR codes

**See [CLOUDSHELL_DEPLOY.md](CLOUDSHELL_DEPLOY.md) for detailed instructions.**

### Deployment Process

The deployment script will:

1. Validate AWS CLI installation and credentials
2. Create an S3 bucket for Lambda deployment packages
3. Package all Lambda functions into zip files
4. Upload Lambda packages to S3
5. Create CloudFormation stack with all AWS resources
6. Wait for stack creation to complete (typically 3-5 minutes)
7. Update Lambda functions with deployment code
8. **Send deployment notification email** with URLs and QR codes
9. Output the Application Load Balancer URL

### Deployment Email

After successful deployment, you'll automatically receive an email at `jeremy.r.silverman@gmail.com` containing:

- All application URLs (Setup, Voting, Leaderboard)
- QR codes for each URL (embedded in the email)
- Next steps for running your event

This allows you to deploy from anywhere (including your phone via AWS Console) and immediately receive all the information you need to run your event.

**Note**: The sender email address (jeremy.r.silverman@gmail.com) must be verified in AWS SES. This has already been configured for your account.

### Deployment Output

Upon successful deployment, you'll see:

```
=========================================
SUCCESS: Deployment completed successfully!
=========================================

📧 A deployment notification email has been sent to:
   jeremy.r.silverman@gmail.com

Application URL: http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com

Available endpoints:
  - Setup:       http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/static/setup.html
  - Voting:      http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/static/vote.html
  - Leaderboard: http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/static/leaderboard.html

API endpoints:
  - Setup API:       http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/api/setup
  - Vote API:        http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/api/vote
  - Leaderboard API: http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com/api/leaderboard
```

**Check your email** for the deployment notification with QR codes!

### Custom Region

To deploy to a different AWS region:

```bash
export AWS_DEFAULT_REGION=us-west-2
./deploy.sh
```

## Usage

### Step 1: Configure Competition Entries

1. Open the Setup interface in your browser:
   ```
   http://YOUR-ALB-URL/static/setup.html
   ```

2. Enter the number of chili entries (1-50)

3. Provide a name for each entry (e.g., "Spicy Texas Chili", "Mild Bean Chili")

4. Click "Submit Configuration"

5. Wait for confirmation message

**Note**: Running setup again will clear all existing entries and votes!

### Step 2: Share Voting Link

Share the voting URL with participants:
```
http://YOUR-ALB-URL/static/vote.html
```

**Tip**: Create a QR code for easy mobile access!

### Step 3: Cast Votes

Participants can vote by:

1. Opening the voting interface
2. Selecting their top 3 chili entries in ranked order:
   - 1st choice: 3 points
   - 2nd choice: 2 points
   - 3rd choice: 1 point
3. Clicking "Submit Vote"
4. Receiving confirmation

**Note**: Each vote must select exactly 3 different entries.

### Step 4: View Leaderboard

View real-time rankings at:
```
http://YOUR-ALB-URL/static/leaderboard.html
```

The leaderboard:
- Updates automatically every 5 seconds
- Shows all entries sorted by total points
- Displays current point totals
- Shows last update timestamp

**Tip**: Display the leaderboard on a large screen during your event!

## Teardown

### Removing All Resources

When your event is complete, remove all AWS resources:

```bash
./teardown.sh
```

### Teardown Process

The teardown script will:

1. Validate AWS CLI installation and credentials
2. Check if the CloudFormation stack exists
3. Initiate stack deletion
4. Wait for deletion to complete (typically 3-5 minutes)
5. Verify all resources are removed
6. Delete the S3 bucket containing Lambda packages
7. Display confirmation

### Teardown Output

Upon successful teardown:

```
=========================================
SUCCESS: Teardown completed successfully!
=========================================

All AWS resources have been removed

Removed resources:
  ✓ CloudFormation stack: chili-cookoff-voting-app
  ✓ DynamoDB table
  ✓ Lambda functions
  ✓ Application Load Balancer
  ✓ IAM roles and policies
  ✓ S3 bucket: chili-cookoff-lambda-packages-us-east-1
```

**Important**: Always run teardown after your event to avoid ongoing AWS charges!

## Troubleshooting

### Deployment Issues

#### Error: "AWS CLI not found"

**Problem**: AWS CLI is not installed.

**Solution**:
```bash
# Install using Homebrew
brew install awscli

# Or download from AWS
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
```

#### Error: "AWS credentials not configured"

**Problem**: AWS credentials are not set up.

**Solution**:
```bash
aws configure
```
Provide your AWS Access Key ID, Secret Access Key, and default region.

#### Error: "Stack already exists"

**Problem**: A previous deployment wasn't cleaned up.

**Solution**:
```bash
# Remove the existing stack first
./teardown.sh

# Then deploy again
./deploy.sh
```

#### Error: "Insufficient AWS permissions"

**Problem**: Your AWS credentials lack required permissions.

**Solution**: Ensure your IAM user/role has permissions for:
- CloudFormation
- DynamoDB
- Lambda
- Application Load Balancer
- IAM
- S3

Contact your AWS administrator to grant these permissions.

#### Error: "Stack creation failed"

**Problem**: CloudFormation encountered an error during resource creation.

**Solution**:
1. Check the error message displayed by the deployment script
2. Common causes:
   - Service limits reached (e.g., too many ALBs)
   - Region doesn't support required services
   - Naming conflicts with existing resources
3. Run teardown to clean up partial deployment:
   ```bash
   ./teardown.sh
   ```
4. Address the underlying issue and redeploy

### Application Issues

#### Issue: "Deployment email not received"

**Problem**: Email notification wasn't sent or was filtered as spam.

**Solution**:
1. Check your spam/junk folder for emails from jeremy.r.silverman@gmail.com
2. Verify the sender email is verified in AWS SES:
   ```bash
   aws ses list-verified-email-addresses --region us-east-1
   ```
3. Check CloudWatch Logs for the deployment notifier Lambda:
   ```bash
   aws logs tail /aws/lambda/ChiliCookoffDeploymentNotifier --follow
   ```
4. The URLs are also displayed in the terminal after deployment completes

#### Issue: "No entries configured" when voting

**Problem**: Setup hasn't been completed yet.

**Solution**: Access the setup interface and configure entries first.

#### Issue: Leaderboard not updating

**Problem**: Browser caching or network issues.

**Solution**:
1. Refresh the page (Cmd+R or Ctrl+R)
2. Clear browser cache
3. Check browser console for JavaScript errors
4. Verify internet connection

#### Issue: "Unable to submit vote"

**Problem**: Network error or invalid vote selection.

**Solution**:
1. Ensure you selected exactly 3 different entries
2. Check your internet connection
3. Verify the ALB URL is correct
4. Try refreshing the page and submitting again

#### Issue: Votes not appearing on leaderboard

**Problem**: DynamoDB write delay or Lambda function error.

**Solution**:
1. Wait 5-10 seconds for the leaderboard to refresh
2. Check AWS CloudWatch Logs for Lambda errors:
   ```bash
   aws logs tail /aws/lambda/ChiliCookoffVoteHandler --follow
   ```
3. Verify DynamoDB table exists and is accessible

### Teardown Issues

#### Error: "Stack deletion failed"

**Problem**: Some resources couldn't be deleted.

**Solution**:
1. Check which resources failed (displayed in error message)
2. Manually delete problematic resources in AWS Console
3. Run teardown again:
   ```bash
   ./teardown.sh
   ```

#### Error: "Failed to delete S3 bucket"

**Problem**: S3 bucket is not empty or has versioning enabled.

**Solution**:
1. The script attempts to empty the bucket automatically
2. If it fails, manually empty the bucket in AWS Console
3. Delete the bucket: `chili-cookoff-lambda-packages-{region}`

### Performance Issues

#### Issue: Slow page loads

**Problem**: Cold start latency for Lambda functions.

**Solution**:
- First request after deployment may be slow (5-10 seconds)
- Subsequent requests will be faster
- Consider using Lambda provisioned concurrency for production events

#### Issue: Leaderboard slow with many votes

**Problem**: DynamoDB scan operation becomes slower with more data.

**Solution**:
- Expected behavior for large vote counts (1000+)
- Leaderboard should still update within 5 seconds
- For very large events, consider implementing DynamoDB Streams with aggregation

### Getting Help

If you encounter issues not covered here:

1. **Check AWS CloudWatch Logs**:
   ```bash
   # View Lambda function logs
   aws logs tail /aws/lambda/ChiliCookoffSetupHandler --follow
   aws logs tail /aws/lambda/ChiliCookoffVoteHandler --follow
   aws logs tail /aws/lambda/ChiliCookoffLeaderboardHandler --follow
   ```

2. **Check CloudFormation Events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name chili-cookoff-voting-app \
     --max-items 20
   ```

3. **Verify Resources**:
   ```bash
   # Check if stack exists
   aws cloudformation describe-stacks \
     --stack-name chili-cookoff-voting-app
   
   # Check DynamoDB table
   aws dynamodb describe-table \
     --table-name ChiliCookoffData
   ```

## Project Structure

```
.
├── deploy.sh                 # Deployment automation script
├── teardown.sh              # Teardown automation script
├── upload-to-s3.sh          # Upload project to S3 for CloudShell deployment
├── CLOUDSHELL_DEPLOY.md     # Guide for deploying from AWS CloudShell
├── S3_UPLOAD_COMMANDS.md    # Quick reference for S3 commands
├── infrastructure/
│   └── template.yaml        # CloudFormation template
├── lambda/
│   ├── setup_handler.py     # Setup API Lambda function
│   ├── vote_handler.py      # Vote API Lambda function
│   ├── leaderboard_handler.py  # Leaderboard API Lambda function
│   ├── static_handler.py    # Static content Lambda function
│   ├── deployment_notifier.py  # Deployment email Lambda function
│   ├── setup_requirements.txt  # Dependencies for setup handler
│   └── deployment_requirements.txt  # Dependencies for deployment notifier
├── web/
│   ├── setup.html          # Setup interface
│   ├── vote.html           # Voting interface
│   ├── leaderboard.html    # Leaderboard interface
│   └── styles.css          # Shared styles
├── qr-codes/               # Generated QR codes (created by deploy.sh)
├── tests/                   # Unit and property-based tests
└── README.md               # This file
```

## Cost Considerations

### Estimated Costs

For a typical chili cook-off event (50 participants, 10 entries, 2-hour duration):

- **Lambda**: ~$0.01 (free tier eligible)
- **DynamoDB**: ~$0.01 (free tier eligible)
- **Application Load Balancer**: ~$0.50 per hour = $1.00 for 2 hours
- **Data Transfer**: ~$0.01

**Total estimated cost**: ~$1.02 per event

### Cost Optimization Tips

1. **Run teardown immediately after your event** to stop ALB charges
2. **Use free tier**: AWS Free Tier includes:
   - 1 million Lambda requests per month
   - 25 GB DynamoDB storage
   - 400,000 seconds of Lambda compute time
3. **Short events**: ALB is charged hourly, so shorter events cost less
4. **Single region**: Deploy only in one region to avoid cross-region charges

### Ongoing Costs

If you don't run teardown:
- **Application Load Balancer**: ~$0.50/hour = ~$360/month
- **DynamoDB**: ~$0.25/month (on-demand, minimal usage)
- **Lambda**: $0 (no requests = no charges)

**Always run teardown.sh after your event!**

## Security Considerations

### Public Access

The application is publicly accessible via the ALB URL. Anyone with the URL can:
- Configure entries (setup interface)
- Submit votes (voting interface)
- View leaderboard (leaderboard interface)

### Recommendations

1. **Share URLs carefully**: Only share voting/leaderboard URLs with participants
2. **Keep setup URL private**: Only share with organizers
3. **Run setup once**: Configure entries before sharing voting URL
4. **Time-limited events**: Deploy just before your event, teardown immediately after
5. **No authentication**: This is a simple application without user authentication

### Data Privacy

- No personally identifiable information (PII) is collected
- Votes are anonymous (no voter identification)
- Entry names and vote data are stored in DynamoDB
- All data is deleted when you run teardown

## Development

### Running Tests

The project includes comprehensive unit and property-based tests:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_vote_handler_unit.py

# Run with coverage
pytest --cov=lambda tests/
```

### Local Development

To modify Lambda functions:

1. Edit files in the `lambda/` directory
2. Test locally using pytest
3. Redeploy to AWS:
   ```bash
   ./deploy.sh
   ```

### Modifying Web Interfaces

To modify web interfaces:

1. Edit files in the `web/` directory
2. Test locally by opening HTML files in browser
3. Redeploy to AWS:
   ```bash
   ./deploy.sh
   ```

## License

This project is provided as-is for educational and event purposes.

## Support

For issues, questions, or contributions, please refer to the troubleshooting section above or check AWS CloudWatch Logs for detailed error information.
