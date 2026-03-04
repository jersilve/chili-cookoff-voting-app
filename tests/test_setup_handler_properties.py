"""
Property-based tests for Setup Handler using Hypothesis.

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
from setup_handler import lambda_handler


# Strategy for generating valid entry names
entry_name_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=100
).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)


# Strategy for generating lists of unique entry names (1-50 entries)
entry_list_strategy = st.lists(
    entry_name_strategy,
    min_size=1,
    max_size=50,
    unique=True
)


@contextmanager
def setup_dynamodb_table():
    """Context manager to create a mocked DynamoDB table for testing."""
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
        
        yield table


# Feature: chili-cookoff-voting-app, Property 5: Entry configuration persistence
@given(entries=entry_list_strategy)
@settings(max_examples=100, deadline=None)
def test_entry_configuration_persistence(entries):
    """
    **Validates: Requirements 2.3, 5.1**
    
    Property 5: Entry configuration persistence
    
    For any valid entry configuration (list of non-empty entry names),
    submitting the configuration should result in all entries being stored
    in DynamoDB and retrievable via query.
    
    This test:
    1. Generates random entry lists (1-50 entries)
    2. Submits via Setup Handler
    3. Verifies all entries are retrievable from DynamoDB
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Create ALB-formatted event
        event = {
            'body': json.dumps({'entries': entries})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        
        # Query DynamoDB to verify all entries are stored
        from boto3.dynamodb.conditions import Key
        
        query_response = dynamodb_table.query(
            KeyConditionExpression=Key('EntityType').eq('ENTRY')
        )
        
        stored_entries = query_response.get('Items', [])
        stored_entry_ids = {item['EntityId'] for item in stored_entries}
        
        # Verify all submitted entries are in DynamoDB
        expected_entry_ids = {entry.strip() for entry in entries}
        assert stored_entry_ids == expected_entry_ids, \
            f"Stored entries {stored_entry_ids} do not match expected {expected_entry_ids}"
        
        # Verify the count matches
        assert len(stored_entries) == len(entries), \
            f"Expected {len(entries)} entries, but found {len(stored_entries)}"
        
        # Verify each entry has the required attributes
        for item in stored_entries:
            assert 'EntityType' in item
            assert item['EntityType'] == 'ENTRY'
            assert 'EntityId' in item
            assert 'CreatedAt' in item
            assert item['EntityId'] in expected_entry_ids
