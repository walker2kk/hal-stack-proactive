#!/usr/bin/env python3
"""
ECC Continuous Learning - Observer Core
Detects patterns in interactions and learns atomic instincts.
Part of Hal Stack Proactive.

Inspired by: ECC (Self-Improving Agent) by Termo
https://termo.ai/skills/openclaw-continuous-learning
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
INSTINCT_DIR = WORKSPACE / "instincts"
PERSONAL_DIR = INSTINCT_DIR / "personal"
PROJECT_DIR = INSTINCT_DIR / "project"
CACHE_DIR = INSTINCT_DIR / "cache"
INDEX_FILE = INSTINCT_DIR / "index.json"

# Pattern detection patterns
CORRECTION_PATTERNS = [
    r'(no|not|actually|correction|correct).+is',
    r'(i prefer|prefer|i like|i don\'t like)',
    r'(instead|rather|actually).+use',
]

INSTINCT_TEMPLATE = """id: {instinct_id}
pattern: "{pattern}"
confidence: {confidence}
observed_count: {count}
first_seen: {first_seen}
last_seen: {last_seen}
scope: {scope}
summary: "{summary}"
---
"""

def ensure_dirs():
    """Create required directories."""
    for d in [INSTINCT_DIR, PERSONAL_DIR, PROJECT_DIR, CACHE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    if not INDEX_FILE.exists():
        with open(INDEX_FILE, 'w') as f:
            json.dump({"instincts": [], "last_learned": None}, f)

def generate_instinct_id():
    """Generate a unique instinct ID."""
    from uuid import uuid4
    return f"inst_{uuid4().hex[:8]}"

def load_index():
    """Load instinct index."""
    if not INDEX_FILE.exists():
        return {"instincts": [], "last_learned": None}
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def save_index(index):
    """Save instinct index."""
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)

def find_matching_instinct(pattern, scope="personal"):
    """Find an existing instinct that matches this pattern."""
    index = load_index()
    for inst in index["instincts"]:
        if inst["pattern"] == pattern and inst["scope"] == scope:
            return inst
    return None

def extract_pattern_from_message(message):
    """Extract potential instinct pattern from user message."""
    message_lower = message.lower()
    
    # Check for corrections and preferences
    for pat in CORRECTION_PATTERNS:
        if re.search(pat, message_lower):
            # Extract the core preference/correction
            lines = message.split('\n')
            for line in lines:
                line_lower = line.lower()
                for cp in CORRECTION_PATTERNS:
                    if re.search(cp, line_lower):
                        # Return the whole line as the pattern
                        return line.strip()
    return None

def learn_pattern(pattern, scope="personal"):
    """Learn or update confidence for a pattern."""
    existing = find_matching_instinct(pattern, scope)
    now = datetime.now().isoformat()
    
    if existing:
        # Update existing instinct
        existing["observed_count"] += 1
        existing["confidence"] = min(1.0, existing["confidence"] + 0.15)
        existing["last_seen"] = now
        
        # Save updated instinct file
        instinct_path = PERSONAL_DIR if scope == "personal" else PROJECT_DIR
        instinct_file = instinct_path / f"{existing['id']}.yaml"
        
        with open(instinct_file, 'w') as f:
            f.write(INSTINCT_TEMPLATE.format(**existing))
        
        # Update index
        index = load_index()
        for i, inst in enumerate(index["instincts"]):
            if inst["id"] == existing["id"]:
                index["instincts"][i] = existing
                break
        save_index(index)
        
        print(f"✓ Updated instinct: {existing['id']} (confidence: {existing['confidence']:.2f})")
        return existing
    
    else:
        # Create new instinct
        instinct_id = generate_instinct_id()
        summary = pattern[:80] + ("..." if len(pattern) > 80 else "")
        instinct = {
            "id": instinct_id,
            "pattern": pattern,
            "confidence": 0.2,
            "observed_count": 1,
            "first_seen": now,
            "last_seen": now,
            "scope": scope,
            "summary": summary
        }
        
        # Save instinct file
        instinct_path = PERSONAL_DIR if scope == "personal" else PROJECT_DIR
        instinct_file = instinct_path / f"{instinct_id}.yaml"
        
        with open(instinct_file, 'w') as f:
            f.write(INSTINCT_TEMPLATE.format(**instinct))
        
        # Update index
        index = load_index()
        index["instincts"].append(instinct)
        index["last_learned"] = now
        save_index(index)
        
        print(f"✓ New instinct learned: {instinct_id}")
        return instinct

def get_high_confidence(scope="personal", min_confidence=0.7):
    """Get all high-confidence instincts for loading into context."""
    index = load_index()
    high_conf = [
        inst for inst in index["instincts"]
        if inst["confidence"] >= min_confidence and inst["scope"] == scope
    ]
    return sorted(high_conf, key=lambda x: x["confidence"], reverse=True)

def list_instincts():
    """List all instincts with confidence."""
    index = load_index()
    print(f"Total instincts: {len(index['instincts'])}\n")
    
    by_scope = {}
    for inst in index["instincts"]:
        by_scope.setdefault(inst["scope"], []).append(inst)
    
    for scope, instincts in by_scope.items():
        print(f"=== {scope.title()} ({len(instincts)}) ===")
        sorted_inst = sorted(instincts, key=lambda x: x["confidence"], reverse=True)
        for inst in sorted_inst:
            print(f"  [{inst['confidence']:.2f}] {inst['id']} - {inst['summary']}")
        print()

def observe_message(message):
    """Observe a message and learn patterns if found."""
    pattern = extract_pattern_from_message(message)
    if pattern:
        print(f"Found potential pattern: {pattern}")
        learn_pattern(pattern, "personal")
        return True
    return False


def main():
    """CLI entry point."""
    import sys
    
    ensure_dirs()
    
    if len(sys.argv) < 2:
        print("Usage: ecc-observe.py [learn|list|high-confidence|observe] [args]")
        print("")
        print("  learn 'pattern' [scope]  — Learn a pattern (scope: personal/project)")
        print("  list                     — List all instincts")
        print("  high-confidence [min]   — List high-confidence instincts")
        print("  observe 'message'        — Observe message for patterns (hook use)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "learn":
        if len(sys.argv) < 3:
            print("Need pattern argument")
            sys.exit(1)
        pattern = sys.argv[2]
        scope = sys.argv[3] if len(sys.argv) > 3 else "personal"
        learn_pattern(pattern, scope)
    
    elif command == "list":
        list_instincts()
    
    elif command == "high-confidence":
        min_conf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
        instincts = get_high_confidence(min_confidence=min_conf)
        print(f"High-confidence instincts (>{min_conf}): {len(instincts)}\n")
        for inst in instincts:
            print(f"- {inst['pattern']} (confidence: {inst['confidence']:.2f})")
    
    elif command == "observe":
        if len(sys.argv) < 3:
            print("Need message argument")
            sys.exit(1)
        message = sys.argv[2]
        observe_message(message)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
