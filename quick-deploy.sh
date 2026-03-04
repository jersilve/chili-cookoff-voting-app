#!/bin/bash

# Quick Deploy Script for Chili Cook-Off Voting App
# This script deploys the application directly from GitHub with a single command

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
STACK_NAME="${STACK_NAME:-chili-cookoff-voting-app}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
GITHUB_REPO="jersilve/chili-cookoff-voting-app"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

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
echo "Chili Cook-Off Quick Deploy"
echo "========================================="
echo ""
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "GitHub: $GITHUB_REPO @ $GITHUB_BRANCH"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure'."
    exit 1
fi

print_success "AWS CLI and credentials validated"

# Check if stack already exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
    print_error "Stack '$STACK_NAME' already exists."
    echo ""
    echo "To teardown the existing stack, run:"
    echo "  ./quick-teardown.sh"
    echo ""
    echo "Or use a different stack name:"
    echo "  STACK_NAME=my-chili-app ./quick-deploy.sh"
    exit 1
fi

# Deploy CloudFormation stack
print_info "Deploying CloudFormation stack from GitHub..."

TEMPLATE_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/infrastructure/template.yaml"

aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-url "$TEMPLATE_URL" \
    --parameters \
        "ParameterKey=GitHubRepo,ParameterValue=${GITHUB_REPO}" \
        "ParameterKey=GitHubBranch,ParameterValue=${GITHUB_BRANCH}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" > /dev/null

print_success "Stack creation initiated"

# Wait for stack creation
print_info "Waiting for stack creation to complete (this may take 5-10 minutes)..."

if ! aws cloudformation wait stack-create-complete \
    --stack-name "$STACK_NAME" \
    --region "$REGION" 2>&1; then
    
    print_error "Stack creation failed"
    
    # Show failure events
    print_info "Fetching failure details..."
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table
    
    exit 1
fi

print_success "Stack creation completed"

# Get ALB URL
print_info "Retrieving application URL..."

ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBURL`].OutputValue' \
    --output text)

if [ -z "$ALB_URL" ]; then
    print_error "Failed to retrieve ALB URL"
    exit 1
fi

echo ""
echo "========================================="
print_success "Deployment completed successfully!"
echo "========================================="
echo ""
echo "Application URL: ${ALB_URL}"
echo ""
echo "Available endpoints:"
echo "  - Setup:       ${ALB_URL}/static/setup.html"
echo "  - Voting:      ${ALB_URL}/static/vote.html"
echo "  - Leaderboard: ${ALB_URL}/static/leaderboard.html"
echo ""
echo "API endpoints:"
echo "  - Setup API:       ${ALB_URL}/api/setup"
echo "  - Vote API:        ${ALB_URL}/api/vote"
echo "  - Leaderboard API: ${ALB_URL}/api/leaderboard"
echo ""
echo "To teardown when finished:"
echo "  ./quick-teardown.sh"
echo ""
echo "Or with custom stack name:"
echo "  STACK_NAME=$STACK_NAME ./quick-teardown.sh"
echo ""
