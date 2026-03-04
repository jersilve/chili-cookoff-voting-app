import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from security_utils import get_security_headers, sanitize_error_message

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ChiliCookoffData')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Leaderboard Handler Lambda function for Chili Cook-Off Voting Application.
    
    Processes ALB requests to retrieve current rankings.
    Scans DynamoDB for all votes, aggregates points, and returns sorted rankings.
    
    Args:
        event: ALB request event
        context: Lambda context object
        
    Returns:
        ALB-formatted response with rankings array and timestamp
    """
    try:
        # Get event title
        event_title = get_event_title()
        
        # Get all configured entries
        all_entries = get_all_entries()
        
        # Scan DynamoDB for all VOTE records
        votes = get_all_votes()
        
        # Aggregate points by entry
        entry_points = aggregate_points(votes)
        
        # Ensure all entries are included, even those with 0 points
        for entry in all_entries:
            if entry not in entry_points:
                entry_points[entry] = 0
        
        # Sort entries by total points descending
        rankings = sort_rankings(entry_points)
        
        # Create response with rankings, event title, and timestamp
        return create_response(200, rankings, event_title)
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = sanitize_error_message(e)
        return create_response(500, [], None, error=True, error_msg=error_msg)


def get_event_title():
    """
    Get event title from DynamoDB CONFIG records.
    
    Returns:
        Event title string, or default value if not found
    """
    try:
        response = table.get_item(
            Key={
                'EntityType': 'CONFIG',
                'EntityId': 'event_title'
            }
        )
        
        item = response.get('Item')
        if item:
            return item.get('Value', 'Chili Cook-Off')
        
        return 'Chili Cook-Off'
    
    except Exception as e:
        print(f'Error getting event title: {str(e)}')
        return 'Chili Cook-Off'


def get_all_votes():
    """
    Scan DynamoDB for all VOTE records.
    
    Returns:
        List of vote items from DynamoDB
    """
    try:
        votes = []
        
        # Scan for all VOTE records
        response = table.scan(
            FilterExpression=Key('EntityType').eq('VOTE')
        )
        
        votes.extend(response.get('Items', []))
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('VOTE'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            votes.extend(response.get('Items', []))
        
        return votes
    
    except Exception as e:
        print(f'Error scanning votes: {str(e)}')
        raise


def get_all_entries():
    """
    Scan DynamoDB for all ENTRY records.
    
    Returns:
        List of entry names from DynamoDB
    """
    try:
        entries = []
        
        # Scan for all ENTRY records
        response = table.scan(
            FilterExpression=Key('EntityType').eq('ENTRY')
        )
        
        # Extract entry names (EntityId)
        entries.extend([item['EntityId'] for item in response.get('Items', [])])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('ENTRY'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            entries.extend([item['EntityId'] for item in response.get('Items', [])])
        
        return entries
    
    except Exception as e:
        print(f'Error scanning entries: {str(e)}')
        raise


def aggregate_points(votes):
    """
    Aggregate points by entry from all votes.
    
    Point assignments:
    - FirstChoice: 3 points
    - SecondChoice: 2 points
    - ThirdChoice: 1 point
    
    Args:
        votes: List of vote items from DynamoDB
        
    Returns:
        Dictionary mapping entry names to total points
    """
    entry_points = {}
    
    for vote in votes:
        # Add 3 points for FirstChoice
        first_choice = vote.get('FirstChoice')
        if first_choice:
            entry_points[first_choice] = entry_points.get(first_choice, 0) + 3
        
        # Add 2 points for SecondChoice
        second_choice = vote.get('SecondChoice')
        if second_choice:
            entry_points[second_choice] = entry_points.get(second_choice, 0) + 2
        
        # Add 1 point for ThirdChoice
        third_choice = vote.get('ThirdChoice')
        if third_choice:
            entry_points[third_choice] = entry_points.get(third_choice, 0) + 1
    
    return entry_points


def sort_rankings(entry_points):
    """
    Sort entries by total points descending.
    
    Args:
        entry_points: Dictionary mapping entry names to total points
        
    Returns:
        List of dictionaries with 'entry' and 'points' keys, sorted by points descending
    """
    # Convert dictionary to list of ranking objects
    rankings = [
        {'entry': entry, 'points': points}
        for entry, points in entry_points.items()
    ]
    
    # Sort by points descending
    rankings.sort(key=lambda x: x['points'], reverse=True)
    
    return rankings


def create_response(status_code, rankings, event_title=None, error=False, error_msg=None):
    """
    Create ALB-formatted response with rankings, event title, voter count, timestamp, and security headers.
    
    Args:
        status_code: HTTP status code
        rankings: List of ranking dictionaries
        event_title: Event title string
        error: Boolean indicating if this is an error response
        error_msg: Optional error message
        
    Returns:
        ALB-formatted response dictionary
    """
    # Count total unique voters
    total_voters = count_total_voters()
    
    response_body = {
        'rankings': rankings,
        'totalVoters': total_voters,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if event_title:
        response_body['eventTitle'] = event_title
    
    if error:
        response_body['error'] = error_msg if error_msg else 'An error occurred processing your request'
    
    return {
        'statusCode': status_code,
        'headers': get_security_headers(),
        'body': json.dumps(response_body)
    }


def count_total_voters():
    """
    Count total number of unique voters (VOTE records).
    
    Returns:
        Integer count of total voters
    """
    try:
        # Scan for all VOTE records and count them
        response = table.scan(
            FilterExpression=Key('EntityType').eq('VOTE'),
            Select='COUNT'
        )
        
        count = response.get('Count', 0)
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Key('EntityType').eq('VOTE'),
                ExclusiveStartKey=response['LastEvaluatedKey'],
                Select='COUNT'
            )
            count += response.get('Count', 0)
        
        return count
    
    except Exception as e:
        print(f'Error counting voters: {str(e)}')
        return 0
