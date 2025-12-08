---
name: add-features
description: "Expand the feature registry with new well-structured features"
---

# Goal

Expand the feature registry with new, well-structured feature definitions that follow the project's standards.

## Instructions

### 1. Review Existing Features

```bash
klondike feature list
klondike status
```

### 2. Structure New Features

Each feature must have:
- **Clear description**: What the feature does
- **Category**: core, ui, api, testing, infrastructure, docs, security, performance
- **Priority**: 1 (critical) to 5 (future)
- **Acceptance criteria**: Specific, testable conditions

### 3. Acceptance Criteria Guidelines

Good criteria are:
- ✅ **Specific**: "User can click 'Save' and see a success toast"
- ✅ **Testable**: "API returns 200 with JSON body containing 'id' field"
- ✅ **Observable**: "Log file contains entry with timestamp"

Bad criteria are:
- ❌ **Vague**: "Works correctly"
- ❌ **Unmeasurable**: "Fast enough"
- ❌ **Subjective**: "Looks good"

### 4. Granularity Guidelines

**Too Big** (split into multiple features):
- "Implement user authentication"
- "Build the frontend"

**Just Right** (single session):
- "User can log in with email/password and receive a JWT"
- "Display loading spinner while API requests are pending"

**Too Small** (combine with related):
- "Add a button"
- "Change color to blue"

### 5. Priority Levels

| Priority | Meaning | Examples |
|----------|---------|----------|
| 1 | Critical - blocks everything | Core architecture, auth |
| 2 | High - needed for MVP | Primary user flows |
| 3 | Medium - enhances experience | Secondary features |
| 4 | Low - nice to have | Polish, optimization |
| 5 | Future - after MVP | Stretch goals |

### 6. Add Features

```bash
klondike feature add --description "Feature description" \
  --category core \
  --priority 2 \
  --criteria "Criterion 1,Criterion 2,Criterion 3"
```

### 7. Verify

```bash
klondike status
klondike feature list
```
