````prompt
---
name: continuous-implementation
description: "Continuously implement features in isolated worktrees until backlog is empty"
---

# Goal

**Autonomously implement all remaining features** by continuously spawning worktree sessions, one feature at a time, until the backlog is empty or a blocking issue is encountered.

## Use Case

This prompt is designed for **cheap, fast implementation models** that can iterate quickly through a feature backlog. It orchestrates the full cycle:

1. Pick next unverified feature
2. Spawn worktree session to implement it
3. Verify the implementation
4. Apply changes and cleanup
5. Repeat

## Prerequisites

- Project initialized with `klondike init`
- Features defined in `.klondike/features.json`
- Git repository in clean state (no uncommitted changes)

---

## Instructions

### 1. Initial Assessment

Run these commands to understand the current state:

```bash
# Get project status
klondike status

# List unverified features
klondike feature list --status not-started
klondike feature list --status in-progress
klondike feature list --status blocked
```

### 2. Implementation Loop

**Repeat the following steps until no features remain:**

#### Step 2.1: Select Next Feature

Pick the next feature to implement based on priority:

```bash
# Get next priority feature (not-started or in-progress, sorted by priority)
klondike status
```

**Selection criteria:**
1. First, complete any `in-progress` features
2. Then, pick highest priority `not-started` feature (priority 1 > 2 > 3)
3. Skip `blocked` features (document why they're blocked)

If no features remain to implement, **STOP** and generate a completion report.

#### Step 2.2: Spawn Worktree Session

Launch an isolated worktree session for the selected feature:

```bash
klondike copilot start -w --apply --feature F00X
```

**Flags explained:**
- `-w` / `--worktree`: Create isolated git worktree
- `--apply`: Auto-apply changes to main project when done
- `--feature F00X`: Focus on specific feature

The copilot session will:
- Create an isolated branch
- Implement the feature
- Commit changes
- Apply changes back to main project
- Cleanup worktree

#### Step 2.3: Verify Implementation

After the worktree session completes, verify the feature works:

```bash
# Check git status for applied changes
git status

# Run project tests
# Python: uv run pytest
# Node.js: CI=true npm test  # Prevents interactive prompts

# Run linting
# Python: uv run ruff check src tests
# Node.js: npm run lint
```

**If verification passes:**

```bash
# Commit the applied changes
git add -A
git commit -m "feat(F00X): <feature description>

Implemented via continuous-implementation workflow.
- <key change 1>
- <key change 2>"

# Mark feature as verified
klondike feature verify F00X --evidence "tests pass, manual verification"
```

**If verification fails:**

```bash
# Revert the applied changes
git checkout -- .

# Block the feature with reason
klondike feature block F00X --reason "Implementation failed: <specific error>"
```

#### Step 2.4: Cleanup and Continue

```bash
# Cleanup any stale worktrees
klondike copilot cleanup --force

# Check project status
klondike status

# Loop back to Step 2.1
```

---

## Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                    START LOOP                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ klondike feature list  │
              │ --status not-started   │
              └────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ Any features  │──── No ────▶ DONE! Generate Report
                   │  remaining?   │
                   └───────────────┘
                           │ Yes
                           ▼
              ┌────────────────────────┐
              │ klondike copilot start │
              │ -w --apply --feature   │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Run tests & linting   │
              └────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  Tests pass?  │
                   └───────────────┘
                     │           │
                    Yes          No
                     │           │
                     ▼           ▼
            ┌──────────────┐  ┌──────────────┐
            │ Commit &     │  │ Revert &     │
            │ Verify       │  │ Block        │
            └──────────────┘  └──────────────┘
                     │           │
                     └─────┬─────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ klondike copilot       │
              │ cleanup --force        │
              └────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ Loop back to  │
                   │ feature list  │
                   └───────────────┘
```

---

## Error Handling

### Worktree Creation Fails

```bash
# Check for stale worktrees
git worktree list

# Prune stale entries
git worktree prune

# Cleanup klondike worktrees
klondike copilot cleanup --force

# Retry
```

### Apply Fails (Merge Conflicts)

```bash
# Discard the failed worktree changes
klondike copilot cleanup --force

# Block the feature
klondike feature block F00X --reason "Merge conflicts with main branch"

# Continue to next feature
```

### Copilot Session Hangs or Errors

```bash
# If session doesn't complete after reasonable time, kill it
# Check for leftover worktrees
klondike copilot list

# Force cleanup
klondike copilot cleanup --force

# Block the feature and continue
klondike feature block F00X --reason "Copilot session failed: <error>"
```

### All Features Blocked

If all remaining features are blocked, **STOP** and generate a blocker report:

```markdown
## 🚫 All Remaining Features Blocked

| Feature | Blocker |
|---------|---------|
| F00X | <reason> |
| F00Y | <reason> |

**Recommended Actions:**
1. <manual intervention needed>
2. <dependency to resolve>
```

---

## Completion Report

When all features are implemented (or only blocked features remain):

```markdown
## 🎉 Continuous Implementation Complete

**Session Summary:**
- Total features: X
- Verified: Y
- Blocked: Z
- Progress: XX%

**Implemented This Run:**
| Feature | Description | Status |
|---------|-------------|--------|
| F001 | ... | ✅ Verified |
| F002 | ... | ✅ Verified |
| F003 | ... | 🚫 Blocked |

**Blocked Features (Require Manual Attention):**
| Feature | Blocker |
|---------|---------|
| F003 | <reason> |

**Final Verification:**
```bash
git log --oneline -10
klondike status
```

**Next Steps:**
1. Review blocked features
2. Run full test suite
3. Consider release
```

---

## Best Practices

### DO:
- ✅ Commit after EACH successful feature
- ✅ Run tests after EACH feature (catch regressions early)
- ✅ Block features immediately if they fail (don't retry endlessly)
- ✅ Keep the loop running until completion
- ✅ Generate completion report at the end

### DON'T:
- ❌ Try to implement multiple features in one worktree session
- ❌ Skip verification steps
- ❌ Leave worktrees dangling
- ❌ Retry failed features more than once
- ❌ Ignore test failures

---

## Quick Start

For fast iteration, run this one-liner pattern:

```bash
# Check what's next
klondike feature list --status not-started | head -5

# Implement next feature (replace F00X with actual ID)
klondike copilot start -w --apply --feature F001

# After it completes, verify and commit
git status && CI=true npm test && git add -A && git commit -m "feat(F001): implement feature"
klondike feature verify F001 --evidence "tests pass"

# Repeat for next feature
klondike copilot start -w --apply --feature F002
# ...
```

---

## Exit Conditions

Stop the loop when:

1. **No features remain** - All features are verified ✅
2. **All remaining features are blocked** - Manual intervention needed 🚫
3. **Critical error** - Project in broken state, needs recovery 💥
4. **User interrupt** - Manual stop requested ⏹️

Always ensure the repository is in a clean, committed state before stopping.

````
