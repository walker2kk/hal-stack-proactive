#!/bin/bash
#
# ECC Continuous Learning - Observer Hook
# Runs after each user message to observe and learn patterns
# Part of Hal Stack Proactive
#

set -e

# Configuration
WORKSPACE_ROOT=~/.openclaw/workspace
INSTINCTS_PERSONAL="$WORKSPACE_ROOT/instincts/personal"
INSTINCTS_PROJECT="$WORKSPACE_ROOT/instincts/project"
OBSERVATION_CACHE="$WORKSPACE_ROOT/instincts/cache/latest observation"

# Create directories if they don't exist
mkdir -p "$INSTINCTS_PERSONAL" "$INSTINCTS_PROJECT" "$WORKSPACE_ROOT/instincts/cache"

# This hook is called after each user message
# It extracts potential patterns and updates instinct confidence

# Get the last interaction from conversation history
# (In actual OpenClaw hook, this would receive the conversation context)
# For now, we just log that observation happened

echo "[$(date -Iseconds)] ECC Observer: Running observation check" > "$OBSERVATION_CACHE"

# Check for patterns that should be learned
# This is where pattern detection happens
# Full implementation would:
# 1. Analyze user corrections and preferences
# 2. Extract atomic patterns
# 3. Increase confidence when pattern repeats
# 4. Auto-promote to system files when confidence > threshold

python3 "$(dirname "$0")/../../scripts/ecc-observe.py" "$@"

exit 0
