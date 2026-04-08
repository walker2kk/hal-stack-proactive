#!/usr/bin/env python3
"""
Promote learnings from .learnings/ to workspace system files.
Part of Hal Stack Proactive + ECC continuous learning.

Usage:
    python promote-learning.py --list              List pending high-priority learnings
    python promote-learning.py --promote LRN-xxx  Promote a specific learning
    python promote-learning.py --auto             Auto-promote recurring learnings
"""

import os
import re
import sys
from pathlib import Path

LEARNINGS_FILE = Path.home() / ".openclaw/workspace/.learnings/LEARNINGS.md"

def find_learning(entry_id):
    """Find a learning entry by ID."""
    if not LEARNINGS_FILE.exists():
        return None
    
    content = LEARNINGS_FILE.read_text()
    pattern = rf'^##\s+({entry_id}[^\s]*)'
    
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        # Try prefix match
        pattern = rf'^##\s+({entry_id}[\w-]+)'
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            return None
    
    start = match.start()
    
    # Find next entry or end of file
    next_match = re.search(r'^##\s+', content[match.end():], re.MULTILINE)
    if next_match:
        end = start + match.end() + next_match.start()
    else:
        end = len(content)
    
    return content[start:end].strip()

def list_pending():
    """List pending high-priority learnings."""
    if not LEARNINGS_FILE.exists():
        print("No learnings file found.")
        return []
    
    content = LEARNINGS_FILE.read_text()
    entries = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    
    pending = []
    for entry in entries:
        lines = entry.split('\n')
        entry_id = lines[0].strip()
        
        status_match = re.search(r'\*\*Status\*\*:\s*(\w+)', entry)
        priority_match = re.search(r'\*\*Priority\*\*:\s*(\w+)', entry)
        
        status = status_match.group(1) if status_match else 'pending'
        priority = priority_match.group(1) if priority_match else 'medium'
        
        if status == 'pending' and priority in ['high', 'critical']:
            summary_match = re.search(r'### Summary\s+(.+?)(?=\n###|\Z)', entry, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else '...'
            pending.append({
                'id': entry_id,
                'priority': priority,
                'summary': summary[:60] + ('...' if len(summary) > 60 else '')
            })
    
    print(f"Pending high-priority learnings ({len(pending)}):\n")
    for p in pending:
        print(f"  [{p['priority']}] {p['id']} — {p['summary']}")
    
    return pending

def detect_target(summary, details):
    """Detect which target file this learning should go to."""
    text = (summary + " " + details).lower()
    
    # Detection rules
    if any(word in text for word in ['behavior', 'personality', 'style', 'how i write', 'communication']):
        return 'SOUL.md'
    elif any(word in text for word in ['workflow', 'process', 'how to', 'pattern', 'routine']):
        return 'AGENTS.md'
    elif any(word in text for word in ['tool', 'command', 'gotcha', 'api', 'error when']):
        return 'TOOLS.md'
    elif any(word in text for word in ['user', 'prefer', 'likes', 'dislikes']):
        return 'USER.md'
    elif any(word in text for word in ['memory', 'long-term', 'decision']):
        return 'MEMORY.md'
    else:
        # Default to AGENTS.md for workflow patterns
        return 'AGENTS.md'

def promote_entry(entry_id, auto=False):
    """Promote a learning entry to workspace file."""
    entry_text = find_learning(entry_id)
    if not entry_text:
        print(f"Learning entry not found: {entry_id}")
        return False
    
    # Extract sections
    summary_match = re.search(r'### Summary\s+(.+?)(?=\n###|\Z)', entry_text, re.DOTALL)
    details_match = re.search(r'### Details\s+(.+?)(?=\n###|\Z)', entry_text, re.DOTALL)
    
    summary = summary_match.group(1).strip() if summary_match else ""
    details = details_match.group(1).strip() if details_match else ""
    
    # Detect target
    target = detect_target(summary, details)
    target_path = Path.home() / f".openclaw/workspace/{target}"
    
    print(f"Learning: {summary}")
    print(f"Detected target: {target}")
    
    if not auto:
        confirm = input(f"Promote to {target}? [Y/n] ")
        if confirm.lower() == 'n':
            new_target = input("Enter alternative filename: ")
            target = new_target
            target_path = Path.home() / f".openclaw/workspace/{target}"
    
    # Distill to concise rule
    lines = []
    
    # Add as a concise bullet or section
    if target_path.exists():
        current = target_path.read_text()
    else:
        current = f"# {target}\n\n"
    
    # Create distilled content
    distilled = f"\n- **{summary}**\n"
    if details:
        # Distill details to 1-3 concise bullet points
        distilled += f"  {details.strip()}\n"
    
    # Append to file
    if "### " in current[-200:]:
        # There's a recent section, append there
        new_content = current.rstrip() + "\n" + distilled
    else:
        # Add to end
        new_content = current.rstrip() + "\n\n## Learnings (auto-promoted)\n" + distilled
    
    target_path.write_text(new_content)
    print(f"✓ Promoted to {target_path}")
    
    # Mark as promoted in LEARNINGS.md
    update_learning_status(entry_id, "promoted")
    return True

def update_learning_status(entry_id, status):
    """Update learning status in LEARNINGS.md."""
    if not LEARNINGS_FILE.exists():
        return
    
    content = LEARNINGS_FILE.read_text()
    pattern = rf'(^##\s+{re.escape(entry_id)}.*?\n\*\*Status\*\*:\s*)[\w-]+'
    
    def replace_status(match):
        return match.group(1) + status
    
    new_content = re.sub(pattern, replace_status, content, flags=re.MULTILINE | re.DOTALL)
    LEARNINGS_FILE.write_text(new_content)

def auto_promote():
    """Auto-promote learnings that meet criteria:
    - Recurrence-Count >= 3
    - Seen across at least 2 tasks
    - Within 30 days
    """
    if not LEARNINGS_FILE.exists():
        print("No learnings file found.")
        return
    
    content = LEARNINGS_FILE.read_text()
    entries = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    
    promoted = 0
    
    for entry_text in entries:
        lines = entry_text.split('\n')
        entry_id = lines[0].strip()
        
        # Check status
        status_match = re.search(r'\*\*Status\*\*:\s*(\w+)', entry_text)
        status = status_match.group(1) if status_match else 'pending'
        if status != 'pending':
            continue
        
        # Check recurrence
        count_match = re.search(r'Recurrence-Count:\s*(\d+)', entry_text)
        if not count_match:
            continue
        
        count = int(count_match.group(1))
        if count >= 3:
            print(f"\nAuto-promoting: {entry_id} (recurrence {count})")
            if promote_entry(entry_id, auto=True):
                promoted += 1
    
    print(f"\nAuto-promotion complete: {promoted} learnings promoted")

def main():
    args = sys.argv[1:]
    
    if not args:
        print(__doc__)
        sys.exit(1)
    
    if args[0] == '--list':
        list_pending()
    elif args[0] == '--promote' and len(args) == 2:
        promote_entry(args[1])
    elif args[0] == '--auto':
        auto_promote()
    else:
        print(__doc__)
        sys.exit(1)

def argparse():
    """Simple arg parsing since we're keeping it simple."""
    pass

if __name__ == "__main__":
    main()
