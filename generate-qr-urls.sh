#!/bin/bash

# Generate QR code URLs for online generation
# This script provides URLs that can be used with online QR code generators
# No dependencies required - works in any environment

if [ -z "$1" ]; then
    echo "Usage: $0 <ALB_URL>"
    echo "Example: $0 http://chili-cookoff-alb-123456789.us-east-1.elb.amazonaws.com"
    exit 1
fi

BASE_URL="$1"

echo "========================================="
echo "QR Code Generation URLs"
echo "========================================="
echo ""
echo "Use these URLs with an online QR code generator:"
echo "Recommended: https://www.qr-code-generator.com/"
echo ""
echo "----------------------------------------"
echo "Setup Page:"
echo "${BASE_URL}/static/setup.html"
echo ""
echo "QR Code Generator Link:"
echo "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/setup.html"
echo ""
echo "----------------------------------------"
echo "Voting Page:"
echo "${BASE_URL}/static/vote.html"
echo ""
echo "QR Code Generator Link:"
echo "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/vote.html"
echo ""
echo "----------------------------------------"
echo "Leaderboard Page:"
echo "${BASE_URL}/static/leaderboard.html"
echo ""
echo "QR Code Generator Link:"
echo "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/leaderboard.html"
echo ""
echo "========================================="
echo ""
echo "To download QR codes directly (requires curl):"
echo ""
echo "curl -o setup_qr.png 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/setup.html'"
echo "curl -o voting_qr.png 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/vote.html'"
echo "curl -o leaderboard_qr.png 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${BASE_URL}/static/leaderboard.html'"
echo ""
