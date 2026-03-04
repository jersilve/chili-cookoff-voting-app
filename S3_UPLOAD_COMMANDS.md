# S3 Upload Commands - Quick Reference

Use these commands to upload your project to S3 for CloudShell deployment.

## One-Time Setup

Run these commands from your local machine (where you have the project):

```bash
# 1. Create a unique S3 bucket (replace YOUR-NAME with something unique)
aws s3 mb s3://chili-cookoff-source-YOUR-NAME

# 2. Upload the entire project to S3
aws s3 sync . s3://chili-cookoff-source-YOUR-NAME/ \
  --exclude ".git/*" \
  --exclude ".hypothesis/*" \
  --exclude ".pytest_cache/*" \
  --exclude ".vscode/*" \
  --exclude ".kiro/*" \
  --exclude "venv/*" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "qr-codes/*" \
  --exclude "*.zip" \
  --exclude ".DS_Store"

# 3. Verify upload
aws s3 ls s3://chili-cookoff-source-YOUR-NAME/ --recursive
```

## Update Project in S3

When you make changes to your local project and want to update S3:

```bash
# Sync changes to S3
aws s3 sync . s3://chili-cookoff-source-YOUR-NAME/ \
  --exclude ".git/*" \
  --exclude ".hypothesis/*" \
  --exclude ".pytest_cache/*" \
  --exclude ".vscode/*" \
  --exclude ".kiro/*" \
  --exclude "venv/*" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "qr-codes/*" \
  --exclude "*.zip" \
  --exclude ".DS_Store" \
  --delete
```

The `--delete` flag removes files from S3 that no longer exist locally.

## CloudShell Deployment Commands

Once uploaded to S3, use these commands in CloudShell:

```bash
# Download project from S3
aws s3 sync s3://chili-cookoff-source-YOUR-NAME/ ~/chili-cookoff/

# Navigate to project
cd ~/chili-cookoff

# Make scripts executable
chmod +x deploy.sh teardown.sh

# Deploy
./deploy.sh

# After event, teardown
./teardown.sh
```

## Mobile-Friendly Commands

For easier typing on mobile, create a simple script in S3:

```bash
# Create a deploy script
cat > quick-deploy.sh << 'EOF'
#!/bin/bash
aws s3 sync s3://chili-cookoff-source-YOUR-NAME/ ~/chili-cookoff/
cd ~/chili-cookoff
chmod +x deploy.sh
./deploy.sh
EOF

# Upload to S3
aws s3 cp quick-deploy.sh s3://chili-cookoff-source-YOUR-NAME/
```

Then in CloudShell (from phone):

```bash
aws s3 cp s3://chili-cookoff-source-YOUR-NAME/quick-deploy.sh .
chmod +x quick-deploy.sh
./quick-deploy.sh
```

## Clean Up S3 Bucket

When you no longer need the project in S3:

```bash
# Delete all files in bucket
aws s3 rm s3://chili-cookoff-source-YOUR-NAME/ --recursive

# Delete the bucket
aws s3 rb s3://chili-cookoff-source-YOUR-NAME/
```

## Cost

Storing this project in S3 costs approximately:
- **Storage**: ~$0.001/month (project is ~5 MB)
- **Requests**: Negligible (only when deploying)

**Total**: Less than $0.01/month

## Tips

1. **Use a unique bucket name**: S3 bucket names must be globally unique
2. **Remember your bucket name**: Write it down or save it somewhere
3. **Keep bucket private**: Don't make it public (default is private)
4. **Update regularly**: Sync changes to S3 when you update the project
5. **Clean up**: Delete the bucket when you no longer need it

## Example Workflow

```bash
# From your computer (one-time):
aws s3 mb s3://chili-cookoff-source-jeremy
aws s3 sync . s3://chili-cookoff-source-jeremy/ --exclude ".git/*" --exclude "venv/*"

# From CloudShell (anytime):
aws s3 sync s3://chili-cookoff-source-jeremy/ ~/chili-cookoff/
cd ~/chili-cookoff && chmod +x deploy.sh && ./deploy.sh

# Check email for URLs and QR codes!
```
