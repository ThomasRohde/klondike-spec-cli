---
description: "Long-running agent session management and context bridging"
applyTo: "**/agent-progress.md,**/.klondike/features.json,**/.klondike/agent-progress.json"
---

# Session Artifact Instructions

These files are critical infrastructure for multi-context-window agent workflows. Handle with care.

> **Note**: The klondike CLI manages these artifacts. Use `klondike` commands instead of manual editing.

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

### What Gets Generated

```markdown
### Session N - <Date>
**Duration**: ~X hours
**Focus**: <feature ID and name>

#### Completed
- <bullet list of accomplishments>

#### Attempted But Incomplete
- <what didn't work and why>

#### Blockers Discovered
- <any issues needing resolution>

#### Recommended Next Steps
1. <most important>
2. <second priority>
3. <third priority>

#### Technical Notes
- <non-obvious decisions>
- <gotchas for next session>
```

## .klondike/features.json

### Purpose
Prevent premature "victory declaration" by maintaining a structured checklist of all features, with explicit status tracking and verification evidence.

### Management

This file is managed by the klondike CLI. Use these commands:

```bash
klondike feature add "description" --category X --criteria "..."  # Add feature
klondike feature start F00X                                        # Mark in-progress
klondike feature verify F00X --evidence "..."                      # Mark verified
klondike feature block F00X --reason "..."                         # Mark blocked
klondike feature list                                              # List all
klondike feature show F00X                                         # Show details
```

**Do not manually edit** - use CLI commands to ensure artifact integrity.

### Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Pattern `F\d{3}` (e.g., F001) |
| `description` | string | ✅ | Feature description |
| `acceptanceCriteria` | string[] | ✅ | Testable criteria (min 1) |
| `passes` | boolean | ✅ | Whether feature is verified complete |
| `status` | enum | ✅ | `not-started`, `in-progress`, `blocked`, `verified` |
| `verifiedAt` | string/null | - | ISO timestamp of verification |
| `verifiedBy` | string/null | - | Identifier of verifying agent/session |
| `evidenceLinks` | string[] | - | Paths to verification evidence files |
| `blockedBy` | string/string[] | - | Feature IDs or reason blocking progress |
| `lastWorkedOn` | string | - | ISO timestamp of last work |
| `notes` | string | - | Context, gotchas, or additional info |

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
- Add paths to `evidenceLinks` array in feature entry
- Update `agent-progress.md` with verification record

### Example Update

```json
// Before
{
  "id": "F003",
  "description": "User can log in",
  "status": "in-progress",
  "passes": false,
  "lastWorkedOn": "2024-01-14T10:00:00Z",
  "notes": "Auth endpoint ready, need E2E test"
}

// After (only if verified with evidence)
{
  "id": "F003",
  "description": "User can log in",
  "status": "verified",
  "passes": true,
  "verifiedAt": "2024-01-15T14:30:00Z",
  "verifiedBy": "coding-agent-session-5",
  "evidenceLinks": [
    "test-results/F003-login-success.png",
    "test-results/F003-validation-error.png"
  ],
  "notes": "Tested Chrome/Firefox. Rate limiting works."
}
```

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
