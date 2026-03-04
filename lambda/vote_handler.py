import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from security_utils import (
    validate_voter_id,
    validate_entry_name,
    validate_request_size,
    get_security_headers,
    sanitize_error_message
)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ChiliCookoffData')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Vote Handler Lambda function for Chili Cook-Off Voting Application.
    
    Processes ALB requests to submit ranked votes for chili entries.
    Validates vote data and stores in DynamoDB with point assignments.
    
    Args:
        event: ALB request event containing body with vote choices
        context: Lambda context object
        
    Returns:
        ALB-formatted response with success and vote ID
    """
    try:
        # Parse ALB request body
        body = event.get('body', '')
        if not body:
            return create_response(400, False, 'Request body is required')
        
        # Validate request size
        size_error = validate_request_size(body)
        if size_error:
            return create_response(400, False, size_error)
        
        # Parse JSON body
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return create_response(400, False, 'Invalid JSON format')
        
        # Extract vote choices and voter ID
        first_choice = data.get('first')
        second_choice = data.get('second')
        third_choice = data.get('third')
        voter_id = data.get('voterId')
        
        # Validate voter ID
        voter_id_error = validate_voter_id(voter_id)
        if voter_id_error:
            return create_response(400, False, voter_id_error)
        
        # Validate vote data
        validation_error = validate_vote(first_choice, second_choice, third_choice)
        if validation_error:
            return create_response(400, False, validation_error)
        
        # Check if voter has already voted (to determine if this is an update)
        existing_vote = get_vote_by_voter_id(voter_id)
        is_update = existing_vote is not None
        
        # Store or update vote in DynamoDB
        store_vote(voter_id, first_choice, second_choice, third_choice)
        
        # Return success response
        message = 'Vote updated successfully' if is_update else 'Vote submitted successfully'
        return create_response(200, True, message, voter_id, is_update)
        
    except Exception as e:
        # Handle unexpected errors - don't expose internal details
        print(f'Error in vote_handler: {str(e)}')
        return create_response(500, False, sanitize_error_message(e))


def validate_vote(first_choice, second_choice, third_choice):
    """
    Validate vote data according to requirements.
    
    Args:
        first_choice: First choice entry name
        second_choice: Second choice entry name
        third_choice: Third choice entry name
        
    Returns:
        Error message string if validation fails, None if valid
    """
    # Check that all three choices are provided
    if not first_choice:
        return 'First choice is required'
    if not second_choice:
        return 'Second choice is required'
    if not third_choice:
        return 'Third choice is required'
    
    # Validate entry names
    for choice, name in [(first_choice, 'First choice'), (second_choice, 'Second choice'), (third_choice, 'Third choice')]:
        error = validate_entry_name(choice)
        if error:
            return f'{name}: {error}'
    
    # Check that all three choices are unique
    choices = [first_choice, second_choice, third_choice]
    if len(choices) != len(set(choices)):
        return 'Must select exactly 3 different entries'
    
    # Check that all choices exist in DynamoDB
    try:
        for choice in choices:
            response = table.get_item(
                Key={
                    'EntityType': 'ENTRY',
                    'EntityId': choice
                }
            )
            
            if 'Item' not in response:
                return 'One or more selected entries not found'
    
    except Exception as e:
        print(f'Error validating entries in DynamoDB: {str(e)}')
        raise
    
    return None


def get_vote_by_voter_id(voter_id):
    """
    Check if a voter has already voted.
    
    Args:
        voter_id: Voter ID string
        
    Returns:
        Vote item if found, None otherwise
    """
    try:
        response = table.get_item(
            Key={
                'EntityType': 'VOTE',
                'EntityId': voter_id
            }
        )
        return response.get('Item')
    except Exception as e:
        print(f'Error checking existing vote: {str(e)}')
        return None


def store_vote(voter_id, first_choice, second_choice, third_choice):
    """
    Store vote in DynamoDB using voter ID as the EntityId.
    
    Args:
        voter_id: Voter ID string
        first_choice: First choice entry name (3 points)
        second_choice: Second choice entry name (2 points)
        third_choice: Third choice entry name (1 point)
    """
    try:
        from datetime import datetime
        
        # Store vote with EntityType=VOTE, using voter_id as EntityId
        table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': voter_id,
                'FirstChoice': first_choice,
                'SecondChoice': second_choice,
                'ThirdChoice': third_choice,
                'Timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        )
    
    except Exception as e:
        print(f'Error storing vote: {str(e)}')
        raise


def create_response(status_code, success, message, voter_id=None, updated=False):
    """
    Create ALB-formatted response with security headers.
    
    Args:
        status_code: HTTP status code
        success: Boolean indicating success/failure
        message: Message to include in response
        voter_id: Optional voter ID to include in response
        updated: Boolean indicating if this was an update
        
    Returns:
        ALB-formatted response dictionary
    """
    response_body = {
        'success': success,
        'message': message
    }
    
    if voter_id:
        response_body['voterId'] = voter_id
    
    if updated:
        response_body['updated'] = True
    
    return {
        'statusCode': status_code,
        'headers': get_security_headers(),
        'body': json.dumps(response_body)
    }
