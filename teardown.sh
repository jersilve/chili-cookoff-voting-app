#!/bin/bash

# Chili Cook-Off Voting Application Teardown Script
# This script removes all AWS resources created by the deployment script

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="chili-cookoff-voting-app"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
S3_BUCKET_PREFIX="chili-cookoff-lambda-packages"
S3_BUCKET="${S3_BUCKET_PREFIX}-${REGION}"

# Function to print colored messages
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Check if AWS CLI is installed
check_aws_cli() {
    print_info "Checking for AWS CLI..."
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI."
        echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    print_success "AWS CLI found"
}

# Validate AWS credentials are configured
check_aws_credentials() {
    print_info "Validating AWS credentials..."
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure'."
        exit 1
    fi
    print_success "AWS credentials validated"
}

# Check if stack exists
check_stack_exists() {
    print_info "Checking if stack exists..."
    
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        print_warning "Stack '${STACK_NAME}' not found. Nothing to tear down."
        return 1
    fi
    
    print_success "Stack found: ${STACK_NAME}"
    return 0
}

# Delete CloudFormation stack
delete_stack() {
    print_info "Deleting CloudFormation stack: ${STACK_NAME}..."
    
    if ! aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION" 2>&1; then
        
        print_error "Failed to initiate stack deletion"
        exit 1
    fi
    
    print_success "Stack deletion initiated"
}

# Wait for stack deletion to complete
wait_for_stack_deletion() {
    print_info "Waiting for stack deletion to complete (this may take several minutes)..."
    
    # Wait for stack deletion with timeout
    local max_wait=1800  # 30 minutes
    local elapsed=0
    local interval=15
    
    while [ $elapsed -lt $max_wait ]; do
        # Check stack status
        local stack_status=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>&1)
        
        # If stack doesn't exist, deletion is complete
        if echo "$stack_status" | grep -q "does not exist"; then
            print_success "Stack deletion completed"
            return 0
        fi
        
        # Check for deletion failure
        if echo "$stack_status" | grep -q "DELETE_FAILED"; then
            print_error "Stack deletion failed"
            
            # Get failed resources
            print_info "Fetching failed resources..."
            aws cloudformation describe-stack-events \
                --stack-name "$STACK_NAME" \
                --region "$REGION" \
                --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[LogicalResourceId,ResourceType,ResourceStatusReason]' \
                --output table
            
            return 1
        fi
        
        # Still deleting, wait and check again
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    print_error "Stack deletion timed out after ${max_wait} seconds"
    return 1
}

# Verify all resources are removed
verify_resources_removed() {
    print_info "Verifying all resources have been removed..."
    
    # Check if stack still exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        print_error "Stack still exists. Some resources may not have been deleted."
        
        # List remaining resources
        print_info "Remaining resources:"
        aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]' \
            --output table
        
        return 1
    fi
    
    print_success "All stack resources have been removed"
    return 0
}

# Delete S3 bucket if empty
delete_s3_bucket() {
    print_info "Checking S3 bucket: ${S3_BUCKET}..."
    
    # Check if bucket exists
    if ! aws s3 ls "s3://${S3_BUCKET}" &> /dev/null; then
        print_info "S3 bucket does not exist or is not accessible"
        return 0
    fi
    
    # Check if bucket is empty
    local object_count=$(aws s3 ls "s3://${S3_BUCKET}" --recursive | wc -l)
    
    if [ "$object_count" -gt 0 ]; then
        print_warning "S3 bucket is not empty (${object_count} objects). Emptying bucket..."
        
        # Empty the bucket
        if ! aws s3 rm "s3://${S3_BUCKET}" --recursive 2>&1; then
            print_error "Failed to empty S3 bucket"
            return 1
        fi
        
        print_success "S3 bucket emptied"
    fi
    
    # Delete the bucket
    print_info "Deleting S3 bucket: ${S3_BUCKET}..."
    
    if ! aws s3 rb "s3://${S3_BUCKET}" 2>&1; then
        print_error "Failed to delete S3 bucket"
        return 1
    fi
    
    print_success "S3 bucket deleted: ${S3_BUCKET}"
    return 0
}

# Handle errors and report remaining resources
handle_errors() {
    local exit_code=$1
    
    if [ $exit_code -ne 0 ]; then
        echo ""
        print_error "Teardown encountered errors"
        echo ""
        echo "Remaining resources may include:"
        echo "  - CloudFormation stack: ${STACK_NAME}"
        echo "  - S3 bucket: ${S3_BUCKET}"
        echo "  - DynamoDB table: ChiliCookoffData"
        echo "  - Lambda functions: ChiliCookoff*Handler"
        echo "  - Application Load Balancer and related resources"
        echo ""
        echo "Please check the AWS Console and manually delete any remaining resources."
        echo "Region: ${REGION}"
        echo ""
        
        # Try to list stack resources if stack still exists
        if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
            print_info "Current stack resources:"
            aws cloudformation describe-stack-resources \
                --stack-name "$STACK_NAME" \
                --region "$REGION" \
                --query 'StackResources[].[LogicalResourceId,ResourceType,ResourceStatus]' \
                --output table 2>&1 || true
        fi
        
        exit 1
    fi
}

# Main teardown flow
main() {
    echo "========================================="
    echo "Chili Cook-Off Voting App Teardown"
    echo "========================================="
    echo ""
    
    # Pre-teardown checks
    check_aws_cli
    check_aws_credentials
    
    # Check if stack exists
    if ! check_stack_exists; then
        # Stack doesn't exist, but check for S3 bucket
        if aws s3 ls "s3://${S3_BUCKET}" &> /dev/null; then
            print_info "Stack not found, but S3 bucket exists. Attempting to delete S3 bucket..."
            delete_s3_bucket || print_warning "Failed to delete S3 bucket"
        fi
        
        echo ""
        print_success "No resources to tear down"
        exit 0
    fi
    
    # Delete CloudFormation stack
    delete_stack
    
    # Wait for deletion to complete
    if ! wait_for_stack_deletion; then
        handle_errors 1
    fi
    
    # Verify all resources are removed
    if ! verify_resources_removed; then
        handle_errors 1
    fi
    
    # Delete S3 bucket
    if ! delete_s3_bucket; then
        print_warning "Failed to delete S3 bucket, but stack resources were removed"
    fi
    
    echo ""
    echo "========================================="
    print_success "Teardown completed successfully!"
    echo "========================================="
    echo ""
    print_success "All AWS resources have been removed"
    echo ""
    echo "Removed resources:"
    echo "  ✓ CloudFormation stack: ${STACK_NAME}"
    echo "  ✓ DynamoDB table"
    echo "  ✓ Lambda functions"
    echo "  ✓ Application Load Balancer"
    echo "  ✓ IAM roles and policies"
    echo "  ✓ S3 bucket: ${S3_BUCKET}"
    echo ""
}

# Run main function
main
