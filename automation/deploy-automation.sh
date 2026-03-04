#!/bin/bash

# Deploy the automation infrastructure (Deploy and Teardown Lambda functions)

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AUTOMATION_STACK_NAME="chili-cookoff-automation"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
SOURCE_BUCKET="chili-cookoff-automation-source-${REGION}"

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

echo "========================================="
echo "Chili Cook-Off Automation Setup"
echo "========================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found"
    exit 1
fi

# Create S3 bucket for source code
print_info "Creating S3 bucket for source code..."
if aws s3 ls "s3://${SOURCE_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
    if [ "$REGION" = "us-east-1" ]; then
        aws s3 mb "s3://${SOURCE_BUCKET}"
    else
        aws s3 mb "s3://${SOURCE_BUCKET}" --region "$REGION"
    fi
    print_success "Created S3 bucket: ${SOURCE_BUCKET}"
else
    print_info "S3 bucket already exists: ${SOURCE_BUCKET}"
fi

# Upload CloudFormation template to S3
print_info "Uploading application CloudFormation template to S3..."
aws s3 cp ../infrastructure/template.yaml "s3://${SOURCE_BUCKET}/infrastructure/template.yaml"
print_success "Uploaded template to S3"

# Package Lambda functions
print_info "Packaging automation Lambda functions..."

# Package deploy lambda
cd "$(dirname "$0")"
zip -q deploy_lambda.zip deploy_lambda.py
zip -q teardown_lambda.zip teardown_lambda.py

print_success "Packaged Lambda functions"

# Deploy automation stack
print_info "Deploying automation CloudFormation stack..."

if aws cloudformation describe-stacks --stack-name "$AUTOMATION_STACK_NAME" --region "$REGION" &> /dev/null; then
    print_info "Stack exists, updating..."
    aws cloudformation update-stack \
        --stack-name "$AUTOMATION_STACK_NAME" \
        --template-body "file://automation-template.yaml" \
        --parameters "ParameterKey=SourceCodeBucket,ParameterValue=${SOURCE_BUCKET}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" || print_info "No updates needed"
else
    print_info "Creating new stack..."
    aws cloudformation create-stack \
        --stack-name "$AUTOMATION_STACK_NAME" \
        --template-body "file://automation-template.yaml" \
        --parameters "ParameterKey=SourceCodeBucket,ParameterValue=${SOURCE_BUCKET}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION"
    
    print_info "Waiting for stack creation..."
    aws cloudformation wait stack-create-complete \
        --stack-name "$AUTOMATION_STACK_NAME" \
        --region "$REGION"
fi

print_success "Automation stack deployed"

# Update Lambda function code
print_info "Updating Lambda function code..."

aws lambda update-function-code \
    --function-name ChiliCookoffDeployAutomation \
    --zip-file fileb://deploy_lambda.zip \
    --region "$REGION" > /dev/null

aws lambda update-function-code \
    --function-name ChiliCookoffTeardownAutomation \
    --zip-file fileb://teardown_lambda.zip \
    --region "$REGION" > /dev/null

print_success "Lambda functions updated"

# Clean up zip files
rm -f deploy_lambda.zip teardown_lambda.zip

# Get function URLs
print_info "Retrieving function URLs..."

DEPLOY_URL=$(aws cloudformation describe-stacks \
    --stack-name "$AUTOMATION_STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DeployFunctionUrl`].OutputValue' \
    --output text)

TEARDOWN_URL=$(aws cloudformation describe-stacks \
    --stack-name "$AUTOMATION_STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`TeardownFunctionUrl`].OutputValue' \
    --output text)

echo ""
echo "========================================="
print_success "Automation setup complete!"
echo "========================================="
echo ""
echo "Deploy URL (visit to deploy the app):"
echo "  ${DEPLOY_URL}"
echo ""
echo "Teardown URL (visit to teardown the app):"
echo "  ${TEARDOWN_URL}"
echo ""
echo "⚠️  IMPORTANT: These URLs are public!"
echo "Anyone with these URLs can deploy or teardown your application."
echo "Keep them private or add authentication if needed."
echo ""
