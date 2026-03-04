#!/bin/bash

# Lightweight QR code dependency installer for CloudShell
# This script installs only the minimal dependencies needed for QR code generation

set -e

echo "========================================="
echo "Installing QR Code Dependencies"
echo "========================================="
echo ""

# Check available space
echo "Checking available disk space..."
df -h ~ | tail -1
echo ""

# Install qrcode with minimal dependencies
echo "Installing qrcode library (minimal)..."
pip3 install --user --no-cache-dir qrcode[pil] 2>&1 | grep -v "Requirement already satisfied" || true

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "You can now run ./deploy.sh and QR codes will be generated."
echo ""
echo "Note: If you run out of space, you can skip QR code generation"
echo "and use online QR code generators instead."
echo ""
