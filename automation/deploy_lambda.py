"""
Lambda function to automate deployment of the Chili Cook-Off application.
This function can be invoked via a Lambda Function URL to trigger deployment.
"""

import json
import boto3
import subprocess
import os
import tempfile
import shutil
from datetime import datetime

# AWS clients
s3 = boto3.client('s3')
cloudformation = boto3.client('cloudformation')
lambda_client = boto3.client('lambda')

# Configuration
STACK_NAME = "chili-cookoff-voting-app"
TEMPLATE_S3_BUCKET = os.environ.get('TEMPLATE_S3_BUCKET')
TEMPLATE_S3_KEY = "infrastructure/template.yaml"
REGION = os.environ.get('AWS_REGION', 'us-east-1')


def lambda_handler(event, context):
    """
    Main handler for deployment Lambda function.
    
    This function:
    1. Downloads the CloudFormation template from S3
    2. Creates the CloudFormation stack
    3. Waits for stack creation to complete
    4. Updates Lambda functions with deployment code
    5. Returns deployment status and URLs
    """
    
    try:
        # Check if stack already exists
        if stack_exists(STACK_NAME):
            return create_response(400, False, 
                f"Stack '{STACK_NAME}' already exists. Please teardown first.",
                None)
        
        # Create the CloudFormation stack
        print(f"Creating CloudFormation stack: {STACK_NAME}")
        
        # Download template from S3
        template_body = download_template()
        
        # Create stack
        cloudformation.create_stack(
            StackName=STACK_NAME,
            TemplateBody=template_body,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        
        print("Stack creation initiated, waiting for completion...")
        
        # Wait for stack creation (with timeout)
        waiter = cloudformation.get_waiter('stack_create_complete')
        waiter.wait(
            StackName=STACK_NAME,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 20  # 10 minutes max
            }
        )
        
        print("Stack creation completed successfully")
        
        # Get stack outputs
        stack_info = cloudformation.describe_stacks(StackName=STACK_NAME)
        outputs = stack_info['Stacks'][0].get('Outputs', [])
        
        alb_url = None
        for output in outputs:
            if output['OutputKey'] == 'ALBURL':
                alb_url = output['OutputValue']
                break
        
        if not alb_url:
            return create_response(500, False, 
                "Stack created but ALB URL not found in outputs",
                None)
        
        # Update Lambda functions with code from S3
        print("Updating Lambda functions...")
        update_lambda_functions()
        
        # Update Lambda environment variables with ALB URL
        update_lambda_env_vars(alb_url)
        
        print(f"Deployment completed successfully! ALB URL: {alb_url}")
        
        # Return success with URLs
        return create_response(200, True, 
            "Deployment completed successfully!",
            {
                'albUrl': alb_url,
                'setupUrl': f"{alb_url}/static/setup.html",
                'votingUrl': f"{alb_url}/static/vote.html",
                'leaderboardUrl': f"{alb_url}/static/leaderboard.html"
            })
        
    except cloudformation.exceptions.ClientError as e:
        error_msg = str(e)
        print(f"CloudFormation error: {error_msg}")
        return create_response(500, False, f"CloudFormation error: {error_msg}", None)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Deployment error: {error_msg}")
        return create_response(500, False, f"Deployment failed: {error_msg}", None)


def stack_exists(stack_name):
    """Check if CloudFormation stack exists."""
    try:
        cloudformation.describe_stacks(StackName=stack_name)
        return True
    except cloudformation.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return False
        raise


def download_template():
    """Download CloudFormation template from S3."""
    try:
        response = s3.get_object(
            Bucket=TEMPLATE_S3_BUCKET,
            Key=TEMPLATE_S3_KEY
        )
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to download template from S3: {str(e)}")


def update_lambda_functions():
    """Update Lambda functions with code from S3."""
    s3_bucket = f"chili-cookoff-lambda-packages-{REGION}"
    
    functions = [
        ('ChiliCookoffSetupHandler', 'setup_handler.zip'),
        ('ChiliCookoffVoteHandler', 'vote_handler.zip'),
        ('ChiliCookoffLeaderboardHandler', 'leaderboard_handler.zip'),
        ('ChiliCookoffStaticHandler', 'static_handler.zip')
    ]
    
    for function_name, zip_file in functions:
        try:
            lambda_client.update_function_code(
                FunctionName=function_name,
                S3Bucket=s3_bucket,
                S3Key=zip_file
            )
            print(f"Updated Lambda function: {function_name}")
        except Exception as e:
            print(f"Warning: Failed to update {function_name}: {str(e)}")


def update_lambda_env_vars(alb_url):
    """Update Lambda environment variables with ALB URL."""
    try:
        lambda_client.update_function_configuration(
            FunctionName='ChiliCookoffSetupHandler',
            Environment={
                'Variables': {
                    'TABLE_NAME': 'ChiliCookoffData',
                    'ALB_URL': alb_url
                }
            }
        )
        print("Updated Lambda environment variables")
    except Exception as e:
        print(f"Warning: Failed to update environment variables: {str(e)}")


def create_response(status_code, success, message, data):
    """Create Lambda Function URL response."""
    body = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if data:
        body['data'] = data
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, indent=2)
    }
