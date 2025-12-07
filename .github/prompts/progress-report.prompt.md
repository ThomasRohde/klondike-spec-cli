---
name: progress-report
description: "Generate a comprehensive progress report on project status"
---

# Goal

Generate a **comprehensive progress report** showing project status, completed work, and remaining effort.

## Context

This prompt helps stakeholders understand project status and helps agents make informed decisions about what to work on next.

## Instructions

### 1. Gather Data

Read and analyze:

**From `features.json`:**
- Total features by category
- Features by status (`not-started`, `in-progress`, `blocked`, `verified`)
- Priority distribution
- Recently verified features (check `verifiedAt`)
- **Stale in-progress features** (check `lastWorkedOn` > 7 days ago)
- **Blocked features** (check `blockedBy` field)
- **Regressions** (features where `passes` flipped from `true` to `false`)

**From `agent-progress.md`:**
- Number of sessions completed
- Pattern of work (what's getting done)
- Recurring blockers
- Velocity trends

**From Git:**
```bash
git log --oneline --since="1 week ago" | wc -l  # commits this week
git log --oneline --since="1 month ago" | wc -l  # commits this month
git shortlog -sn --since="1 month ago"  # contributors
```

**From Codebase:**
- Lines of code (approximate)
- Test coverage (if available)
- Dependency count

### 2. Calculate Metrics

**Completion Metrics:**
- Overall completion: verified / total features
- Completion by category
- Completion by priority level

**Status Metrics:**
- Not started count
- In-progress count (flag if > 3 concurrent)
- Blocked count (flag if > 0)
- Verified count

**Health Metrics:**
- Stale in-progress: features with `lastWorkedOn` > 7 days ago
- Regressions: features that were passing but now fail
- Unblocked recently: features where `blockedBy` was cleared

**Velocity Metrics:**
- Features verified per session (average)
- Sessions per week (if timestamps available)
- Estimated sessions to completion

**Quality Metrics:**
- Features with evidence links vs without
- Features that passed on first verification
- Features that required rework

### 3. Identify Patterns

**What's Going Well:**
- Categories with high completion rate
- Consistently productive areas

**What Needs Attention:**
- Categories with low completion
- Long-standing incomplete features
- Recurring blockers

**Risks:**
- Dependencies blocking progress
- Technical debt accumulating
- Scope creep indicators

### 4. Generate Report

## Output Format

```markdown
# Project Progress Report

**Generated**: <timestamp>
**Project**: <name>
**Reporting Period**: <start> to <end>

---

## Executive Summary

<2-3 sentence overview of project status>

**Overall Progress**: ██████████░░░░░░ XX%

---

## Feature Completion

### By Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Verified | X | XX% |
| 🔄 In-Progress | Y | YY% |
| 🚫 Blocked | B | BB% |
| ⏳ Not Started | Z | ZZ% |
| **Total** | **N** | **100%** |

### By Priority

| Priority | Total | Complete | Remaining |
|----------|-------|----------|-----------|
| 🔴 P1 (Critical) | X | Y | Z |
| 🟠 P2 (High) | X | Y | Z |
| 🟡 P3 (Medium) | X | Y | Z |
| 🟢 P4 (Low) | X | Y | Z |
| ⚪ P5 (Future) | X | Y | Z |

### By Category

| Category | Progress | Status |
|----------|----------|--------|
| Core | ████████░░ 80% | 🟢 On Track |
| UI | ██████░░░░ 60% | 🟡 Attention |
| API | ████░░░░░░ 40% | 🔴 Behind |
| Tests | ██░░░░░░░░ 20% | 🔴 Behind |

---

## Recent Activity

### Last 5 Sessions

| Date | Focus | Features Completed | Key Accomplishments |
|------|-------|-------------------|---------------------|
| <date> | F0XX | 2 | <summary> |
| <date> | F0XY | 1 | <summary> |

### Git Activity

- **Commits (Last Week)**: X
- **Commits (Last Month)**: Y
- **Active Contributors**: Z

---

## ⚠️ Attention Required

### Stale In-Progress Features

| ID | Description | Last Worked | Days Stale |
|----|-------------|-------------|------------|
| F0XX | <description> | <date> | <N> days |

### Blocked Features

| ID | Description | Blocked By | Suggested Action |
|----|-------------|------------|------------------|
| F0XX | <description> | <reason/IDs> | <action> |

### Regressions (Features That Flipped to Failing)

| ID | Description | Was Verified | Now Status | Notes |
|----|-------------|--------------|------------|-------|
| F0XX | <description> | <date> | failing | <what broke> |

---

## Current Blockers

| ID | Blocker | Impact | Suggested Resolution |
|----|---------|--------|---------------------|
| B1 | <description> | Blocks F0XX, F0XY | <suggestion> |
| B2 | <description> | Blocks F0ZZ | <suggestion> |

---

## Recommendations

### Immediate Priorities

1. **<Action 1>** - <rationale>
2. **<Action 2>** - <rationale>
3. **<Action 3>** - <rationale>

### Technical Debt to Address

- <Item 1>
- <Item 2>

### Process Improvements

- <Suggestion 1>
- <Suggestion 2>

---

## Projections

**Estimated Sessions to MVP**: X-Y sessions
**Estimated Completion**: <date range>
**Confidence Level**: High/Medium/Low

**Assumptions**:
- <assumption 1>
- <assumption 2>

---

## Appendix: Feature List

<Full feature list with current status>
```
