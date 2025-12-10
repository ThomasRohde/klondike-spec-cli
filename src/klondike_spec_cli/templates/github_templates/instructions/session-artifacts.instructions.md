---
description: "Long-running agent session management and context bridging"
applyTo: "**/agent-progress.md,**/.klondike/features.json,**/.klondike/agent-progress.json"
---

# Session Artifact Instructions

These files are critical infrastructure for multi-context-window agent workflows. Handle with care.

> **⚠️ CRITICAL**: The klondike CLI is the **only** interface for these artifacts. 
> - **Never read** `.klondike/features.json`, `.klondike/agent-progress.json`, or `agent-progress.md` directly
> - **Always use** `klondike` commands to access project state
> - The CLI output is the canonical source of truth

## agent-progress.md

### Purpose
Bridge context between agent sessions. Each agent starts fresh and uses this file to understand what happened before.

### Management

This file is **auto-generated** by the klondike CLI from `.klondike/agent-progress.json`. Use these commands:

```bash
klondike session start --focus "F00X - description"  # Start session
klondike session end --summary "..." --next "..."    # End session
klondike progress                                     # Regenerate file
```

**Do not manually edit** - changes will be overwritten by the CLI.

## .klondike/features.json

### Purpose
Prevent premature "victory declaration" by maintaining a structured checklist of all features, with explicit status tracking and verification evidence.

### Management

This file is managed **exclusively** by the klondike CLI. 

**To access feature data, use these commands:**

```bash
klondike status                    # Project overview with feature counts
klondike feature list              # List all features with status
klondike feature list --json       # Full feature data as JSON
klondike feature show F00X         # Detailed view of one feature
```

**To modify feature state, use these commands:**

```bash
klondike feature add "description" --category X --criteria "..." --notes "Implementation guidance"  # Add feature
klondike feature start F00X                                        # Mark in-progress
klondike feature verify F00X --evidence "..."                      # Mark verified
klondike feature block F00X --reason "..."                         # Mark blocked
```

> **Note**: Always use `--notes` when adding features. Include implementation hints, edge cases,
> dependencies, and gotchas. This helps weaker agents implement features correctly.

> **⚠️ FORBIDDEN**: Do not read `.klondike/features.json` directly using file read tools.
> Use `klondike feature list --json` if you need the raw JSON data.

### CLI Commands for State Changes

**Starting Work:**
```bash
klondike feature start F00X
```
Sets `status: "in-progress"` and `lastWorkedOn` timestamp.

**Verifying (after E2E testing):**
```bash
klondike feature verify F00X --evidence "test-results/F00X.png" --notes "Tested on Chrome/Firefox"
```
Sets `status: "verified"`, `passes: true`, `verifiedAt`, and `evidenceLinks`.

**Blocking:**
```bash
klondike feature block F00X --reason "Waiting for API integration"
```
Sets `status: "blocked"` and `blockedBy` reason.

### Verification Requirements

Before setting `passes: true` and `status: verified`:
1. All acceptance criteria must be tested
2. Tests must be end-to-end (not just unit tests)
3. Tests must be on the actual running system
4. Edge cases should be considered
5. **Evidence must be captured and linked**

### Evidence Requirements

- Save evidence files to `test-results/` directory
- Naming: `F00X-<description>.{png,log,txt}`
- Add paths to `evidenceLinks` array via CLI command

## Why This Matters

Without these artifacts:
- Agents don't know what was done before
- Agents declare "done" too early
- Features get left half-implemented
- Same work gets redone across sessions
- Quality degrades over time

With these artifacts:
- Clear handoffs between sessions
- Objective completion criteria
- Traceable progress history
- Consistent quality standards
