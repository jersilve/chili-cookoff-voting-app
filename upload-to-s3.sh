#!/bin/bash

# Upload Chili Cook-Off Project to S3
# This script uploads the project to S3 for CloudShell deployment

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure'."
    exit 1
fi

echo "========================================="
echo "Upload Chili Cook-Off Project to S3"
echo "========================================="
echo ""

# Prompt for bucket name
read -p "Enter a unique S3 bucket name (e.g., chili-cookoff-source-yourname): " BUCKET_NAME

if [ -z "$BUCKET_NAME" ]; then
    print_error "Bucket name cannot be empty"
    exit 1
fi

# Check if bucket exists
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    print_info "Creating S3 bucket: ${BUCKET_NAME}"
    
    # Create bucket
    REGION=$(aws configure get region)
    if [ "$REGION" = "us-east-1" ]; then
        aws s3 mb "s3://${BUCKET_NAME}" || {
            print_error "Failed to create S3 bucket"
            exit 1
        }
    else
        aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" || {
            print_error "Failed to create S3 bucket"
            exit 1
        }
    fi
    
    print_success "S3 bucket created"
else
    print_info "S3 bucket already exists: ${BUCKET_NAME}"
fi

# Upload project to S3
print_info "Uploading project to S3..."

aws s3 sync . "s3://${BUCKET_NAME}/" \
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
  --exclude ".DS_Store" || {
    print_error "Failed to upload project to S3"
    exit 1
}

print_success "Project uploaded to S3"

# Create quick-deploy script
print_info "Creating quick-deploy script..."

cat > /tmp/quick-deploy.sh << EOF
#!/bin/bash
echo "Downloading project from S3..."
aws s3 sync s3://${BUCKET_NAME}/ ~/chili-cookoff/
cd ~/chili-cookoff
chmod +x deploy.sh teardown.sh
echo ""
echo "Ready to deploy! Run: ./deploy.sh"
EOF

aws s3 cp /tmp/quick-deploy.sh "s3://${BUCKET_NAME}/" || {
    print_error "Failed to upload quick-deploy script"
    exit 1
}

rm /tmp/quick-deploy.sh

print_success "Quick-deploy script created"

echo ""
echo "========================================="
print_success "Upload completed successfully!"
echo "========================================="
echo ""
echo "Your project is now in S3: s3://${BUCKET_NAME}/"
echo ""
echo "To deploy from CloudShell:"
echo ""
echo "  1. Open AWS CloudShell in your browser"
echo "  2. Run these commands:"
echo ""
echo "     aws s3 cp s3://${BUCKET_NAME}/quick-deploy.sh ."
echo "     chmod +x quick-deploy.sh"
echo "     ./quick-deploy.sh"
echo "     ./deploy.sh"
echo ""
echo "  3. Check your email for URLs and QR codes!"
echo ""
echo "To update the project in S3 later, run this script again."
echo ""
