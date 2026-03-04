"""
Property-based tests for Vote Handler using Hypothesis.

Feature: chili-cookoff-voting-app
"""

import json
import os
from contextlib import contextmanager
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))
from vote_handler import lambda_handler


# Strategy for generating valid entry names
entry_name_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=100
).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)


@contextmanager
def setup_dynamodb_with_entries(entries):
    """
    Context manager to create a mocked DynamoDB table with pre-populated entries.
    
    Args:
        entries: List of entry names to pre-populate in the table
    """
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create table
        table = dynamodb.create_table(
            TableName='ChiliCookoffData',
            KeySchema=[
                {'AttributeName': 'EntityType', 'KeyType': 'HASH'},
                {'AttributeName': 'EntityId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'EntityType', 'AttributeType': 'S'},
                {'AttributeName': 'EntityId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Set environment variable for table name
        os.environ['TABLE_NAME'] = 'ChiliCookoffData'
        
        # Pre-populate entries
        from datetime import datetime
        for entry in entries:
            table.put_item(
                Item={
                    'EntityType': 'ENTRY',
                    'EntityId': entry,
                    'CreatedAt': datetime.utcnow().isoformat() + 'Z'
                }
            )
        
        yield table


# Feature: chili-cookoff-voting-app, Property 8: Vote point assignment
@given(
    entries=st.lists(
        entry_name_strategy,
        min_size=3,
        max_size=50,
        unique=True
    ).filter(lambda lst: len(lst) >= 3)
)
@settings(max_examples=100, deadline=None)
def test_vote_point_assignment(entries):
    """
    **Validates: Requirements 3.3**
    
    Property 8: Vote point assignment
    
    For any valid vote submission with three distinct entries, the application
    should assign exactly 3 points to the first choice, 2 points to the second
    choice, and 1 point to the third choice.
    
    The point assignment is implicit in the storage structure:
    - FirstChoice field represents 3 points
    - SecondChoice field represents 2 points
    - ThirdChoice field represents 1 point
    
    This test:
    1. Generates random entry lists (at least 3 entries)
    2. Selects 3 distinct entries for a vote
    3. Submits the vote via Vote Handler
    4. Verifies the vote is stored with correct FirstChoice, SecondChoice, ThirdChoice fields
    """
    with setup_dynamodb_with_entries(entries) as dynamodb_table:
        # Select 3 distinct entries for the vote
        import random
        selected_entries = random.sample(entries, 3)
        first_choice = selected_entries[0]
        second_choice = selected_entries[1]
        third_choice = selected_entries[2]
        
        # Create ALB-formatted event
        event = {
            'body': json.dumps({
                'first': first_choice,
                'second': second_choice,
                'third': third_choice
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}: {response.get('body')}"
        
        response_body = json.loads(response['body'])
        assert response_body['success'] is True, \
            f"Expected success=True, got {response_body}"
        assert 'voteId' in response_body, \
            "Response should include voteId"
        
        vote_id = response_body['voteId']
        
        # Query DynamoDB to verify the vote is stored correctly
        from boto3.dynamodb.conditions import Key
        
        query_response = dynamodb_table.query(
            KeyConditionExpression=Key('EntityType').eq('VOTE') & Key('EntityId').eq(vote_id)
        )
        
        stored_votes = query_response.get('Items', [])
        assert len(stored_votes) == 1, \
            f"Expected exactly 1 vote, found {len(stored_votes)}"
        
        stored_vote = stored_votes[0]
        
        # Verify the vote has the correct structure and point assignments
        # FirstChoice = 3 points (implicit)
        assert 'FirstChoice' in stored_vote, \
            "Vote must have FirstChoice field"
        assert stored_vote['FirstChoice'] == first_choice, \
            f"FirstChoice should be '{first_choice}', got '{stored_vote['FirstChoice']}'"
        
        # SecondChoice = 2 points (implicit)
        assert 'SecondChoice' in stored_vote, \
            "Vote must have SecondChoice field"
        assert stored_vote['SecondChoice'] == second_choice, \
            f"SecondChoice should be '{second_choice}', got '{stored_vote['SecondChoice']}'"
        
        # ThirdChoice = 1 point (implicit)
        assert 'ThirdChoice' in stored_vote, \
            "Vote must have ThirdChoice field"
        assert stored_vote['ThirdChoice'] == third_choice, \
            f"ThirdChoice should be '{third_choice}', got '{stored_vote['ThirdChoice']}'"
        
        # Verify all three choices are distinct
        choices = [
            stored_vote['FirstChoice'],
            stored_vote['SecondChoice'],
            stored_vote['ThirdChoice']
        ]
        assert len(choices) == len(set(choices)), \
            f"All three choices must be distinct, got {choices}"
        
        # Verify other required fields
        assert stored_vote['EntityType'] == 'VOTE', \
            "EntityType must be 'VOTE'"
        assert stored_vote['EntityId'] == vote_id, \
            f"EntityId should be '{vote_id}', got '{stored_vote['EntityId']}'"
        assert 'Timestamp' in stored_vote, \
            "Vote must have Timestamp field"


# Feature: chili-cookoff-voting-app, Property 7: Vote selection constraint
@given(
    entries=st.lists(
        entry_name_strategy,
        min_size=3,
        max_size=50,
        unique=True
    ).filter(lambda lst: len(lst) >= 3),
    invalid_vote_type=st.sampled_from([
        'duplicate_first_second',
        'duplicate_first_third',
        'duplicate_second_third',
        'all_same',
        'missing_first',
        'missing_second',
        'missing_third',
        'non_existent_entry'
    ])
)
@settings(max_examples=100, deadline=None)
def test_vote_selection_constraint(entries, invalid_vote_type):
    """
    **Validates: Requirements 3.2**
    
    Property 7: Vote selection constraint
    
    For any vote submission attempt, the voting interface should enforce
    selection of exactly three distinct entries in ranked order (first, second, third).
    
    This test:
    1. Generates random entry lists (at least 3 entries)
    2. Creates various types of invalid votes:
       - Duplicate selections (same entry in multiple positions)
       - Missing choices (fewer than 3 selections)
       - Non-existent entries
    3. Verifies Vote Handler rejects them with appropriate error messages
    """
    with setup_dynamodb_with_entries(entries) as dynamodb_table:
        import random
        
        # Select entries for the vote based on invalid vote type
        if invalid_vote_type == 'duplicate_first_second':
            # First and second choice are the same
            first_choice = entries[0]
            second_choice = entries[0]
            third_choice = entries[1] if len(entries) > 1 else entries[0]
            expected_error = 'Must select exactly 3 different entries'
            
        elif invalid_vote_type == 'duplicate_first_third':
            # First and third choice are the same
            first_choice = entries[0]
            second_choice = entries[1] if len(entries) > 1 else entries[0]
            third_choice = entries[0]
            expected_error = 'Must select exactly 3 different entries'
            
        elif invalid_vote_type == 'duplicate_second_third':
            # Second and third choice are the same
            first_choice = entries[0]
            second_choice = entries[1] if len(entries) > 1 else entries[0]
            third_choice = entries[1] if len(entries) > 1 else entries[0]
            expected_error = 'Must select exactly 3 different entries'
            
        elif invalid_vote_type == 'all_same':
            # All three choices are the same
            first_choice = entries[0]
            second_choice = entries[0]
            third_choice = entries[0]
            expected_error = 'Must select exactly 3 different entries'
            
        elif invalid_vote_type == 'missing_first':
            # First choice is missing (None or empty string)
            first_choice = None
            second_choice = entries[0]
            third_choice = entries[1] if len(entries) > 1 else entries[0]
            expected_error = 'First choice is required'
            
        elif invalid_vote_type == 'missing_second':
            # Second choice is missing
            first_choice = entries[0]
            second_choice = None
            third_choice = entries[1] if len(entries) > 1 else entries[0]
            expected_error = 'Second choice is required'
            
        elif invalid_vote_type == 'missing_third':
            # Third choice is missing
            first_choice = entries[0]
            second_choice = entries[1] if len(entries) > 1 else entries[0]
            third_choice = None
            expected_error = 'Third choice is required'
            
        elif invalid_vote_type == 'non_existent_entry':
            # One of the choices doesn't exist in the database
            first_choice = entries[0]
            second_choice = entries[1] if len(entries) > 1 else entries[0]
            # Generate a non-existent entry name
            third_choice = 'NonExistentEntry_' + str(random.randint(10000, 99999))
            expected_error = f"Entry '{third_choice}' not found"
        
        # Create ALB-formatted event
        event = {
            'body': json.dumps({
                'first': first_choice,
                'second': second_choice,
                'third': third_choice
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400, \
            f"Expected status 400 for invalid vote, got {response['statusCode']}: {response.get('body')}"
        
        response_body = json.loads(response['body'])
        assert response_body['success'] is False, \
            f"Expected success=False for invalid vote, got {response_body}"
        assert 'message' in response_body, \
            "Error response should include message"
        
        # Verify the error message matches expected error
        actual_error = response_body['message']
        assert expected_error in actual_error or actual_error in expected_error, \
            f"Expected error containing '{expected_error}', got '{actual_error}'"
        
        # Verify no vote was stored in DynamoDB
        from boto3.dynamodb.conditions import Key
        
        scan_response = dynamodb_table.scan(
            FilterExpression=Key('EntityType').eq('VOTE')
        )
        
        stored_votes = scan_response.get('Items', [])
        assert len(stored_votes) == 0, \
            f"Invalid vote should not be stored, but found {len(stored_votes)} vote(s)"
