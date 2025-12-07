---
description: "Long-running agent session management and context bridging"
applyTo: "**/agent-progress.md,**/features.json"
---

# Session Artifact Instructions

These files are critical infrastructure for multi-context-window agent workflows. Handle with care.

## agent-progress.md

### Purpose
Bridge context between agent sessions. Each agent starts fresh and uses this file to understand what happened before.

### Rules

**DO:**
- Append new session entries at the end
- Be specific about what was accomplished
- List files that were changed
- Include concrete next steps
- Note any gotchas or surprises

**DON'T:**
- Delete or modify previous session entries
- Be vague ("made progress")
- Leave out important context
- Forget to update before ending session

### Structure

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

## features.json

### Purpose
Prevent premature "victory declaration" by maintaining a structured checklist of all features, with explicit status tracking and verification evidence.

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

### Rules

**Allowed Changes:**
- Set `status` (`not-started` → `in-progress` → `blocked` | `verified`)
- Set `passes` from `false` to `true` (after verification)
- Set `verifiedAt` to ISO timestamp
- Set `verifiedBy` to session identifier
- Set `evidenceLinks` with paths to evidence files
- Set `blockedBy` when blocked
- Set `lastWorkedOn` timestamp
- Add/update `notes`
- Update `metadata.lastUpdated`
- Update `metadata.passingFeatures` count

**Forbidden Changes:**
- Deleting features
- Editing `description` field
- Editing `acceptanceCriteria`
- Changing `id` or `priority`
- Setting `passes: true` without end-to-end verification
- Setting `status: verified` without `evidenceLinks`

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
