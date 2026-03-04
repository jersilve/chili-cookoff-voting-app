"""
Unit tests for Static Content Handler Lambda function.

Tests cover:
- Serving HTML files with correct Content-Type
- Serving JavaScript files with correct Content-Type
- Serving CSS files with correct Content-Type
- 404 response for non-existent files
- Path traversal attack prevention
"""

import pytest
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from static_handler import lambda_handler, get_content_type, create_response


class TestStaticHandler:
    """Test suite for Static Content Handler."""
    
    def test_serve_html_file(self):
        """Test serving HTML file with correct Content-Type."""
        event = {
            'path': '/static/setup.html'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/html'
        assert 'body' in response
        assert len(response['body']) > 0
    
    def test_serve_css_file(self):
        """Test serving CSS file with correct Content-Type."""
        event = {
            'path': '/static/styles.css'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/css'
        assert 'body' in response
    
    def test_serve_file_without_static_prefix(self):
        """Test serving file when path doesn't have /static/ prefix."""
        event = {
            'path': '/setup.html'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/html'
    
    def test_404_for_nonexistent_file(self):
        """Test 404 response for non-existent file."""
        event = {
            'path': '/static/nonexistent.html'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 404
        assert response['body'] == 'File not found'
        assert response['headers']['Content-Type'] == 'text/plain'
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention."""
        event = {
            'path': '/static/../../../etc/passwd'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 404
        assert response['body'] == 'File not found'
    
    def test_path_traversal_with_dots(self):
        """Test path traversal prevention with .. in path."""
        event = {
            'path': '/static/../../sensitive.txt'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 404
    
    def test_default_to_index_html(self):
        """Test that empty path defaults to index.html."""
        event = {
            'path': '/static/'
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        # Should attempt to serve index.html (which doesn't exist in our case)
        assert response['statusCode'] == 404
    
    def test_get_content_type_html(self):
        """Test Content-Type detection for HTML files."""
        content_type = get_content_type('test.html')
        assert content_type == 'text/html'
    
    def test_get_content_type_css(self):
        """Test Content-Type detection for CSS files."""
        content_type = get_content_type('styles.css')
        assert content_type == 'text/css'
    
    def test_get_content_type_javascript(self):
        """Test Content-Type detection for JavaScript files."""
        content_type = get_content_type('app.js')
        assert content_type == 'application/javascript'
    
    def test_get_content_type_unknown(self):
        """Test Content-Type detection for unknown file types."""
        content_type = get_content_type('file.unknown')
        assert content_type == 'application/octet-stream'
    
    def test_create_response(self):
        """Test response creation helper function."""
        response = create_response(200, 'test body', 'text/plain')
        
        assert response['statusCode'] == 200
        assert response['body'] == 'test body'
        assert response['headers']['Content-Type'] == 'text/plain'
    
    def test_error_handling(self):
        """Test error handling for unexpected exceptions."""
        # Create an event that will cause an error during file reading
        event = {
            'path': None  # This should cause an error
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        # Should return 500 error
        assert response['statusCode'] == 500
        assert 'error' in response['body'].lower()
