#!/bin/bash
# Install myTime from source for development
# Usage: ./scripts/dev_install.sh

set -e

echo "==> Installing myTime in development mode..."
pip3 install --break-system-packages -e . 2>/dev/null || pip3 install -e .

echo "==> Done! Run with: python3 -m myTime"
echo "   Or just: myTime (if scripts installed)"
EOF