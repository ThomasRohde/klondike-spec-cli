Expand the feature registry with new well-structured features

# Goal

Add new features to the registry with proper structure, acceptance criteria, and implementation notes.

## Instructions

### 1. Review Current State

```bash
klondike status
klondike feature list
```

### 2. Plan New Features

For each feature you need to add, prepare:
- **Description**: Clear, concise feature name
- **Category**: Logical grouping (e.g., "auth", "ui", "api")
- **Priority**: 1 (critical) to 5 (nice-to-have)
- **Acceptance Criteria**: Specific, testable conditions
- **Notes**: Implementation hints, edge cases, dependencies

### 3. Add Features

```bash
klondike feature add "User can reset password via email" \
  --category auth \
  --priority 2 \
  --criteria "Reset link sent within 30s" \
  --criteria "Link expires after 24h" \
  --criteria "Password change logged" \
  --notes "Use SendGrid for emails. Consider rate limiting."
```

### 4. Feature Writing Guidelines

**Good Description:**
- Starts with user action: "User can...", "System shows...", "Admin manages..."
- Specific and bounded: "User can filter products by price range" NOT "Search functionality"

**Good Acceptance Criteria:**
- Testable: Can answer "did this pass?" with yes/no
- Specific: Include numbers, formats, edge cases
- Independent: Each criterion tests one thing

**Good Notes:**
- Implementation approach
- Known edge cases
- Dependencies on other features/systems
- Technical constraints

### 5. Verify Addition

```bash
klondike feature show F00X
```

## Example Output

```
klondike feature add "User can export data as CSV" \
  --category data \
  --priority 3 \
  --criteria "Export completes in <30s for 10k rows" \
  --criteria "CSV includes all visible columns" \
  --criteria "Download works in Chrome, Firefox, Safari" \
  --notes "Use streaming for large datasets. Consider chunking."

✅ Added F004: User can export data as CSV
```
