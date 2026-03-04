"""
Unit tests for Setup Handler edge cases.

Feature: chili-cookoff-voting-app
Requirements: 2.1, 2.2, 2.3, 5.3
"""

import json
import os
import pytest
from contextlib import contextmanager
from moto import mock_aws
import boto3
from botocore.exceptions import ClientError

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))
from setup_handler import lambda_handler


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


def test_empty_entry_list_rejection():
    """
    Test that an empty entry list is rejected with appropriate error message.
    
    Requirements: 2.1, 2.2
    """
    with setup_dynamodb_table():
        # Create event with empty entry list
        event = {
            'body': json.dumps({'entries': []})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'at least one entry' in response_body['message'].lower()


def test_duplicate_entry_name_rejection():
    """
    Test that duplicate entry names are rejected with appropriate error message.
    
    Requirements: 2.2, 2.3
    """
    with setup_dynamodb_table():
        # Create event with duplicate entry names
        event = {
            'body': json.dumps({
                'entries': ['Spicy Chili', 'Mild Chili', 'Spicy Chili']
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'unique' in response_body['message'].lower()


def test_entry_name_with_special_characters():
    """
    Test that entry names with special characters are accepted and stored correctly.
    
    Requirements: 2.2, 2.3
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Create event with special characters in entry names
        special_entries = [
            "Bob's Spicy Chili!",
            "Chili #1 - Extra Hot",
            "Mom & Dad's Recipe",
            "Chili (Vegetarian)",
            "Texas-Style BBQ Chili"
        ]
        
        event = {
            'body': json.dumps({'entries': special_entries})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        
        # Query DynamoDB to verify entries are stored correctly
        from boto3.dynamodb.conditions import Key
        
        query_response = dynamodb_table.query(
            KeyConditionExpression=Key('EntityType').eq('ENTRY')
        )
        
        stored_entries = query_response.get('Items', [])
        stored_entry_ids = {item['EntityId'] for item in stored_entries}
        
        # Verify all special character entries are stored
        expected_entry_ids = {entry.strip() for entry in special_entries}
        assert stored_entry_ids == expected_entry_ids


def test_maximum_entry_count():
    """
    Test that exactly 50 entries (maximum allowed) are accepted and stored correctly.
    
    Requirements: 2.1, 2.2, 2.3
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Create event with exactly 50 entries
        max_entries = [f"Chili Entry {i+1}" for i in range(50)]
        
        event = {
            'body': json.dumps({'entries': max_entries})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert '50' in response_body['message']
        
        # Query DynamoDB to verify all 50 entries are stored
        from boto3.dynamodb.conditions import Key
        
        query_response = dynamodb_table.query(
            KeyConditionExpression=Key('EntityType').eq('ENTRY')
        )
        
        stored_entries = query_response.get('Items', [])
        assert len(stored_entries) == 50


def test_exceeds_maximum_entry_count():
    """
    Test that more than 50 entries are rejected with appropriate error message.
    
    Requirements: 2.1, 2.2
    """
    with setup_dynamodb_table():
        # Create event with 51 entries (exceeds maximum)
        too_many_entries = [f"Chili Entry {i+1}" for i in range(51)]
        
        event = {
            'body': json.dumps({'entries': too_many_entries})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'maximum' in response_body['message'].lower() or '50' in response_body['message']


def test_dynamodb_error_handling():
    """
    Test that DynamoDB errors are handled gracefully with appropriate error messages.
    
    Requirements: 5.3
    """
    with setup_dynamodb_table():
        # Set an invalid table name to trigger DynamoDB error
        original_table_name = os.environ.get('TABLE_NAME')
        os.environ['TABLE_NAME'] = 'NonExistentTable'
        
        # Need to reload the module to pick up the new table name
        import importlib
        import setup_handler
        importlib.reload(setup_handler)
        
        try:
            event = {
                'body': json.dumps({'entries': ['Test Chili']})
            }
            context = {}
            
            # Call the handler
            response = setup_handler.lambda_handler(event, context)
            
            # Verify error response
            assert response['statusCode'] == 500
            response_body = json.loads(response['body'])
            assert response_body['success'] is False
            assert 'error' in response_body['message'].lower()
            
        finally:
            # Restore original table name
            if original_table_name:
                os.environ['TABLE_NAME'] = original_table_name
            else:
                os.environ.pop('TABLE_NAME', None)
            
            # Reload module again to restore original state
            importlib.reload(setup_handler)


def test_entry_with_whitespace_trimming():
    """
    Test that entry names with leading/trailing whitespace are trimmed correctly.
    
    Requirements: 2.2, 2.3
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Create event with entries that have whitespace
        entries_with_whitespace = [
            "  Spicy Chili  ",
            "\tMild Chili\t",
            " Vegetarian Chili "
        ]
        
        event = {
            'body': json.dumps({'entries': entries_with_whitespace})
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        
        # Query DynamoDB to verify entries are stored with trimmed names
        from boto3.dynamodb.conditions import Key
        
        query_response = dynamodb_table.query(
            KeyConditionExpression=Key('EntityType').eq('ENTRY')
        )
        
        stored_entries = query_response.get('Items', [])
        stored_entry_ids = {item['EntityId'] for item in stored_entries}
        
        # Verify entries are stored with trimmed names
        expected_entry_ids = {'Spicy Chili', 'Mild Chili', 'Vegetarian Chili'}
        assert stored_entry_ids == expected_entry_ids


def test_empty_string_entry_rejection():
    """
    Test that entries with empty strings (or only whitespace) are rejected.
    
    Requirements: 2.2
    """
    with setup_dynamodb_table():
        # Create event with empty string entries
        event = {
            'body': json.dumps({
                'entries': ['Valid Chili', '', 'Another Valid Chili']
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'empty' in response_body['message'].lower()


def test_whitespace_only_entry_rejection():
    """
    Test that entries with only whitespace are rejected.
    
    Requirements: 2.2
    """
    with setup_dynamodb_table():
        # Create event with whitespace-only entries
        event = {
            'body': json.dumps({
                'entries': ['Valid Chili', '   ', 'Another Valid Chili']
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'empty' in response_body['message'].lower()
