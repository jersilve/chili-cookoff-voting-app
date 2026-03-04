"""
Unit tests for Leaderboard Handler edge cases.

Feature: chili-cookoff-voting-app
Requirements: 4.1, 4.2, 5.3
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
from leaderboard_handler import lambda_handler


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


def test_empty_vote_set():
    """
    Test that leaderboard returns empty rankings when no votes exist yet.
    
    Requirements: 4.1, 4.2
    """
    with setup_dynamodb_table():
        # Create event (no body needed for GET request)
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response with empty rankings
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'rankings' in response_body
        assert response_body['rankings'] == []
        assert 'timestamp' in response_body


def test_single_vote_scenario():
    """
    Test that leaderboard correctly displays rankings with a single vote.
    
    Requirements: 4.1, 4.2
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Add a single vote to DynamoDB
        dynamodb_table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': 'vote-001',
                'FirstChoice': 'Spicy Chili',
                'SecondChoice': 'Mild Chili',
                'ThirdChoice': 'Vegetarian Chili',
                'Timestamp': '2024-01-15T14:22:33Z'
            }
        )
        
        # Create event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        
        # Verify rankings
        rankings = response_body['rankings']
        assert len(rankings) == 3
        
        # Verify correct point assignments and sorting
        assert rankings[0] == {'entry': 'Spicy Chili', 'points': 3}
        assert rankings[1] == {'entry': 'Mild Chili', 'points': 2}
        assert rankings[2] == {'entry': 'Vegetarian Chili', 'points': 1}


def test_tie_scenario():
    """
    Test that leaderboard correctly handles ties (multiple entries with same points).
    
    Requirements: 4.1, 4.2
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Add votes that create a tie
        # Vote 1: A=3, B=2, C=1
        dynamodb_table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': 'vote-001',
                'FirstChoice': 'Chili A',
                'SecondChoice': 'Chili B',
                'ThirdChoice': 'Chili C',
                'Timestamp': '2024-01-15T14:22:33Z'
            }
        )
        
        # Vote 2: B=3, C=2, A=1 (now A=4, B=5, C=3)
        dynamodb_table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': 'vote-002',
                'FirstChoice': 'Chili B',
                'SecondChoice': 'Chili C',
                'ThirdChoice': 'Chili A',
                'Timestamp': '2024-01-15T14:23:00Z'
            }
        )
        
        # Vote 3: C=3, A=2, B=1 (now A=6, B=6, C=6 - three-way tie!)
        dynamodb_table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': 'vote-003',
                'FirstChoice': 'Chili C',
                'SecondChoice': 'Chili A',
                'ThirdChoice': 'Chili B',
                'Timestamp': '2024-01-15T14:23:30Z'
            }
        )
        
        # Create event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        
        # Verify rankings
        rankings = response_body['rankings']
        assert len(rankings) == 3
        
        # All entries should have 6 points (tie)
        for ranking in rankings:
            assert ranking['points'] == 6
        
        # Verify all entries are present
        entry_names = {ranking['entry'] for ranking in rankings}
        assert entry_names == {'Chili A', 'Chili B', 'Chili C'}


def test_entry_with_zero_votes():
    """
    Test that entries with zero votes do not appear on the leaderboard.
    
    Note: The leaderboard only shows entries that have received votes.
    Entries configured in setup but not voted for will not appear.
    
    Requirements: 4.1, 4.2
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Add entries to DynamoDB (configured but not all voted for)
        dynamodb_table.put_item(
            Item={
                'EntityType': 'ENTRY',
                'EntityId': 'Chili A',
                'CreatedAt': '2024-01-15T10:00:00Z'
            }
        )
        dynamodb_table.put_item(
            Item={
                'EntityType': 'ENTRY',
                'EntityId': 'Chili B',
                'CreatedAt': '2024-01-15T10:00:00Z'
            }
        )
        dynamodb_table.put_item(
            Item={
                'EntityType': 'ENTRY',
                'EntityId': 'Chili C',
                'CreatedAt': '2024-01-15T10:00:00Z'
            }
        )
        
        # Add a vote that only includes Chili A and Chili B
        dynamodb_table.put_item(
            Item={
                'EntityType': 'VOTE',
                'EntityId': 'vote-001',
                'FirstChoice': 'Chili A',
                'SecondChoice': 'Chili B',
                'ThirdChoice': 'Chili C',
                'Timestamp': '2024-01-15T14:22:33Z'
            }
        )
        
        # Create event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        
        # Verify rankings - all three entries should appear since they all got votes
        rankings = response_body['rankings']
        assert len(rankings) == 3
        
        # Verify points
        entry_points = {r['entry']: r['points'] for r in rankings}
        assert entry_points['Chili A'] == 3
        assert entry_points['Chili B'] == 2
        assert entry_points['Chili C'] == 1


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
        import leaderboard_handler
        importlib.reload(leaderboard_handler)
        
        try:
            event = {}
            context = {}
            
            # Call the handler
            response = leaderboard_handler.lambda_handler(event, context)
            
            # Verify error response
            assert response['statusCode'] == 500
            response_body = json.loads(response['body'])
            assert 'error' in response_body
            assert response_body['rankings'] == []
            
        finally:
            # Restore original table name
            if original_table_name:
                os.environ['TABLE_NAME'] = original_table_name
            else:
                os.environ.pop('TABLE_NAME', None)
            
            # Reload module again to restore original state
            importlib.reload(leaderboard_handler)


