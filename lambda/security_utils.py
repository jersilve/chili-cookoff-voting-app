"""
Security utilities for Chili Cook-Off Lambda functions.
Provides input validation, sanitization, and security headers.
"""

import re
from typing import Optional, Dict, Any


# Security constants
MAX_REQUEST_SIZE = 10 * 1024  # 10 KB
MAX_STRING_LENGTH = 1000
MAX_VOTER_ID_LENGTH = 50
VOTER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{4,50}$')
ENTRY_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\']{1,100}$')


def validate_voter_id(voter_id: Any) -> Optional[str]:
    """
    Validate and sanitize voter ID.
    
    Args:
        voter_id: Voter ID to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not voter_id:
        return 'Voter ID is required'
    
    if not isinstance(voter_id, str):
        return 'Voter ID must be a string'
    
    if len(voter_id) > MAX_VOTER_ID_LENGTH:
        return f'Voter ID must be {MAX_VOTER_ID_LENGTH} characters or less'
    
    if not VOTER_ID_PATTERN.match(voter_id):
        return 'Voter ID must contain only alphanumeric characters (4-50 chars)'
    
    return None


def validate_entry_name(entry_name: Any) -> Optional[str]:
    """
    Validate and sanitize entry name.
    
    Args:
        entry_name: Entry name to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not entry_name:
        return 'Entry name is required'
    
    if not isinstance(entry_name, str):
        return 'Entry name must be a string'
    
    if len(entry_name) > 100:
        return 'Entry name must be 100 characters or less'
    
    if not ENTRY_NAME_PATTERN.match(entry_name):
        return 'Entry name contains invalid characters'
    
    return None


def validate_request_size(body: str) -> Optional[str]:
    """
    Validate request body size.
    
    Args:
        body: Request body string
        
    Returns:
        Error message if too large, None if valid
    """
    if len(body) > MAX_REQUEST_SIZE:
        return f'Request body too large (max {MAX_REQUEST_SIZE} bytes)'
    
    return None


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to avoid exposing internal details.
    
    Args:
        error: Exception object
        
    Returns:
        Safe error message string
    """
    # Log the actual error for debugging
    print(f'Internal error: {str(error)}')
    
    # Return generic message to user
    return 'An error occurred processing your request'


def validate_string_length(value: str, max_length: int, field_name: str) -> Optional[str]:
    """
    Validate string length.
    
    Args:
        value: String to validate
        max_length: Maximum allowed length
        field_name: Name of field for error message
        
    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(value, str):
        return f'{field_name} must be a string'
    
    if len(value) > max_length:
        return f'{field_name} must be {max_length} characters or less'
    
    return None
