Thoroughly verify a feature works end-to-end before marking it complete

# Goal

Perform **rigorous end-to-end verification** of a feature before marking it as passing.

## Instructions

### 1. Load Feature Details

```bash
klondike feature show F00X
```

This displays:
- Feature ID and description
- Acceptance Criteria (ALL must pass)
- Current status and notes

### 2. Ensure Environment is Running

```bash
klondike validate
./init.sh  # or .\init.ps1
```

### 3. Design Verification Plan

For each acceptance criterion, define:
- **Test method**: How to verify (browser, API call, CLI command, etc.)
- **Expected result**: What success looks like
- **Evidence to capture**: What to save (screenshot path, log file, command output)

### 4. Execute Verification

Perform each test **as a real user would**:

**For Web Applications:**
- Navigate through the actual UI
- Click buttons, fill forms, submit data
- Check that results appear correctly
- Verify error states work

**For APIs:**
- Make actual HTTP requests
- Test happy path AND error cases
- Verify response format matches spec

**For CLI Tools:**
- Run actual commands
- Test with various arguments
- Verify output format

### 5. Document Results

For each acceptance criterion:

```markdown
#### Criterion: "<description>"
- **Method**: <how tested>
- **Result**: ✅ PASS / ❌ FAIL
- **Evidence**: <screenshot path, command output, etc.>
```

### 6. Update Feature Status

**Only if ALL criteria pass:**

```bash
klondike feature verify F00X \
  --evidence "test-results/F00X-criterion-1.png" \
  --notes "Tested on Chrome. Edge case: empty input handled."
```

**If ANY criterion fails:**

```bash
klondike feature block F00X --reason "Criterion 2 failed: API returns 500"
```

## Important Notes

- **Never skip verification** - code that "looks right" often has bugs
- **Test the actual running system** - not mocks or simulations
- **Document everything** - next agent needs to understand what was tested
- **Be honest about failures** - incomplete features should stay incomplete
