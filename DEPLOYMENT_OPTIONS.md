# Deployment Options Summary

This document summarizes all the ways you can deploy the Chili Cook-Off Voting App.

## Option 1: Local Deployment (Traditional)

**Best for**: Running from your computer

**Requirements**:
- AWS CLI installed and configured
- Python 3 with pip
- Local copy of the project

**Steps**:
```bash
./deploy.sh
```

**Pros**:
- Fastest deployment
- Full control
- Easy to troubleshoot

**Cons**:
- Requires local setup
- Can't deploy from phone

---

## Option 2: CloudShell Deployment (Recommended for Mobile)

**Best for**: Deploying from anywhere, including your phone

**Requirements**:
- AWS account
- Web browser
- Project uploaded to S3 (one-time setup)

**One-Time Setup** (from computer):
```bash
./upload-to-s3.sh
```

**Deploy** (from CloudShell on any device):
```bash
aws s3 cp s3://YOUR-BUCKET/quick-deploy.sh .
chmod +x quick-deploy.sh
./quick-deploy.sh
./deploy.sh
```

**Pros**:
- Deploy from anywhere (phone, tablet, any browser)
- No local setup needed
- AWS CLI pre-configured
- Free to use

**Cons**:
- Requires one-time S3 upload
- Session timeout after 20 minutes of inactivity

---

## Option 3: AWS Console Manual Deployment

**Best for**: Understanding the infrastructure

**Requirements**:
- AWS account
- Lambda function code uploaded to S3

**Steps**:
1. Upload Lambda packages to S3
2. Create CloudFormation stack via Console
3. Upload template.yaml
4. Wait for stack creation
5. Update Lambda function code

**Pros**:
- Visual interface
- Step-by-step control
- Good for learning

**Cons**:
- Most time-consuming
- Manual steps required
- No automation

---

## Comparison Table

| Feature | Local | CloudShell | Console |
|---------|-------|------------|---------|
| **Speed** | ⚡⚡⚡ Fast | ⚡⚡ Medium | ⚡ Slow |
| **Mobile-Friendly** | ❌ No | ✅ Yes | ⚠️ Limited |
| **Setup Required** | ✅ Yes | ⚠️ One-time | ❌ No |
| **Automation** | ✅ Full | ✅ Full | ❌ Manual |
| **Cost** | Free | Free | Free |
| **Email Notification** | ✅ Yes | ✅ Yes | ⚠️ Manual |
| **QR Code Generation** | ✅ Yes | ✅ Yes | ❌ No |

---

## Recommended Workflow

### For First-Time Users
1. Deploy locally to understand the process
2. Upload to S3 for future mobile deployments
3. Use CloudShell for subsequent deployments

### For Regular Users
1. One-time: Upload project to S3
2. Anytime: Deploy from CloudShell (even from phone)
3. After event: Teardown from CloudShell

### For Learning/Development
1. Deploy locally for quick iterations
2. Test changes locally
3. Upload to S3 when ready for production

---

## Email Notifications

All deployment methods automatically send an email to `jeremy.r.silverman@gmail.com` with:
- Setup page URL and QR code
- Voting page URL and QR code
- Leaderboard page URL and QR code
- Next steps for running your event

This means you can deploy from anywhere and immediately have everything you need!

---

## Quick Reference

### Local Deployment
```bash
./deploy.sh
```

### CloudShell Deployment
```bash
# One-time setup (from computer)
./upload-to-s3.sh

# Deploy (from CloudShell)
aws s3 cp s3://YOUR-BUCKET/quick-deploy.sh . && chmod +x quick-deploy.sh && ./quick-deploy.sh && ./deploy.sh
```

### Teardown (Any Method)
```bash
./teardown.sh
```

---

## Cost Comparison

| Method | Setup Cost | Deployment Cost | Storage Cost |
|--------|-----------|-----------------|--------------|
| Local | $0 | ~$1-2/event | $0 |
| CloudShell | $0 | ~$1-2/event | ~$0.001/month (S3) |
| Console | $0 | ~$1-2/event | Varies |

**Note**: The deployment cost is the same for all methods - it's the cost of running the AWS resources (ALB, Lambda, DynamoDB).

---

## Troubleshooting

### Local Deployment Issues
- Check AWS CLI installation: `aws --version`
- Check credentials: `aws sts get-caller-identity`
- Check Python: `python3 --version`

### CloudShell Issues
- Session timeout: Reconnect and check stack status
- Region not supported: Switch to supported region
- Permission denied: Run `chmod +x deploy.sh`

### Email Not Received
- Check spam folder
- Verify SES email: `aws ses list-verified-email-addresses --region us-east-1`
- Check CloudWatch Logs: `aws logs tail /aws/lambda/ChiliCookoffDeploymentNotifier --follow`

---

## Next Steps

1. **Choose your deployment method** based on your needs
2. **Follow the appropriate guide**:
   - Local: See main README.md
   - CloudShell: See CLOUDSHELL_DEPLOY.md
   - S3 Upload: See S3_UPLOAD_COMMANDS.md
3. **Deploy and check your email** for URLs and QR codes
4. **Run your event** and have fun!
5. **Teardown after the event** to avoid charges

Happy cooking! 🌶️
