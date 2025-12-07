---
description: "Testing practices for end-to-end feature verification"
applyTo: "**/*.test.*,**/*.spec.*,**/test/**,**/tests/**,**/__tests__/**"
---

# Testing for Long-Running Agents

This instruction file defines testing practices that prevent the "mark as done without proper testing" failure mode.

## Core Principle

**"If you haven't tested it as a user would, it's not verified."**

Unit tests are valuable but insufficient. Features must be verified end-to-end on the actual running system.

## Testing Pyramid for Agents

```
        /\
       /  \     E2E Tests (verify features.json)
      /----\
     /      \   Integration Tests
    /--------\
   /          \ Unit Tests
  /____________\
```

All layers matter, but **E2E tests are required for feature verification**.

## Before Marking a Feature Complete

### Required Steps

1. **Start the actual application**
   ```bash
   ./init.sh  # or platform-specific init
   ```

2. **Test each acceptance criterion**
   - Navigate/interact as a real user would
   - Use actual UI, CLI, or API endpoints
   - Not mocks, not simulations

3. **Document the test**
   - What you tested
   - How you tested it
   - What you observed
   - Any edge cases checked

4. **Only then update features.json**

### Example Verification Session

```markdown
## Verifying F005: Add new todo via input field

### Acceptance Criteria
1. Input field is visible on main page
2. User can type todo text
3. Pressing Enter adds the todo
4. New todo appears in list
5. Input clears after adding

### Verification

**Started server**: ./init.sh ✅

**Criterion 1**: Navigated to http://localhost:3000
- Input field visible at top of page ✅

**Criterion 2**: Typed "Buy groceries"
- Text appeared in input ✅

**Criterion 3**: Pressed Enter
- No page reload, todo added ✅

**Criterion 4**: Checked list
- "Buy groceries" appears as first item ✅

**Criterion 5**: Checked input
- Input is now empty ✅

**Edge Cases Tested**:
- Empty input: Shows validation message ✅
- Very long text: Accepted, wraps properly ✅
- Special characters: Works correctly ✅

**VERDICT**: All criteria pass, marking feature complete.
```

## Testing Web Applications

### Manual Testing

```bash
# Start the dev server
npm run dev

# Open browser and test:
# - Navigate between pages
# - Fill and submit forms
# - Click buttons, check results
# - Verify error states
# - Test on different viewports
```

### Automated E2E (Preferred)

```javascript
// Using Playwright or similar
test('user can add a todo', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="todo-input"]', 'Buy groceries');
  await page.press('[data-testid="todo-input"]', 'Enter');
  await expect(page.locator('.todo-item')).toContainText('Buy groceries');
});
```

## Testing APIs

```bash
# Health check
curl http://localhost:3000/health

# Test CRUD operations
curl -X POST -H "Content-Type: application/json" \
  -d '{"title": "Test todo"}' \
  http://localhost:3000/api/todos

curl http://localhost:3000/api/todos

curl -X DELETE http://localhost:3000/api/todos/1

# Test error handling
curl http://localhost:3000/api/todos/nonexistent
# Should return 404, not 500
```

## Testing CLI Tools

```bash
# Help and version
./tool --help
./tool --version

# Normal operations
./tool create "Test item"
./tool list
./tool update 1 "Updated item"
./tool delete 1

# Error cases
./tool delete nonexistent  # Should show helpful error
./tool create ""           # Should validate input
```

## Red Flags (Don't Mark as Complete)

- ❌ Only ran unit tests
- ❌ Checked code looks correct
- ❌ Tested in isolation, not integrated
- ❌ Skipped testing because "it's a small change"
- ❌ Tested happy path only
- ❌ Server wasn't actually running

## Test Infrastructure

Every project should have:

1. **Quick smoke test** in init script
2. **Unit test suite** for logic
3. **Integration tests** for API/database
4. **E2E tests** for user flows (linked to features.json)

## Continuous Testing During Development

Don't batch testing to the end:

```
❌ Code, code, code, code → test everything at end

✅ Code → test → commit → code → test → commit
```

Test each change before moving on. This catches issues early when they're easy to fix.
