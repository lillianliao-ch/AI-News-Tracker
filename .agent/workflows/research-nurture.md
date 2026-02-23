---
description: 3-Step Research Talent Cold Start Nurturing Workflow (Connect -> Message -> Email)
---
# Research Talent Nurturing Workflow

This workflow implements a "low pressure" cold start process to build long-term connections with top-tier research talent.

## Philosophy
1.  **Stage 1 (Connect)**: Zero pressure. "I read your paper X."
2.  **Stage 2 (Message)**: 3-5 days later. Add value/insight. No ask.
3.  **Stage 3 (Email)**: 7-14 days later. Soft ask on openness.

## Daily SOP (Standard Operating Procedure)

### 1. Check Status
Review the dashboard to see who is due for action today.
```bash
python3 nurture_tracker.py status
```

### 2. Import New Candidates
bulk import S-tier candidates into the pending pool.
```bash
python3 nurture_tracker.py import --tier S
```

### 3. Execution

**Stage 1: Generate Connection Requests**
```bash
# Generate content
python3 nurture_tracker.py generate-connect

# (Manually send on LinkedIn)

# Mark as sent
python3 nurture_tracker.py mark-sent <ID> stage1
```

**Stage 2: Process Accepted Connections**
When you see someone accepted your request on LinkedIn:
```bash
# Triggers the 3-day cooldown timer
python3 nurture_tracker.py mark-accepted <ID>
```

**Stage 2: Send Follow-up Messages**
For those whose cooldown timer has expired (Due Today):
```bash
# Generate content
python3 nurture_tracker.py generate-message

# (Manually send on LinkedIn)

# Mark as sent (Triggers Stage 3 timer)
python3 nurture_tracker.py mark-sent <ID> stage2
```

**Stage 3: Send Final Email**
For those whose Stage 3 timer has expired:
```bash
# Generate content
python3 nurture_tracker.py generate-email

# (Manually send via Email)

# Mark as sent (Move to Long Term Pool)
python3 nurture_tracker.py mark-sent <ID> stage3
```
