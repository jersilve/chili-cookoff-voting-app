#!/bin/bash

# Quick Teardown Script for Chili Cook-Off Voting App
# This script removes all AWS resources with a single command

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
STACK_NAME="${STACK_NAME:-chili-cookoff-voting-app}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

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
echo "Chili Cook-Off Quick Teardown"
echo "========================================="
echo ""
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured"
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
    print_error "Stack '$STACK_NAME' does not exist"
    exit 1
fi

# Get stack status
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].StackStatus' \
    --output text)

print_info "Current stack status: $STACK_STATUS"

# Handle DELETE_FAILED state
if [ "$STACK_STATUS" = "DELETE_FAILED" ]; then
    print_info "Stack is in DELETE_FAILED state, attempting to delete with retain..."
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION" 2>/dev/null || \
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
else
    # Initiate stack deletion
    print_info "Initiating stack deletion..."
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
fi

print_success "Stack deletion initiated"

# Wait for deletion
print_info "Waiting for stack deletion to complete (this may take 3-5 minutes)..."

if ! aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region "$REGION" 2>&1; then
    
    print_error "Stack deletion encountered issues"
    
    # Show failure events
    print_info "Fetching failure details..."
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table 2>/dev/null || true
    
    echo ""
    print_info "You may need to manually delete some resources in the AWS Console"
    exit 1
fi

print_success "Stack deletion completed"

echo ""
echo "========================================="
print_success "Teardown completed successfully!"
echo "========================================="
echo ""
echo "All AWS resources have been removed"
echo ""
echo "To deploy again:"
echo "  ./quick-deploy.sh"
echo ""
