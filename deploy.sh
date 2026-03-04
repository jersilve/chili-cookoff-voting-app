#!/bin/bash

# Chili Cook-Off Voting Application Deployment Script
# This script deploys the application to AWS using CloudFormation

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="chili-cookoff-voting-app"
TEMPLATE_FILE="infrastructure/template.yaml"
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

# Create S3 bucket for Lambda packages if it doesn't exist
create_s3_bucket() {
    print_info "Checking S3 bucket for Lambda packages..."
    
    if aws s3 ls "s3://${S3_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
        print_info "Creating S3 bucket: ${S3_BUCKET}"
        
        # Create bucket (different command for us-east-1)
        if [ "$REGION" = "us-east-1" ]; then
            aws s3 mb "s3://${S3_BUCKET}" || {
                print_error "Failed to create S3 bucket"
                exit 1
            }
        else
            aws s3 mb "s3://${S3_BUCKET}" --region "$REGION" || {
                print_error "Failed to create S3 bucket"
                exit 1
            }
        fi
        
        print_success "S3 bucket created: ${S3_BUCKET}"
    else
        print_success "S3 bucket already exists: ${S3_BUCKET}"
    fi
}

# Package Lambda function
package_lambda() {
    local function_name=$1
    local handler_file=$2
    local zip_file=$3
    
    print_info "Packaging Lambda function: ${function_name}..."
    
    # Create temporary directory for packaging
    local temp_dir=$(mktemp -d)
    
    # Copy Lambda handler
    cp "lambda/${handler_file}" "${temp_dir}/"
    
    # Copy security_utils.py to all Lambda packages
    cp "lambda/security_utils.py" "${temp_dir}/"
    
    # Install Python dependencies if requirements file exists
    if [ "$function_name" = "setup" ] && [ -f "lambda/setup_requirements.txt" ]; then
        print_info "Installing Python dependencies for ${function_name}..."
        pip install -q -r lambda/setup_requirements.txt -t "${temp_dir}/" || {
            print_error "Failed to install dependencies for ${function_name}"
            rm -rf "${temp_dir}"
            exit 1
        }
    fi
    
    # Copy web files for static handler
    if [ "$function_name" = "static" ]; then
        mkdir -p "${temp_dir}/static"
        cp web/*.html "${temp_dir}/static/" 2>/dev/null || true
        cp web/*.css "${temp_dir}/static/" 2>/dev/null || true
        cp web/*.js "${temp_dir}/static/" 2>/dev/null || true
    fi
    
    # Create zip file
    cd "${temp_dir}"
    zip -q -r "${zip_file}" . || {
        print_error "Failed to create zip file for ${function_name}"
        rm -rf "${temp_dir}"
        exit 1
    }
    cd - > /dev/null
    
    # Move zip to current directory
    mv "${temp_dir}/${zip_file}" .
    
    # Clean up
    rm -rf "${temp_dir}"
    
    print_success "Packaged ${function_name}: ${zip_file}"
}

# Upload Lambda package to S3
upload_to_s3() {
    local zip_file=$1
    
    print_info "Uploading ${zip_file} to S3..."
    
    aws s3 cp "${zip_file}" "s3://${S3_BUCKET}/${zip_file}" || {
        print_error "Failed to upload ${zip_file} to S3"
        exit 1
    }
    
    print_success "Uploaded ${zip_file} to S3"
}

# Package all Lambda functions
package_all_lambdas() {
    print_info "Packaging all Lambda functions..."
    
    # Package each Lambda function
    package_lambda "setup" "setup_handler.py" "setup_handler.zip"
    package_lambda "vote" "vote_handler.py" "vote_handler.zip"
    package_lambda "leaderboard" "leaderboard_handler.py" "leaderboard_handler.zip"
    package_lambda "static" "static_handler.py" "static_handler.zip"
    
    print_success "All Lambda functions packaged"
}

# Upload all Lambda packages to S3
upload_all_packages() {
    print_info "Uploading all Lambda packages to S3..."
    
    upload_to_s3 "setup_handler.zip"
    upload_to_s3 "vote_handler.zip"
    upload_to_s3 "leaderboard_handler.zip"
    upload_to_s3 "static_handler.zip"
    
    print_success "All Lambda packages uploaded"
}

# Update Lambda function code from S3
update_lambda_code() {
    local function_name=$1
    local zip_file=$2
    
    print_info "Updating Lambda function code: ${function_name}..."
    
    aws lambda update-function-code \
        --function-name "${function_name}" \
        --s3-bucket "${S3_BUCKET}" \
        --s3-key "${zip_file}" \
        --region "$REGION" > /dev/null || {
        print_error "Failed to update Lambda function: ${function_name}"
        return 1
    }
    
    print_success "Updated Lambda function: ${function_name}"
}

# Deploy CloudFormation stack
deploy_stack() {
    print_info "Checking if stack exists..."
    
    # Check if stack already exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        print_error "Stack '${STACK_NAME}' already exists. Run teardown.sh first or use a different stack name."
        exit 1
    fi
    
    print_info "Deploying CloudFormation stack: ${STACK_NAME}..."
    
    # Create stack
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://${TEMPLATE_FILE}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" > /dev/null || {
        print_error "Failed to create CloudFormation stack"
        exit 1
    }
    
    print_success "CloudFormation stack creation initiated"
}

# Wait for stack creation to complete
wait_for_stack() {
    print_info "Waiting for stack creation to complete (this may take several minutes)..."
    
    # Wait for stack creation
    if ! aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION" 2>&1; then
        
        print_error "Stack creation failed"
        
        # Get stack events to show what failed
        print_info "Fetching stack events..."
        aws cloudformation describe-stack-events \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
            --output table
        
        exit 1
    fi
    
    print_success "Stack creation completed"
}

# Update Lambda functions with actual code
update_all_lambda_functions() {
    print_info "Updating Lambda functions with deployment packages..."
    
    update_lambda_code "ChiliCookoffSetupHandler" "setup_handler.zip"
    update_lambda_code "ChiliCookoffVoteHandler" "vote_handler.zip"
    update_lambda_code "ChiliCookoffLeaderboardHandler" "leaderboard_handler.zip"
    update_lambda_code "ChiliCookoffStaticHandler" "static_handler.zip"
    
    print_success "All Lambda functions updated"
}

# Update Lambda environment variables with ALB URL
update_lambda_env_vars() {
    local alb_url=$1
    
    print_info "Updating Lambda environment variables with ALB URL..."
    
    aws lambda update-function-configuration \
        --function-name "ChiliCookoffSetupHandler" \
        --environment "Variables={TABLE_NAME=ChiliCookoffData,ALB_URL=${alb_url}}" \
        --region "$REGION" > /dev/null || {
        print_error "Failed to update environment variables for ChiliCookoffSetupHandler"
        return 1
    }
    
    print_success "Lambda environment variables updated"
}

# Get ALB URL from stack outputs
get_alb_url() {
    print_info "Retrieving ALB URL from stack outputs..." >&2
    
    local alb_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ALBURL`].OutputValue' \
        --output text)
    
    if [ -z "$alb_url" ]; then
        print_error "Failed to retrieve ALB URL from stack outputs"
        exit 1
    fi
    
    echo "$alb_url"
}

# Clean up zip files
cleanup() {
    print_info "Cleaning up temporary files..."
    rm -f setup_handler.zip vote_handler.zip leaderboard_handler.zip static_handler.zip
    print_success "Cleanup complete"
}

# Generate QR codes for all URLs
generate_qr_codes() {
    local base_url=$1
    
    echo "========================================="
    echo "Generating QR Codes"
    echo "========================================="
    echo ""
    
    # Check if qrcode module is available
    if python3 -c "import qrcode" 2>/dev/null; then
        # Create qr-codes directory if it doesn't exist
        mkdir -p qr-codes
        
        # Generate QR codes using Python
        python3 << EOF
import qrcode
import sys

base_url = "${base_url}"

urls = {
    "setup": f"{base_url}/static/setup.html",
    "voting": f"{base_url}/static/vote.html",
    "leaderboard": f"{base_url}/static/leaderboard.html"
}

for name, url in urls.items():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr-codes/{name}_qr_code.png"
    img.save(filename)
    print(f"✓ Generated: {filename}")
    print(f"  URL: {url}")
    print()

print("All QR codes saved in ./qr-codes/ directory")
EOF
        
        if [ $? -eq 0 ]; then
            echo ""
            print_success "QR codes generated successfully!"
            echo ""
            echo "QR codes saved in: ./qr-codes/"
            echo "  - setup_qr_code.png (Setup page)"
            echo "  - voting_qr_code.png (Voting page)"
            echo "  - leaderboard_qr_code.png (Leaderboard page)"
            echo ""
        fi
    else
        print_info "QR code generation skipped (qrcode module not installed)"
        echo ""
        echo "To generate QR codes locally, install: pip install qrcode[pil]"
        echo ""
        echo "Or use online QR code generators with these URLs:"
        echo "  - Setup:       ${base_url}/static/setup.html"
        echo "  - Voting:      ${base_url}/static/vote.html"
        echo "  - Leaderboard: ${base_url}/static/leaderboard.html"
        echo ""
        echo "Recommended online QR code generator: https://www.qr-code-generator.com/"
        echo ""
    fi
}

# Main deployment flow
main() {
    echo "========================================="
    echo "Chili Cook-Off Voting App Deployment"
    echo "========================================="
    echo ""
    
    # Pre-deployment checks
    check_aws_cli
    check_aws_credentials
    
    # Create S3 bucket for Lambda packages
    create_s3_bucket
    
    # Package and upload Lambda functions
    package_all_lambdas
    upload_all_packages
    
    # Deploy CloudFormation stack
    deploy_stack
    wait_for_stack
    
    # Update Lambda functions with actual code
    update_all_lambda_functions
    
    # Get and display ALB URL
    alb_url=$(get_alb_url)
    
    # Update Lambda environment variables with ALB URL
    update_lambda_env_vars "${alb_url}"
    
    # Clean up
    cleanup
    
    echo ""
    echo "========================================="
    print_success "Deployment completed successfully!"
    echo "========================================="
    echo ""
    echo "Application URL: ${alb_url}"
    echo ""
    echo "Available endpoints:"
    echo "  - Setup:       ${alb_url}/static/setup.html"
    echo "  - Voting:      ${alb_url}/static/vote.html"
    echo "  - Leaderboard: ${alb_url}/static/leaderboard.html"
    echo ""
    echo "API endpoints:"
    echo "  - Setup API:       ${alb_url}/api/setup"
    echo "  - Vote API:        ${alb_url}/api/vote"
    echo "  - Leaderboard API: ${alb_url}/api/leaderboard"
    echo ""
    
    # Generate QR codes
    generate_qr_codes "${alb_url}"
}

# Run main function
main
