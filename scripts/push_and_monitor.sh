#!/bin/bash
"""Push changes and monitor CI/bot comments.

This script pushes changes to the current branch and then monitors
CI checks and bot comments for the latest commit.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="kpblcaoo"
REPO_NAME="sboxmgr"
CI_TIMEOUT=10
BOT_TIMEOUT=5

echo -e "${BLUE}🚀 Starting push and monitor process...${NC}"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📋 Current branch: ${CURRENT_BRANCH}${NC}"

# Check if there are changes to push
if ! git diff --quiet HEAD origin/$CURRENT_BRANCH 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Changes detected, pushing to origin/${CURRENT_BRANCH}...${NC}"

    # Push changes
    if git push origin $CURRENT_BRANCH; then
        echo -e "${GREEN}✅ Push successful!${NC}"
    else
        echo -e "${RED}❌ Push failed!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ No changes to push${NC}"
fi

# Get the latest commit SHA
LATEST_COMMIT=$(git rev-parse HEAD)
echo -e "${BLUE}📝 Latest commit: ${LATEST_COMMIT:0:8}${NC}"

# Wait a moment for GitHub to process the push
echo -e "${YELLOW}⏳ Waiting 30 seconds for GitHub to process the push...${NC}"
sleep 30

# Run the monitoring script
echo -e "${BLUE}🔍 Starting CI and bot monitoring...${NC}"
python scripts/monitor_ci_and_bots.py \
    --owner "$REPO_OWNER" \
    --repo "$REPO_NAME" \
    --branch "$CURRENT_BRANCH" \
    --commit "$LATEST_COMMIT" \
    --ci-timeout "$CI_TIMEOUT" \
    --bot-timeout "$BOT_TIMEOUT"

# Check if monitoring was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Monitoring completed successfully!${NC}"

    # Check if bot comments were found
    if [ -f "bot_comments.json" ]; then
        echo -e "${BLUE}🤖 Bot comments found and saved to bot_comments.json${NC}"

        # Display bot comments summary
        echo -e "${BLUE}📋 Bot comments summary:${NC}"
        python -c "
import json
try:
    with open('bot_comments.json', 'r') as f:
        comments = json.load(f)
    for i, comment in enumerate(comments, 1):
        user = comment.get('user', {}).get('login', 'Unknown')
        body = comment.get('body', '')[:150] + '...' if len(comment.get('body', '')) > 150 else comment.get('body', '')
        print(f'  {i}. {user}: {body}')
except Exception as e:
    print(f'Error reading bot comments: {e}')
"
    else
        echo -e "${YELLOW}🤖 No bot comments found${NC}"
    fi
else
    echo -e "${RED}❌ Monitoring failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Push and monitor process completed!${NC}"
