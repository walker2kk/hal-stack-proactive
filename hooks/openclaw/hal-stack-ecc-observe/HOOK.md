---
name: hal-stack-ecc-observe
description: "ECC Continuous Learning — Observe user messages after receiving to learn patterns"
metadata:
  openclaw:
    emoji: "🧠"
    events: ["message:received"]
    requires:
      bins: ["python3"]
---

# Hal Stack ECC Observer

Runs after receiving a user message, automatically extracts patterns and learns instincts for ECC Continuous Learning.

**Requires:** Hal Stack Proactive installed.
