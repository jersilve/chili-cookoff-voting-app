# Security Documentation

This document outlines the security measures implemented in the Chili Cook-Off Voting Application.

## Security Features

### 1. Data Protection

#### DynamoDB Encryption
- **Encryption at Rest**: All data in DynamoDB is encrypted using AWS KMS
- **Point-in-Time Recovery**: Enabled for data backup and recovery
- **Access Control**: IAM roles restrict access to authorized Lambda functions only

#### Data Validation
- **Input Sanitization**: All user inputs are validated and sanitized
- **Voter ID Validation**: Alphanumeric only, 4-50 characters
- **Entry Name Validation**: Limited character set, max 100 characters
- **Request Size Limits**: Maximum 10KB request body size

### 2. Application Security

#### HTTP Security Headers
All API responses include:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering
- `Strict-Transport-Security` - Enforces HTTPS (when behind HTTPS)
- `Content-Security-Policy` - Restricts resource loading
- `Referrer-Policy` - Controls referrer information

#### Input Validation
- Voter IDs: Alphanumeric characters only (4-50 chars)
- Entry names: Letters, numbers, spaces, hyphens, apostrophes (1-100 chars)
- Request body size: Maximum 10KB
- JSON parsing: Strict validation with error handling

#### Path Traversal Protection
- Static file handler prevents directory traversal attacks
- Path validation blocks `..` and absolute paths
- File access restricted to `/var/task/static/` directory only

### 3. Infrastructure Security

#### Network Security
- **VPC Isolation**: Application runs in isolated VPC
- **Security Groups**: ALB security group allows HTTP (port 80) only
- **Public Subnets**: ALB in public subnets, Lambda functions serverless

#### IAM Security
- **Least Privilege**: Lambda execution role has minimal required permissions
- **DynamoDB Access**: Limited to specific table operations (PutItem, GetItem, Scan, BatchWriteItem)
- **SES Access**: Limited to SendEmail and SendRawEmail
- **CloudWatch Logs**: Automatic logging for audit trail

### 4. Error Handling

#### Secure Error Messages
- Internal errors logged to CloudWatch for debugging
- Generic error messages returned to users (no internal details exposed)
- Stack traces never exposed in API responses

#### Logging
- All Lambda functions log to CloudWatch Logs
- Errors include context for debugging
- No sensitive data (passwords, tokens) logged

## Known Limitations

### 1. No Authentication
- **Impact**: Anyone with the URL can access the application
- **Mitigation**: Share URLs carefully, use for time-limited events only
- **Recommendation**: Deploy just before event, teardown immediately after

### 2. No Rate Limiting
- **Impact**: Potential for vote spam or DoS attacks
- **Mitigation**: Application designed for small events (< 100 participants)
- **Recommendation**: Monitor CloudWatch metrics during event

### 3. HTTP Only (No HTTPS)
- **Impact**: Traffic not encrypted in transit
- **Mitigation**: ALB supports HTTPS but requires SSL certificate
- **Recommendation**: For production use, add ACM certificate and HTTPS listener

### 4. No CORS Restrictions
- **Impact**: Any website can make requests to the API
- **Mitigation**: Application designed for public access
- **Recommendation**: Add CORS headers if needed for specific domains

### 5. Anonymous Voting
- **Impact**: No way to verify voter identity
- **Mitigation**: Voter IDs stored in browser localStorage
- **Design Choice**: Intentional for privacy and simplicity

## Security Best Practices

### For Organizers

1. **URL Management**
   - Keep setup URL private (share with organizers only)
   - Share voting URL only with event participants
   - Display leaderboard URL publicly

2. **Event Lifecycle**
   - Deploy just before your event starts
   - Run teardown immediately after event ends
   - Don't leave application running when not in use

3. **Data Privacy**
   - Don't collect personally identifiable information
   - Entry names should not include personal data
   - Votes are anonymous by design

4. **Monitoring**
   - Check CloudWatch Logs for unusual activity
   - Monitor DynamoDB for unexpected data
   - Review AWS billing for cost anomalies

### For Developers

1. **Code Security**
   - Always validate and sanitize user inputs
   - Use security_utils module for validation
   - Never expose internal error details to users
   - Log errors to CloudWatch for debugging

2. **Dependency Management**
   - Keep Python dependencies up to date
   - Review security advisories for boto3, qrcode, pillow
   - Use `pip install --upgrade` regularly

3. **Testing**
   - Run security tests before deployment
   - Test input validation with malicious inputs
   - Verify error handling doesn't expose internals

4. **Deployment**
   - Review CloudFormation template changes
   - Test in non-production environment first
   - Use version control for all changes

## Incident Response

### If You Suspect a Security Issue

1. **Immediate Actions**
   - Run `./teardown.sh` to remove all resources
   - Check CloudWatch Logs for suspicious activity
   - Review DynamoDB data for anomalies

2. **Investigation**
   - Check AWS CloudTrail for API calls
   - Review ALB access logs (if enabled)
   - Examine Lambda function logs

3. **Remediation**
   - Update affected code
   - Redeploy with fixes
   - Document incident and lessons learned

## Compliance

### Data Retention
- All data deleted when running teardown
- No long-term data storage
- No backup retention (unless manually configured)

### Privacy
- No personally identifiable information collected
- Voter IDs are anonymous
- No tracking or analytics

### Audit Trail
- All Lambda invocations logged to CloudWatch
- DynamoDB operations logged via CloudTrail (if enabled)
- ALB access logs available (if enabled)

## Security Updates

This application is provided as-is for educational and event purposes. For production use:

1. Add HTTPS with ACM certificate
2. Implement authentication (Cognito, OAuth)
3. Add rate limiting (API Gateway, WAF)
4. Enable ALB access logs
5. Enable CloudTrail for audit logging
6. Add monitoring and alerting (CloudWatch Alarms)
7. Implement CORS restrictions
8. Add input validation on frontend
9. Implement CAPTCHA for vote submission
10. Add database backups and disaster recovery

## Reporting Security Issues

If you discover a security vulnerability:

1. Do NOT create a public GitHub issue
2. Document the vulnerability details
3. Include steps to reproduce
4. Suggest potential fixes if possible
5. Contact the maintainer privately

## Security Checklist

Before deploying:
- [ ] Review all Lambda function code
- [ ] Verify input validation is in place
- [ ] Check security headers are set
- [ ] Confirm DynamoDB encryption enabled
- [ ] Review IAM permissions (least privilege)
- [ ] Test error handling (no internal details exposed)
- [ ] Verify path traversal protection
- [ ] Check request size limits
- [ ] Review CloudFormation template
- [ ] Test with malicious inputs

After event:
- [ ] Run teardown script
- [ ] Verify all resources deleted
- [ ] Check for any remaining data
- [ ] Review CloudWatch Logs for issues
- [ ] Document any security incidents

## Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Lambda Security](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)
- [DynamoDB Security](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security.html)