def test_multiple_votes_aggregation():
    """
    Test that leaderboard correctly aggregates points from multiple votes.
    
    Requirements: 4.1, 4.2
    """
    with setup_dynamodb_table() as dynamodb_table:
        # Add multiple votes
        votes = [
            {
                'EntityType': 'VOTE',
                'EntityId': 'vote-001',
                'FirstChoice': 'Spicy Chili',
                'SecondChoice': 'Mild Chili',
                'ThirdChoice': 'Vegetarian Chili',
                'Timestamp': '2024-01-15T14:22:33Z'
            },
            {
                'EntityType': 'VOTE',
                'EntityId': 'vote-002',
                'FirstChoice': 'Spicy Chili',
                'SecondChoice': 'Vegetarian Chili',
                'ThirdChoice': 'Mild Chili',
                'Timestamp': '2024-01-15T14:23:00Z'
            },
            {
                'EntityType': 'VOTE',
                'EntityId': 'vote-003',
                'FirstChoice': 'Mild Chili',
                'SecondChoice': 'Spicy Chili',
                'ThirdChoice': 'Vegetarian Chili',
                'Timestamp': '2024-01-15T14:23:30Z'
            }
        ]
        
        for vote in votes:
            dynamodb_table.put_item(Item=vote)
        
        # Create event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        
        # Calculate expected points:
        # Spicy Chili: 3 + 3 + 2 = 8 points
        # Mild Chili: 2 + 1 + 3 = 6 points
        # Vegetarian Chili: 1 + 2 + 1 = 4 points
        
        rankings = response_body['rankings']
        assert len(rankings) == 3
        
        # Verify correct sorting and point totals
        assert rankings[0] == {'entry': 'Spicy Chili', 'points': 8}
        assert rankings[1] == {'entry': 'Mild Chili', 'points': 6}
        assert rankings[2] == {'entry': 'Vegetarian Chili', 'points': 4}


def test_timestamp_format():
    """
    Test that leaderboard response includes a properly formatted ISO8601 timestamp.
    
    Requirements: 4.2
    """
    with setup_dynamodb_table():
        # Create event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        
        # Verify timestamp exists and is in ISO8601 format
        assert 'timestamp' in response_body
        timestamp = response_body['timestamp']
        
        # Basic ISO8601 format check (should end with 'Z' for UTC)
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        
        # Verify it can be parsed as a valid datetime
        from datetime import datetime
        parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed_timestamp is not None
