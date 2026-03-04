"""
Lambda function to automate teardown of the Chili Cook-Off application.
This function can be invoked via a Lambda Function URL to trigger teardown.
"""

import json
import boto3
import time
from datetime import datetime

# AWS clients
cloudformation = boto3.client('cloudformation')
s3 = boto3.client('s3')

# Configuration
STACK_NAME = "chili-cookoff-voting-app"
REGION = boto3.session.Session().region_name


def lambda_handler(event, context):
    """
    Main handler for teardown Lambda function.
    
    This function:
    1. Checks if the stack exists
    2. Initiates stack deletion
    3. Waits for deletion to complete
    4. Cleans up S3 bucket
    5. Returns teardown status
    """
    
    try:
        # Check if stack exists
        if not stack_exists(STACK_NAME):
            return create_response(404, False, 
                f"Stack '{STACK_NAME}' does not exist. Nothing to teardown.",
                None)
        
        # Get stack status
        stack_info = cloudformation.describe_stacks(StackName=STACK_NAME)
        current_status = stack_info['Stacks'][0]['StackStatus']
        
        print(f"Current stack status: {current_status}")
        
        # Check if stack is already being deleted
        if current_status in ['DELETE_IN_PROGRESS', 'DELETE_COMPLETE']:
            return create_response(200, True, 
                f"Stack is already being deleted (status: {current_status})",
                {'status': current_status})
        
        # Check if stack is in a failed state
        if current_status == 'DELETE_FAILED':
            print("Stack is in DELETE_FAILED state, attempting to delete with retain")
            # Try to delete with retaining problematic resources
            try:
                cloudformation.delete_stack(
                    StackName=STACK_NAME,
                    RetainResources=['DeploymentNotification']  # Retain custom resource if it exists
                )
            except Exception as e:
                # If that fails, try regular delete
                cloudformation.delete_stack(StackName=STACK_NAME)
        else:
            # Initiate stack deletion
            print(f"Initiating deletion of stack: {STACK_NAME}")
            cloudformation.delete_stack(StackName=STACK_NAME)
        
        print("Stack deletion initiated, waiting for completion...")
        
        # Wait for stack deletion (with timeout)
        waiter = cloudformation.get_waiter('stack_delete_complete')
        waiter.wait(
            StackName=STACK_NAME,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 20  # 10 minutes max
            }
        )
        
        print("Stack deletion completed successfully")
        
        # Clean up S3 bucket
        s3_bucket = f"chili-cookoff-lambda-packages-{REGION}"
        cleanup_s3_bucket(s3_bucket)
        
        print("Teardown completed successfully")
        
        return create_response(200, True, 
            "Teardown completed successfully! All resources have been removed.",
            {
                'stackName': STACK_NAME,
                's3Bucket': s3_bucket,
                'status': 'deleted'
            })
        
    except cloudformation.exceptions.ClientError as e:
        error_msg = str(e)
        print(f"CloudFormation error: {error_msg}")
        return create_response(500, False, f"CloudFormation error: {error_msg}", None)
        
    except Exception as e:
        error_msg = str(e)
        print(f"Teardown error: {error_msg}")
        return create_response(500, False, f"Teardown failed: {error_msg}", None)


def stack_exists(stack_name):
    """Check if CloudFormation stack exists."""
    try:
        cloudformation.describe_stacks(StackName=stack_name)
        return True
    except cloudformation.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return False
        raise


def cleanup_s3_bucket(bucket_name):
    """Delete all objects in S3 bucket and then delete the bucket."""
    try:
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
        except:
            print(f"S3 bucket {bucket_name} does not exist, skipping cleanup")
            return
        
        print(f"Cleaning up S3 bucket: {bucket_name}")
        
        # Delete all objects in bucket
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        objects_to_delete = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
        
        if objects_to_delete:
            # Delete objects in batches of 1000
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': batch}
                )
            print(f"Deleted {len(objects_to_delete)} objects from bucket")
        
        # Delete the bucket
        s3.delete_bucket(Bucket=bucket_name)
        print(f"Deleted S3 bucket: {bucket_name}")
        
    except Exception as e:
        print(f"Warning: Failed to cleanup S3 bucket: {str(e)}")
        # Don't fail the entire teardown if S3 cleanup fails


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
