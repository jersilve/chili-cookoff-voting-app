# Deploying from AWS CloudShell

This guide explains how to deploy the Chili Cook-Off Voting App from AWS CloudShell, allowing you to deploy from anywhere using just a web browser (including your phone).

## What is AWS CloudShell?

AWS CloudShell is a browser-based shell that gives you command-line access to AWS resources. It comes pre-installed with:
- AWS CLI (already configured with your credentials)
- Python 3 and pip
- Git
- Common Linux utilities

## Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **Web Browser**: Any modern browser (Chrome, Safari, Firefox, etc.)

## Deployment Steps

### Option 1: Deploy from S3 (Recommended)

This method allows you to upload the project once and deploy multiple times without re-uploading.

#### Step 1: Upload Project to S3 (One-time setup)

From your local machine:

```bash
# Create a unique S3 bucket for your project files
aws s3 mb s3://chili-cookoff-source-code-YOUR-UNIQUE-ID

# Upload the entire project to S3
aws s3 sync . s3://chili-cookoff-source-code-YOUR-UNIQUE-ID/ \
  --exclude ".git/*" \
  --exclude ".hypothesis/*" \
  --exclude ".pytest_cache/*" \
  --exclude "venv/*" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "qr-codes/*" \
  --exclude "*.zip"
```

#### Step 2: Deploy from CloudShell

1. **Open AWS CloudShell**:
   - Log into AWS Console (https://console.aws.amazon.com)
   - Click the CloudShell icon (>_) in the top navigation bar
   - Wait for CloudShell to initialize (takes ~30 seconds)

2. **Download project from S3**:
   ```bash
   # Download the project
   aws s3 sync s3://chili-cookoff-source-code-YOUR-UNIQUE-ID/ ~/chili-cookoff/
   
   # Navigate to project directory
   cd ~/chili-cookoff
   ```

3. **Make deploy script executable**:
   ```bash
   chmod +x deploy.sh
   ```

4. **Run deployment**:
   ```bash
   ./deploy.sh
   ```

5. **Check terminal output**:
   - URLs are displayed in CloudShell output
   - QR codes are generated in the qr-codes/ directory

### Option 2: Deploy from GitHub

If your project is in a GitHub repository:

1. **Open AWS CloudShell**

2. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/chili-cookoff-app.git
   cd chili-cookoff-app
   ```

3. **Make deploy script executable**:
   ```bash
   chmod +x deploy.sh
   ```

4. **Run deployment**:
   ```bash
   ./deploy.sh
   ```

### Option 3: Quick Deploy (Copy-Paste)

For a one-time deployment without S3 or GitHub:

1. **Open AWS CloudShell**

2. **Create project directory**:
   ```bash
   mkdir -p ~/chili-cookoff
   cd ~/chili-cookoff
   ```

3. **Upload files using CloudShell Actions**:
   - Click "Actions" → "Upload file" in CloudShell
   - Upload `deploy.sh` and `teardown.sh`
   - Create subdirectories and upload files:
     ```bash
     mkdir -p infrastructure lambda web
     ```
   - Upload files to their respective directories

4. **Make scripts executable and run**:
   ```bash
   chmod +x deploy.sh teardown.sh
   ./deploy.sh
   ```

## Deploying from Your Phone

CloudShell works great on mobile devices:

1. **Open AWS Console on your phone's browser**
2. **Tap the CloudShell icon** (you may need to scroll the top menu)
3. **Run the deployment commands** (use Option 1 or 2 above)
4. **Check terminal output** for the URLs

**Tip**: For easier typing on mobile, use the S3 method (Option 1) so you only need to type a few commands.

## CloudShell Limitations

Be aware of these CloudShell limitations:

1. **Session Timeout**: CloudShell sessions timeout after ~20 minutes of inactivity
2. **Storage**: 1 GB of persistent storage in your home directory
3. **Compute**: Limited compute resources (sufficient for this deployment)
4. **Region**: CloudShell runs in specific regions - ensure you're in a supported region

## Troubleshooting

### Issue: "Command not found: pip"

**Solution**: CloudShell has Python 3 pre-installed. Use `pip3` instead:
```bash
# The deploy script should work as-is, but if you need to install packages manually:
pip3 install qrcode pillow
```

### Issue: "Permission denied: ./deploy.sh"

**Solution**: Make the script executable:
```bash
chmod +x deploy.sh
```

### Issue: CloudShell session disconnected during deployment

**Solution**: 
1. Reconnect to CloudShell
2. Check if the stack is still being created:
   ```bash
   aws cloudformation describe-stacks --stack-name chili-cookoff-voting-app
   ```
3. If stack creation is in progress, wait for it to complete
4. If stack creation failed, run teardown and try again:
   ```bash
   cd ~/chili-cookoff
   ./teardown.sh
   ./deploy.sh
   ```

### Issue: "Region not supported"

**Solution**: CloudShell is available in specific regions. Switch to a supported region:
- US East (N. Virginia) - us-east-1
- US West (Oregon) - us-west-2
- Europe (Ireland) - eu-west-1
- Asia Pacific (Tokyo) - ap-northeast-1

Change region in the AWS Console top-right dropdown, then open CloudShell.

## Teardown from CloudShell

To remove all resources after your event:

```bash
cd ~/chili-cookoff
./teardown.sh
```

## Best Practices

1. **Use S3 Method**: Upload your project to S3 once, deploy multiple times
2. **Keep CloudShell Active**: Don't let it timeout during deployment (takes 5-10 minutes)
3. **Save Output**: Copy the ALB URL from CloudShell output
4. **Clean Up**: Always run teardown after your event to avoid charges

## Cost Considerations

- **CloudShell**: Free! No charges for using CloudShell
- **S3 Storage**: ~$0.023/GB/month for storing project files (~$0.001/month for this project)
- **Application**: Same costs as regular deployment (~$1-2 per event)

## Example: Complete Mobile Deployment Workflow

Here's the complete workflow for deploying from your phone:

1. **One-time setup** (from computer):
   ```bash
   aws s3 mb s3://chili-cookoff-source-YOUR-NAME
   aws s3 sync . s3://chili-cookoff-source-YOUR-NAME/ --exclude ".git/*" --exclude "venv/*"
   ```

2. **Deploy from phone** (anytime you need it):
   - Open AWS Console on phone
   - Tap CloudShell icon
   - Run:
     ```bash
     aws s3 sync s3://chili-cookoff-source-YOUR-NAME/ ~/chili-cookoff/
     cd ~/chili-cookoff
     chmod +x deploy.sh
     ./deploy.sh
     ```
   - Check terminal output for URLs
   - Start your event!

3. **Teardown from phone** (after event):
   - Open CloudShell
   - Run:
     ```bash
     cd ~/chili-cookoff
     ./teardown.sh
     ```

That's it! You can now deploy your chili cook-off app from anywhere, anytime, using just a web browser.
