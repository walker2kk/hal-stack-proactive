#!/usr/bin/env python3
"""
Memory tiering organizer for Hal Stack Proactive.
Implements three-tier memory architecture: HOT/WARM/COLD.
Automatically reorganizes memory after compaction.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Tier definitions
BASE_DIR = Path.home() / ".openclaw/workspace"
HOT_DIR = BASE_DIR / "memory/hot"
WARM_DIR = BASE_DIR / "memory/warm"
COLD_FILE = BASE_DIR / "MEMORY.md"

def ensure_directories():
    """Create tier directories if they don't exist."""
    HOT_DIR.mkdir(parents=True, exist_ok=True)
    WARM_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directories created/verified:\n  - {HOT_DIR}\n  - {WARM_DIR}")

def get_daily_logs():
    """Get list of daily log files."""
    memory_dir = BASE_DIR / "memory"
    logs = []
    for f in memory_dir.glob("????-??-??.md"):
        if f.is_file():
            logs.append(f)
    return sorted(logs, reverse=True)

def organize_memory():
    """Main organization process."""
    print("=== Memory Tiering Organization ===\n")
    
    ensure_directories()
    
    # 1. Read all daily logs
    logs = get_daily_logs()
    print(f"\nFound {len(logs)} daily memory logs")
    
    # 2. Classify by recency
    today = datetime.now().date()
    
    hot_count = 0
    warm_count = 0
    
    for log in logs:
        # Parse date from filename
        try:
            date_str = log.stem
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            days_ago = (today - log_date).days
            
            if days_ago <= 2:
                # HOT: Last 2 days - keep in hot for immediate access
                target = HOT_DIR / log.name
                if not target.exists():
                    # Copy to HOT (keep original for backwards compatibility)
                    content = log.read_text()
                    target.write_text(content)
                    hot_count += 1
            else:
                # WARM: Older than 2 days but still relevant - move to warm
                target = WARM_DIR / log.name
                if not target.exists():
                    content = log.read_text()
                    target.write_text(content)
                    warm_count += 1
                
        except ValueError:
            # Not a valid date log, skip
            continue
    
    print(f"\n✓ Organization complete:")
    print(f"  - HOT: {hot_count} files (last 2 days)")
    print(f"  - WARM: {warm_count} files (older than 2 days)")
    print(f"  - COLD: {COLD_FILE} (curated long-term memory)")
    
    print("\n👉 Next steps:")
    print("  1. Review COLD (MEMORY.md) and distill new learnings")
    print("  2. Remove stale content from HOT/WARM")

def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: memory-tiering.py [organize|status|clean]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "organize":
        organize_memory()
    elif command == "status":
        ensure_directories()
        hot_files = list(HOT_DIR.glob("*.md"))
        warm_files = list(WARM_DIR.glob("*.md"))
        print(f"Status:\n  HOT: {len(hot_files)} files\n  WARM: {len(warm_files)} files")
    elif command == "clean":
        print("Clean not implemented - manually remove stale files")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
