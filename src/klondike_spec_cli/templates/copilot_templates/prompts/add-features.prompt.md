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

### 6. Implementation Notes (STRONGLY RECOMMENDED)

> **Important**: Features are often created by a strong agent but implemented by a weaker agent.
> The `--notes` flag bridges this gap by providing implementation guidance that wouldn't fit in the description or criteria.

Use `--notes` to include:
- **Implementation hints**: Suggested approach, algorithms, or patterns
- **Edge cases**: Known corner cases the implementer should handle
- **Dependencies**: Other features or external systems this depends on
- **Context**: Why this feature exists, business reasoning
- **Gotchas**: Common pitfalls or non-obvious requirements

**Notes format template:**
```
Implementation: <suggested approach>
Edge cases: <cases to handle>
Dependencies: <F00X, external APIs, etc.>
Context: <why this matters>
Gotchas: <common pitfalls>
```

### 7. Add Features

```bash
klondike feature add --description "Feature description" \
  --category core \
  --priority 2 \
  --criteria "Criterion 1,Criterion 2,Criterion 3" \
  --notes "Implementation: Use existing AuthService. Edge cases: Handle expired tokens, invalid credentials. Dependencies: F001 (user model). Gotchas: Rate limiting applies after 5 failed attempts."
```

**Example with multi-line notes** (use quotes):
```bash
klondike feature add --description "User can reset password via email" \
  --category core \
  --priority 2 \
  --criteria "Reset link sent within 30s,Link expires after 1 hour,Password updated on valid token" \
  --notes "Implementation: Generate secure token with crypto.randomBytes(32). Store hashed token in DB with expiry. Edge cases: User requests multiple resets (invalidate old tokens). Dependencies: F003 (email service), F001 (user model). Context: Security requirement from compliance. Gotchas: Don't reveal whether email exists in system."
```

### 7. Verify

```bash
klondike status
klondike feature list
```
