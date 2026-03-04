import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from security_utils import get_security_headers, validate_entry_name, validate_request_size, sanitize_error_message

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ChiliCookoffData')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Setup Handler Lambda function for Chili Cook-Off Voting Application.
    
    Processes ALB requests to configure competition entries.
    Validates entry data and stores in DynamoDB.
    
    Args:
        event: ALB request event containing body with entry list
        context: Lambda context object
        
    Returns:
        ALB-formatted response with success/error message
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
        
        # Extract entry list and event title
        entries = data.get('entries', [])
        event_title = data.get('eventTitle', '')
        
        # Validate event title
        if not event_title or not event_title.strip():
            return create_response(400, False, 'Event title is required')
        
        if len(event_title.strip()) > 100:
            return create_response(400, False, 'Event title must be 100 characters or less')
        
        # Validate entry data
        validation_error = validate_entries(entries)
        if validation_error:
            return create_response(400, False, validation_error)
        
        # Clear existing ENTRY and CONFIG records from DynamoDB
        clear_existing_entries()
        clear_existing_config()
        
        # Clear all existing VOTE records (reset votes)
        clear_existing_votes()
        
        # Store event title as config
        store_event_title(event_title.strip())
        
        # Store new entries
        store_entries(entries)
        
        # Return success response
        return create_response(200, True, f'Successfully configured {len(entries)} entries')
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = sanitize_error_message(e)
        return create_response(500, False, error_msg)


def validate_entries(entries):
    """
    Validate entry data according to requirements.
    
    Args:
        entries: List of entry names
        
    Returns:
        Error message string if validation fails, None if valid
    """
    # Check if entries is a list
    if not isinstance(entries, list):
        return 'Entries must be a list'
    
    # Check entry count (1-50)
    if len(entries) < 1:
        return 'At least one entry is required'
    
    if len(entries) > 50:
        return 'Maximum 50 entries allowed'
    
    # Check for non-empty names and validate each entry
    for i, entry in enumerate(entries):
        if not isinstance(entry, str):
            return f'Entry at position {i+1} must be a string'
        
        if not entry.strip():
            return f'Entry at position {i+1} cannot be empty'
        
        # Validate entry name using security utils
        validation_error = validate_entry_name(entry.strip())
        if validation_error:
            return f'Entry at position {i+1}: {validation_error}'
    
    # Check for unique names
    entry_names = [entry.strip() for entry in entries]
    if len(entry_names) != len(set(entry_names)):
        return 'Entry names must be unique'
    
    return None


def clear_existing_entries():
    """
    Clear all existing ENTRY records from DynamoDB.
    Uses Scan to find all entries, then BatchWriteItem to delete them.
    """
    try:
        # Scan for all ENTRY records
        response = table.scan(
            FilterExpression=Key('EntityType').eq('ENTRY')
        )
        
        items = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('ENTRY'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        # Delete items in batches (max 25 per batch)
        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={
                            'EntityType': item['EntityType'],
                            'EntityId': item['EntityId']
                        }
                    )
    
    except Exception as e:
        print(f'Error clearing existing entries: {str(e)}')
        raise


def clear_existing_config():
    """
    Clear all existing CONFIG records from DynamoDB.
    """
    try:
        # Scan for all CONFIG records
        response = table.scan(
            FilterExpression=Key('EntityType').eq('CONFIG')
        )
        
        items = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('CONFIG'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        # Delete items in batches
        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={
                            'EntityType': item['EntityType'],
                            'EntityId': item['EntityId']
                        }
                    )
    
    except Exception as e:
        print(f'Error clearing existing config: {str(e)}')
        raise


def clear_existing_votes():
    """
    Clear all existing VOTE records from DynamoDB.
    This is called when resetting the event to start fresh.
    """
    try:
        # Scan for all VOTE records
        response = table.scan(
            FilterExpression=Key('EntityType').eq('VOTE')
        )
        
        items = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('VOTE'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        # Delete items in batches
        if items:
            with table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={
                            'EntityType': item['EntityType'],
                            'EntityId': item['EntityId']
                        }
                    )
    
    except Exception as e:
        print(f'Error clearing existing votes: {str(e)}')
        raise


def store_event_title(event_title):
    """
    Store event title in DynamoDB as a CONFIG record.
    
    Args:
        event_title: Event title string
    """
    try:
        from datetime import datetime
        
        table.put_item(
            Item={
                'EntityType': 'CONFIG',
                'EntityId': 'event_title',
                'Value': event_title,
                'UpdatedAt': datetime.utcnow().isoformat() + 'Z'
            }
        )
    
    except Exception as e:
        print(f'Error storing event title: {str(e)}')
        raise


def store_entries(entries):
    """
    Store new entries in DynamoDB.
    
    Args:
        entries: List of entry names to store
    """
    try:
        from datetime import datetime
        
        # Store entries using batch writer for efficiency
        with table.batch_writer() as batch:
            for entry_name in entries:
                batch.put_item(
                    Item={
                        'EntityType': 'ENTRY',
                        'EntityId': entry_name.strip(),
                        'CreatedAt': datetime.utcnow().isoformat() + 'Z'
                    }
                )
    
    except Exception as e:
        print(f'Error storing entries: {str(e)}')
        raise


def create_response(status_code, success, message):
    """
    Create ALB-formatted response with security headers.
    
    Args:
        status_code: HTTP status code
        success: Boolean indicating success/failure
        message: Message to include in response
        
    Returns:
        ALB-formatted response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': get_security_headers(),
        'body': json.dumps({
            'success': success,
            'message': message
        })
    }

