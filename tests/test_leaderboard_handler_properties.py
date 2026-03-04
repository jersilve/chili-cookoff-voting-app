"""
Property-based tests for Leaderboard Handler using Hypothesis.

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
from leaderboard_handler import lambda_handler


# Strategy for generating valid entry names
entry_name_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),
    min_size=1,
    max_size=100
).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)


@contextmanager
def setup_dynamodb_with_votes(entries, votes):
    """
    Context manager to create a mocked DynamoDB table with pre-populated entries and votes.
    
    Args:
        entries: List of entry names to pre-populate in the table
        votes: List of vote tuples (first_choice, second_choice, third_choice)
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
        
        # Pre-populate votes
        import uuid
        for idx, (first, second, third) in enumerate(votes):
            vote_id = str(uuid.uuid4())
            table.put_item(
                Item={
                    'EntityType': 'VOTE',
                    'EntityId': vote_id,
                    'FirstChoice': first,
                    'SecondChoice': second,
                    'ThirdChoice': third,
                    'Timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
        
        yield table


# Feature: chili-cookoff-voting-app, Property 10: Leaderboard sorting correctness
@given(
    entries=st.lists(
        entry_name_strategy,
        min_size=3,
        max_size=20,
        unique=True
    ).filter(lambda lst: len(lst) >= 3),
    num_votes=st.integers(min_value=1, max_value=50)
)
@settings(max_examples=100, deadline=None)
def test_leaderboard_sorting_correctness(entries, num_votes):
    """
    **Validates: Requirements 4.1**
    
    Property 10: Leaderboard sorting correctness
    
    For any set of votes in DynamoDB, the leaderboard should display all entries
    sorted in descending order by their total points, where total points equals
    the sum of all points received from all votes.
    
    Point assignments:
    - FirstChoice: 3 points
    - SecondChoice: 2 points
    - ThirdChoice: 1 point
    
    This test:
    1. Generates random entry lists (3-20 entries)
    2. Generates random sets of votes (1-50 votes)
    3. Calculates expected point totals manually
    4. Queries leaderboard via Leaderboard Handler
    5. Verifies entries are sorted by points in descending order
    6. Verifies point totals match expected values
    """
    import random
    
    # Generate random votes
    votes = []
    for _ in range(num_votes):
        # Select 3 distinct entries for each vote
        selected = random.sample(entries, 3)
        votes.append((selected[0], selected[1], selected[2]))
    
    with setup_dynamodb_with_votes(entries, votes) as dynamodb_table:
        # Calculate expected point totals manually
        expected_points = {}
        for first, second, third in votes:
            expected_points[first] = expected_points.get(first, 0) + 3
            expected_points[second] = expected_points.get(second, 0) + 2
            expected_points[third] = expected_points.get(third, 0) + 1
        
        # Create ALB-formatted event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}: {response.get('body')}"
        
        response_body = json.loads(response['body'])
        assert 'rankings' in response_body, \
            "Response should include rankings"
        assert 'timestamp' in response_body, \
            "Response should include timestamp"
        
        rankings = response_body['rankings']
        
        # Verify all entries with votes are present in rankings
        ranked_entries = {r['entry'] for r in rankings}
        expected_entries = set(expected_points.keys())
        assert ranked_entries == expected_entries, \
            f"Rankings should include all entries with votes. Expected: {expected_entries}, Got: {ranked_entries}"
        
        # Verify rankings are sorted by points in descending order
        for i in range(len(rankings) - 1):
            current_points = rankings[i]['points']
            next_points = rankings[i + 1]['points']
            assert current_points >= next_points, \
                f"Rankings must be sorted by points descending. " \
                f"Entry '{rankings[i]['entry']}' has {current_points} points, " \
                f"but entry '{rankings[i + 1]['entry']}' has {next_points} points"
        
        # Verify point totals match expected values
        for ranking in rankings:
            entry = ranking['entry']
            actual_points = ranking['points']
            expected = expected_points.get(entry, 0)
            assert actual_points == expected, \
                f"Entry '{entry}' should have {expected} points, but has {actual_points} points"
        
        # Verify the structure of each ranking entry
        for ranking in rankings:
            assert 'entry' in ranking, \
                "Each ranking must have 'entry' field"
            assert 'points' in ranking, \
                "Each ranking must have 'points' field"
            assert isinstance(ranking['entry'], str), \
                "Entry name must be a string"
            assert isinstance(ranking['points'], int), \
                "Points must be an integer"
            assert ranking['points'] >= 0, \
                "Points must be non-negative"


# Feature: chili-cookoff-voting-app, Property 11: Leaderboard point totals accuracy
@given(
    entries=st.lists(
        entry_name_strategy,
        min_size=3,
        max_size=20,
        unique=True
    ).filter(lambda lst: len(lst) >= 3),
    num_votes=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_leaderboard_point_totals_accuracy(entries, num_votes):
    """
    **Validates: Requirements 4.2**
    
    Property 11: Leaderboard point totals accuracy
    
    For any set of votes in DynamoDB, the point total displayed for each entry
    on the leaderboard should equal the sum of all points that entry received
    across all votes (3 points per first-place vote, 2 per second-place, 1 per third-place).
    
    This test:
    1. Generates random entry lists (3-20 entries)
    2. Generates random sets of votes (1-100 votes)
    3. Calculates expected point totals manually for each entry
    4. Queries leaderboard via Leaderboard Handler
    5. Verifies each entry's point total matches the expected value exactly
    """
    import random
    
    # Generate random votes
    votes = []
    for _ in range(num_votes):
        # Select 3 distinct entries for each vote
        selected = random.sample(entries, 3)
        votes.append((selected[0], selected[1], selected[2]))
    
    with setup_dynamodb_with_votes(entries, votes) as dynamodb_table:
        # Calculate expected point totals manually
        expected_points = {}
        for first, second, third in votes:
            expected_points[first] = expected_points.get(first, 0) + 3
            expected_points[second] = expected_points.get(second, 0) + 2
            expected_points[third] = expected_points.get(third, 0) + 1
        
        # Create ALB-formatted event
        event = {}
        context = {}
        
        # Call the handler
        response = lambda_handler(event, context)
        
        # Verify successful response
        assert response['statusCode'] == 200, \
            f"Expected status 200, got {response['statusCode']}: {response.get('body')}"
        
        response_body = json.loads(response['body'])
        assert 'rankings' in response_body, \
            "Response should include rankings"
        
        rankings = response_body['rankings']
        
        # Verify point totals match expected values for each entry
        for ranking in rankings:
            entry = ranking['entry']
            actual_points = ranking['points']
            expected = expected_points.get(entry, 0)
            
            assert actual_points == expected, \
                f"Point total accuracy failed for entry '{entry}': " \
                f"Expected {expected} points (from {num_votes} total votes), " \
                f"but got {actual_points} points. " \
                f"Difference: {actual_points - expected}"
        
        # Verify all entries with votes are accounted for
        ranked_entries = {r['entry'] for r in rankings}
        expected_entries = set(expected_points.keys())
        assert ranked_entries == expected_entries, \
            f"All entries with votes should appear in rankings. " \
            f"Expected: {expected_entries}, Got: {ranked_entries}"
        
        # Verify no entry has incorrect point calculation
        # (this is a redundant check but emphasizes the property)
        total_expected_points = sum(expected_points.values())
        total_actual_points = sum(r['points'] for r in rankings)
        assert total_actual_points == total_expected_points, \
            f"Total points across all entries should match. " \
            f"Expected total: {total_expected_points}, Got: {total_actual_points}"
