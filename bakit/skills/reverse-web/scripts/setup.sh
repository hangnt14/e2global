#!/bin/bash
# setup.sh — Install dependencies and Playwright chromium for reverse-web skill
# Usage: bash skills/reverse-web/scripts/setup.sh

set -e

cd "$(dirname "$0")/.."

echo "Installing npm dependencies..."
npm install

echo "Installing Playwright chromium..."
# On Linux CI, may need: PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install --with-deps chromium
npx playwright install chromium

echo ""
echo "✓ Setup complete."
echo ""
echo "Usage:"
echo "  node scripts/crawl.js <url> --consent"
echo "  node scripts/crawl.js <url> --consent --max-pages 50"
echo "  node scripts/crawl.js <url> --consent --continue"
echo ""
echo "Run tests:"
echo "  npm run test:unit"
echo "  npm run test:integration  (requires display on Linux)"
