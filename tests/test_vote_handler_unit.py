"""
Unit tests for Vote Handler edge cases.

Feature: chili-cookoff-voting-app
Requirements: 3.2, 3.4, 5.3
"""

import json
import os
import pytest
from contextlib import contextmanager
from moto import mock_aws
import boto3
from unittest.mock import patch
import uuid

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))
from vote_handler import lambda_handler


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


def test_vote_with_non_existent_entry_name():
    """
    Test that a vote with a non-existent entry name is rejected.
    
    Requirements: 3.2, 5.3
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with non-existent entry
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Mild Chili',
                'third': 'Non-Existent Chili'  # This entry doesn't exist
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'Non-Existent Chili' in response_body['message']
        assert 'not found' in response_body['message']


def test_vote_with_only_2_entries():
    """
    Test that a vote with only 2 entries (missing third choice) is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with only 2 entries (missing third)
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Mild Chili'
                # 'third' is missing
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'third choice' in response_body['message'].lower() or 'required' in response_body['message'].lower()


def test_vote_with_4_entries():
    """
    Test that a vote with 4 entries is rejected (only 3 allowed).
    
    Note: The API only accepts first, second, third fields, so a 4th entry
    would be ignored. This test verifies the handler only processes the 3 expected fields.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili', 'BBQ Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with 4 entries (fourth should be ignored)
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Mild Chili',
                'third': 'Vegetarian Chili',
                'fourth': 'BBQ Chili'  # This should be ignored
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response (fourth entry is ignored)
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert 'voteId' in response_body
        
        # Verify only 3 entries are stored in the vote
        vote_id = response_body['voteId']
        
        # Query DynamoDB to verify the vote
        from boto3.dynamodb.conditions import Key
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('ChiliCookoffData')
        
        query_response = table.query(
            KeyConditionExpression=Key('EntityType').eq('VOTE') & Key('EntityId').eq(vote_id)
        )
        
        stored_votes = query_response.get('Items', [])
        assert len(stored_votes) == 1
        
        stored_vote = stored_votes[0]
        assert stored_vote['FirstChoice'] == 'Spicy Chili'
        assert stored_vote['SecondChoice'] == 'Mild Chili'
        assert stored_vote['ThirdChoice'] == 'Vegetarian Chili'
        # Verify 'fourth' is not stored
        assert 'FourthChoice' not in stored_vote
        assert 'fourth' not in stored_vote


def test_vote_with_duplicate_entries():
    """
    Test that a vote with duplicate entries is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with duplicate entries
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Spicy Chili',  # Duplicate of first
                'third': 'Mild Chili'
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'different' in response_body['message'].lower() or 'unique' in response_body['message'].lower()


def test_uuid_generation_uniqueness():
    """
    Test that UUID generation produces unique vote IDs for multiple votes.
    
    Requirements: 3.4
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        vote_ids = []
        
        # Submit 10 votes and collect vote IDs
        for i in range(10):
            event = {
                'body': json.dumps({
                    'first': entries[0],
                    'second': entries[1],
                    'third': entries[2]
                })
            }
            context = {}
            
            # Call the handler
            response = lambda_handler(event, context)
            
            # Verify successful response
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['success'] is True
            assert 'voteId' in response_body
            
            vote_ids.append(response_body['voteId'])
        
        # Verify all vote IDs are unique
        assert len(vote_ids) == len(set(vote_ids)), \
            f"Vote IDs should be unique, but found duplicates: {vote_ids}"
        
        # Verify all vote IDs are valid UUIDs
        for vote_id in vote_ids:
            try:
                uuid.UUID(vote_id)
            except ValueError:
                pytest.fail(f"Vote ID '{vote_id}' is not a valid UUID")


def test_vote_with_all_three_same_entry():
    """
    Test that a vote with all three choices being the same entry is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with all same entry
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Spicy Chili',
                'third': 'Spicy Chili'
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'different' in response_body['message'].lower()


def test_vote_with_empty_string_entry():
    """
    Test that a vote with an empty string entry is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with empty string
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': '',  # Empty string
                'third': 'Mild Chili'
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False


def test_vote_with_null_entry():
    """
    Test that a vote with a null entry is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with null value
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': None,  # Null value
                'third': 'Mild Chili'
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'required' in response_body['message'].lower()


def test_dynamodb_error_handling_on_vote_storage():
    """
    Test that DynamoDB errors during vote storage are handled gracefully.
    
    Requirements: 5.3
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create valid vote
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 'Mild Chili',
                'third': 'Vegetarian Chili'
            })
        }
        context = {}
        
        # Mock the store_vote function to raise an exception
        with patch('vote_handler.store_vote', side_effect=Exception('DynamoDB error')):
            # Call the handler
            response = lambda_handler(event, context)
            
            # Verify error response
            assert response['statusCode'] == 500
            response_body = json.loads(response['body'])
            assert response_body['success'] is False
            assert 'error' in response_body['message'].lower()


def test_vote_with_non_string_entry():
    """
    Test that a vote with non-string entry values is rejected.
    
    Requirements: 3.2
    """
    entries = ['Spicy Chili', 'Mild Chili', 'Vegetarian Chili']
    
    with setup_dynamodb_with_entries(entries):
        # Create vote with integer instead of string
        event = {
            'body': json.dumps({
                'first': 'Spicy Chili',
                'second': 123,  # Integer instead of string
                'third': 'Mild Chili'
            })
        }
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify error response
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'string' in response_body['message'].lower()
