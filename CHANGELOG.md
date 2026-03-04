# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-03-04

### Added
- Initial release of Chili Cook-Off Voting Application
- Setup interface for configuring competition entries
- Voting interface with ranked choice voting (top 3)
- Real-time leaderboard with automatic updates
- Anonymous voter ID system for vote tracking and updates
- Multi-voter support for families (multiple voters per device)
- Event title customization
- Automatic QR code generation for all URLs
- CloudShell deployment support
- Comprehensive security improvements:
  - Input validation and sanitization
  - Security headers on all responses
  - DynamoDB encryption at rest
  - Request size limits
  - Error message sanitization
- Unit tests and property-based tests
- CloudFormation infrastructure as code
- Automated deployment and teardown scripts
- Documentation:
  - Main README with full instructions
  - CloudShell deployment guide
  - Deployment options comparison
  - Security review and documentation
  - S3 upload commands reference

### Security
- Added security_utils.py for centralized validation
- Implemented security headers (CSP, X-Frame-Options, etc.)
- Added DynamoDB encryption with KMS
- Enabled point-in-time recovery for DynamoDB
- Input validation for all user-provided data
- Request size limits (10KB max)
- Sanitized error messages to prevent information leakage

### Infrastructure
- AWS Lambda functions for all API endpoints
- DynamoDB for data persistence
- Application Load Balancer for routing
- CloudFormation for automated provisioning
- S3 for Lambda deployment packages

## [Unreleased]

### Planned
- Additional voting algorithms (Borda count, instant runoff)
- Admin authentication for setup page
- Vote export functionality
- Historical event tracking
- Mobile app version
- Real-time notifications
- Custom branding options
