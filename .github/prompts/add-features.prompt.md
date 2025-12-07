---
name: add-features
description: "Expand the feature registry with new well-structured features"
---

# Goal

Expand `features.json` with new, well-structured feature definitions that follow the project's standards and prevent premature completion.

## Context

From Anthropic's research: A comprehensive feature list prevents agents from "declaring victory too early." Features should be granular enough to be completed in a single session, with clear acceptance criteria that can be objectively verified.

## Instructions

### 1. Review Existing Features

Read `features.json` to understand:
- Current feature structure
- ID numbering scheme
- Categories in use
- Priority levels used
- Style of acceptance criteria

### 2. Analyze New Requirements

Based on user input, identify:
- Distinct capabilities to add
- Dependencies between features
- Appropriate granularity (not too big, not too small)
- Related existing features

### 3. Structure New Features

Each feature must have:

```json
{
  "id": "F0XX",
  "category": "core|ui|api|testing|infrastructure|docs|security|performance",
  "priority": 1-5,
  "description": "Clear, concise description of the feature",
  "dependencies": ["F0YY", "F0ZZ"],
  "acceptanceCriteria": [
    "Specific, testable criterion 1",
    "Specific, testable criterion 2",
    "At least 3 criteria per feature"
  ],
  "estimatedEffort": "small|medium|large",
  "status": "not-started",
  "passes": false,
  "verifiedAt": null,
  "verifiedBy": null,
  "evidenceLinks": [],
  "blockedBy": null,
  "lastWorkedOn": null,
  "notes": null
}
```

**Status values:**
- `not-started`: Feature has not been worked on
- `in-progress`: Currently being implemented
- `blocked`: Cannot proceed (set `blockedBy`)
- `verified`: Complete with evidence (set `passes: true`)

### 4. Acceptance Criteria Guidelines

Good criteria are:
- ✅ **Specific**: "User can click 'Save' and see a success toast"
- ✅ **Testable**: "API returns 200 with JSON body containing 'id' field"
- ✅ **Observable**: "Log file contains entry with timestamp"

Bad criteria are:
- ❌ **Vague**: "Works correctly"
- ❌ **Unmeasurable**: "Fast enough"
- ❌ **Subjective**: "Looks good"

### 5. Granularity Guidelines

**Too Big** (split into multiple features):
- "Implement user authentication"
- "Build the frontend"

**Just Right** (single session):
- "User can log in with email/password and receive a JWT"
- "Display loading spinner while API requests are pending"

**Too Small** (combine with related):
- "Add a button"
- "Change color to blue"

### 6. Assign Priorities

| Priority | Meaning | Examples |
|----------|---------|----------|
| 1 | Critical - blocks everything | Core architecture, auth |
| 2 | High - needed for MVP | Primary user flows |
| 3 | Medium - enhances experience | Secondary features |
| 4 | Low - nice to have | Polish, optimization |
| 5 | Future - after MVP | Stretch goals |

### 7. Update Features File

Add new features to `features.json`:
- Maintain sorted order by priority, then ID
- Update metadata (totalFeatures count)
- Preserve all existing features unchanged

```json
{
  "metadata": {
    "lastUpdated": "<new timestamp>",
    "totalFeatures": <new count>,
    "passingFeatures": <unchanged>
  }
}
```

### 8. Document the Additions

Update `agent-progress.md` to note what features were added and why.

## Output Format

```markdown
## Features Added

**Date**: <timestamp>
**Requested By**: User
**Features Added**: <count>

### New Features

| ID | Priority | Category | Description |
|----|----------|----------|-------------|
| F0XX | 1 | core | <description> |
| F0XY | 2 | ui | <description> |

### Feature Details

#### F0XX: <title>
**Priority**: 1 (Critical)
**Category**: core
**Dependencies**: None
**Estimated Effort**: Medium

**Acceptance Criteria**:
1. <criterion 1>
2. <criterion 2>
3. <criterion 3>

#### F0XY: <title>
...

### Integration Notes

- <How these features relate to existing ones>
- <Suggested implementation order>
- <Any architectural considerations>

### Updated Statistics

- **Total Features**: X → Y
- **Passing**: Z (W%)
- **New Features by Category**: <breakdown>
```
