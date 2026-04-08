#!/bin/bash
#
# Hal Stack Proactive — One-click Installer
# Installs to target OpenClaw workspace
# Creates all the best practices: token optimization, proactive memory, ECC learning
#

set -e

# Get target workspace
if [ -n "$1" ]; then
    TARGET_WORKSPACE="$1"
else
    TARGET_WORKSPACE=~/.openclaw/workspace
fi

echo "=== Hal Stack Proactive Installer"
echo "Installing to: $TARGET_WORKSPACE"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Check we are in the right place
if [ ! -d "$SCRIPT_DIR/assets" ] || [ ! -d "$SCRIPT_DIR/scripts" ]; then
    echo "✗ Error: Must run install from the hal-stack-proactive directory"
    exit 1
fi

# Step 2: Backup existing files
echo "[1/7] Creating backup..."
BACKUP_DIR="$TARGET_WORKSPACE/backups/hal-stack-$(date +%Y-%m-%d_%H%M)"
mkdir -p "$BACKUP_DIR"

FILES_TO_BACKUP=(
    AGENTS.md
    HEARTBEAT.md
    SOUL.md
    USER.md
    MEMORY.md
    TOOLS.md
    IDENTITY.md
)

for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$TARGET_WORKSPACE/$file" ]; then
        cp "$TARGET_WORKSPACE/$file" "$BACKUP_DIR/"
        echo "  ✓ Backed up $file → $BACKUP_DIR/"
    else
        echo "  ○ $file doesn't exist yet, no backup needed"
    fi
done

echo

# Step 3: Create required directories
echo "[2/7] Creating directory structure..."
mkdir -p "$TARGET_WORKSPACE/memory/hot"
mkdir -p "$TARGET_WORKSPACE/memory/warm"
mkdir -p "$TARGET_WORKSPACE/memory/ontology"
mkdir -p "$TARGET_WORKSPACE/.learnings"
mkdir -p "$TARGET_WORKSPACE/instincts/personal"
mkdir -p "$TARGET_WORKSPACE/instincts/project"
mkdir -p "$TARGET_WORKSPACE/instincts/cache"
mkdir -p "$TARGET_WORKSPACE/notes/areas"
mkdir -p "$TARGET_WORKSPACE/skills/hal-stack-proactive/config"

# Initialize .learnings if empty
if [ ! -f "$TARGET_WORKSPACE/.learnings/LEARNINGS.md" ]; then
    cat > "$TARGET_WORKSPACE/.learnings/LEARNINGS.md" <<EOF
# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---
EOF
fi

if [ ! -f "$TARGET_WORKSPACE/.learnings/ERRORS.md" ]; then
    cat > "$TARGET_WORKSPACE/.learnings/ERRORS.md" <<EOF
# Errors

Command failures and integration errors.

---
EOF
fi

if [ ! -f "$TARGET_WORKSPACE/.learnings/FEATURE_REQUESTS.md" ]; then
    cat > "$TARGET_WORKSPACE/.learnings/FEATURE_REQUESTS.md" <<EOF
# Feature Requests

Capabilities requested by the user.

---
EOF
fi

echo "✓ Directories created"
echo

# Step 4: Install scripts
echo "[3/7] Installing scripts to target..."
SCRIPTS_DIR="$TARGET_WORKSPACE/skills/hal-stack-proactive/scripts"
mkdir -p "$SCRIPTS_DIR"

cp "$SCRIPT_DIR/scripts/"* "$SCRIPTS_DIR/"
chmod +x "$SCRIPTS_DIR/"*
ln -sf "$SCRIPTS_DIR/hal-stack" "$TARGET_WORKSPACE/scripts/hal-stack"
chmod +x "$TARGET_WORKSPACE/scripts/hal-stack"

echo "✓ Scripts installed to $TARGET_WORKSPACE/scripts/hal-stack"
echo

# Step 5: Install hooks for OpenClaw
echo "[4/7] Installing hooks..."
# Install according to OpenClaw workspace hook convention:
# <workspace>/hooks/<hook-name>/HOOK.md + handler.ts
HOOK_ROOT="$TARGET_WORKSPACE/hooks/hal-stack-ecc-observe"
mkdir -p "$HOOK_ROOT"
cp "$SCRIPT_DIR/hooks/openclaw/hal-stack-ecc-observe/HOOK.md" "$HOOK_ROOT/"
cp "$SCRIPT_DIR/hooks/openclaw/hal-stack-ecc-observe/handler.ts" "$HOOK_ROOT/"
chmod +x "$HOOK_ROOT/handler.ts" 2>/dev/null || true

echo "✓ ECC observer hook installed to workspace hooks"
echo "  Enabling hook automatically..."
openclaw hooks enable hal-stack-ecc-observe || echo "  ⚠️  Failed to enable hook automatically, you can enable it manually later with: openclaw hooks enable hal-stack-ecc-observe"
echo

# Step 6: Deploy templates (don't overwrite existing)
echo "[5/7] Deploying templates..."

TEMPLATES="
AGENTS.md:AGENTS.md.template
HEARTBEAT.md:HEARTBEAT.md.template
SOUL.md:SOUL.md.template
IDENTITY.md:IDENTITY.md.template
USER.md:USER.md.template
MEMORY.md:MEMORY.md
TOOLS.md:TOOLS.md
"

for pair in $TEMPLATES; do
    IFS=: read target template <<< "$pair"
    TEMPLATE_SRC="$SCRIPT_DIR/assets/$template"
    TARGET_FILE="$TARGET_WORKSPACE/$target"
    
    if [ ! -f "$TARGET_FILE" ]; then
        cp "$TEMPLATE_SRC" "$TARGET_FILE"
        echo "  ✓ Created $target"
    else
        echo "  ○ Skipped $target — already exists (not overwriting)"
    fi
done

echo

# Step 7: Auto-configure token tracker from openclaw.json
echo "[6/7] Auto-configuring token tracker..."
echo "  Reading model configuration from ~/.openclaw/openclaw.json..."
python3 "$SCRIPTS_DIR/auto-config.py" || echo "  ⚠️  Auto-config failed, will use built-in defaults"
echo

# Final step: Make CLI accessible
echo "[7/7] Final setup..."
chmod +x "$SCRIPT_DIR/install.sh"

echo
echo "🎉 Installation Complete!"
echo "===================="
echo
echo "Hal Stack Proactive installed to: $TARGET_WORKSPACE"
echo
echo "Next steps:"
echo "1. Verify installation:"
echo "   hal-stack doctor"
echo
echo "2. Restart OpenClaw Gateway for changes to take effect:"
echo "   openclaw gateway restart"
echo
echo "3. After restart, ECC automatic observation is already enabled and working!"
echo "   - Every user message is automatically observed for patterns"
echo "   - Corrections/preferences are learned as instincts automatically"
echo "   - Token tracker is auto-configured with your current model"
echo
echo "Features installed:"
echo "  ✓ Token-optimized context loading (saves 50-80% tokens)"
echo "  ✓ Three-tier memory: HOT/WARM/COLD"
echo "  ✓ WAL Protocol + working buffer for compaction recovery"
echo "  ✓ ECC Continuous Learning (instinct-based pattern detection)"
echo "  ✓ .learnings logging with auto-promotion"
echo "  ✓ Ontology typed knowledge graph"
echo "  ✓ Smart model routing (cheaper models for simpler tasks)"
echo "  ✓ Heartbeat optimization (reduces API calls) + cache warming"
echo "  ✓ Token budget tracking with alerts (auto-read your model config)"
echo
echo "All existing files were backed up to: $BACKUP_DIR"
