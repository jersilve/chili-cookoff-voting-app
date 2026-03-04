import json
import os
import mimetypes
from security_utils import sanitize_error_message

# Initialize mimetypes
mimetypes.init()


def lambda_handler(event, context):
    """
    Static Content Handler Lambda function for Chili Cook-Off Voting Application.
    
    Serves HTML, JavaScript, and CSS files from the Lambda deployment package.
    Parses ALB request path to determine requested file and sets appropriate Content-Type headers.
    
    Args:
        event: ALB request event containing path information
        context: Lambda context object
        
    Returns:
        ALB-formatted response with file content or 404 error
    """
    try:
        # Parse ALB request path
        path = event.get('path', '')
        
        # Remove /static/ prefix if present
        if path.startswith('/static/'):
            path = path[8:]  # Remove '/static/' (8 characters)
        elif path.startswith('/'):
            path = path[1:]  # Remove leading '/'
        
        # Prevent path traversal attacks
        if '..' in path or path.startswith('/'):
            return create_response(404, 'File not found', 'text/plain')
        
        # Default to index.html if path is empty
        if not path:
            path = 'index.html'
        
        # Determine file path in Lambda package
        # Support both Lambda runtime (/var/task/static) and local testing (lambda/static)
        lambda_path = os.path.join('/var/task/static', path)
        local_path = os.path.join(os.path.dirname(__file__), 'static', path)
        
        if os.path.exists(lambda_path):
            file_path = lambda_path
        elif os.path.exists(local_path):
            file_path = local_path
        else:
            return create_response(404, 'File not found', 'text/plain')
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return create_response(404, 'File not found', 'text/plain')
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine Content-Type based on file extension
        content_type = get_content_type(path)
        
        # Return success response with file content
        return create_response(200, content, content_type)
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = sanitize_error_message(e)
        return create_response(500, error_msg, 'text/plain')


def get_content_type(file_path):
    """
    Determine Content-Type header based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Content-Type string (e.g., 'text/html', 'application/javascript', 'text/css')
    """
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Map common extensions to Content-Type
    content_type_map = {
        '.html': 'text/html',
        '.htm': 'text/html',
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.txt': 'text/plain'
    }
    
    # Return mapped Content-Type or use mimetypes as fallback
    if ext in content_type_map:
        return content_type_map[ext]
    
    # Use mimetypes module as fallback
    guessed_type, _ = mimetypes.guess_type(file_path)
    return guessed_type or 'application/octet-stream'


def create_response(status_code, body, content_type):
    """
    Create ALB-formatted response with security headers.
    
    Args:
        status_code: HTTP status code
        body: Response body content
        content_type: Content-Type header value
        
    Returns:
        ALB-formatted response dictionary
    """
    # Get base security headers
    headers = {
        'Content-Type': content_type,
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Add CSP for HTML files
    if content_type == 'text/html':
        headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }
