Initialize project infrastructure AND start implementing features in one session

# Goal

Set up the **Klondike Spec agent infrastructure** for a new project, then immediately begin implementing features. This is a convenience command that combines `/init-project` + `/session-start` for smaller projects or when you want continuous progress.

## Context

Based on [Anthropic's research on long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), projects benefit from structured artifacts. This command creates them AND starts building.

**Use this when:**
- Building a small-to-medium project in extended sessions
- You want continuous progress without manual handoffs
- The project scope is well-defined upfront

**Use `/init-project` instead when:**
- Setting up infrastructure for a large project
- You want explicit control over session boundaries
- Multiple people/agents will work on the project

## Instructions

### Phase 1: Scaffolding (same as /init-project)

#### 1.1 Gather Project Information

- Confirm project type and name from user input
- Ask clarifying questions about:
  - Primary language/framework
  - Key features to implement (at least 5-10)
  - Testing approach (unit, integration, e2e)
  - Deployment target (if known)

#### 1.2 Create Feature Registry

Use the klondike CLI:

```bash
klondike init <project-name>
```

Then add features:

```bash
klondike feature add "Short description" \
  --category core \
  --priority 1 \
  --criteria "Criterion 1,Criterion 2,Criterion 3" \
  --notes "Implementation guidance for the implementing agent"
```

Generate **at least 20 features** covering:
- Core functionality
- Error handling
- User experience
- Testing infrastructure
- Documentation
- Deployment readiness

#### 1.3 Create Init Scripts

Create `init.sh` and `init.ps1` for reproducible environment startup. **Ensure the dev server starts in the background** so the script doesn't block the agent.

#### 1.4 Initialize Git & Commit

```bash
git init
git add .
git commit -m "feat: initialize project with agent harness infrastructure"
```

---

### Phase 2: Implementation (continues in same session)

After scaffolding is complete, **immediately transition to coding mode**:

#### 2.1 Start Development Environment

Run the init script to start the dev server.

#### 2.2 Implement Features Incrementally

Follow these rules:

1. **Work on ONE feature at a time** (by priority order)
2. **Commit after each feature** with descriptive messages
3. **Test incrementally** - verify each feature works before moving on
4. **Update feature status** - mark `passes: true` only after verification:
   ```bash
   klondike feature verify F00X --evidence "tests pass, manual verification"
   ```
5. **Log progress** periodically:
   ```bash
   klondike session note "Completed F001-F003, starting F004"
   ```

#### 2.3 Continue Until Natural Stopping Point

Keep implementing features until:
- User indicates they want to stop
- A blocker is encountered
- Significant milestone reached (e.g., MVP complete)
- Context is getting long (proactively offer to summarize and continue)

### Phase 3: Session End

When stopping (user request or natural break):

1. Ensure all code compiles and tests pass
2. Commit any uncommitted changes
3. End the session properly:
   ```bash
   klondike session end --summary "Completed X features, next is F00Y"
   ```
4. Provide handoff summary for next session

## Behavioral Guidelines

### DO:
- Create comprehensive feature list upfront
- Implement features in priority order
- Commit frequently with good messages
- Test features as you build them
- Mark features passing only after verification
- Offer progress updates periodically

### DON'T:
- Try to implement all features at once (one-shotting)
- Skip testing to move faster
- Mark features passing without verification
- Leave code in broken state
- Forget to update progress artifacts

## Output Format

### After Phase 1 (Scaffolding):

```
## Project Scaffolded

**Files Created:**
- .klondike/features.json (X features)
- .klondike/agent-progress.json
- init.sh / init.ps1
- [other project files]

**Feature Breakdown:**
- Core: X features
- UI: X features
- Infrastructure: X features
- Testing: X features

Transitioning to implementation...
```

### During Phase 2 (Building):

After each feature:
```
## F001: [Feature Name]

**Implemented:**
- [what was built]

**Verified:**
- [how it was tested]

**Next:** F002 - [description]
```

### At Session End:

```
## Session Summary

**Progress:** X/Y features complete (Z%)

**Completed This Session:**
- F001: [description]
- F002: [description]

**Next Session Should:**
1. Continue with F003: [description]
2. [any follow-up tasks]

**Handoff Notes:**
[Any important context for next session]
```
