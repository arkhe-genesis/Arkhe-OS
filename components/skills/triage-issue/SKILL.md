---
name: triage-issue
description: Triage a bug or issue by exploring the codebase to find root cause, then create a GitHub issue with a TDD-based fix plan. Use when user reports a bug, wants to file an issue, mentions "triage", or wants to investigate and plan a fix for a problem.
---

# Triage Issue

Investigate a reported problem, find its root cause, and create a GitHub issue with a TDD fix plan. This is a mostly hands-off workflow - minimize questions to the user.

## Process

1. **Capture the problem**: Get a brief description of the issue from the user. Ask ONE question: "What's the problem you're seeing?"
2. **Explore and diagnose**: Deeply investigate the codebase to find where the bug manifests, trace the code path, and identify the root cause.
3. **Identify the fix approach**: Determine the minimal change needed, affected modules, and behaviors to verify.
4. **Design TDD fix plan**: Create an ordered list of RED-GREEN cycles (vertical slices).
5. **Create the GitHub issue**: Use `gh issue create` with the template below.

## Template

### Problem
A clear description of the bug or issue (actual vs expected behavior, reproduction steps).

### Root Cause Analysis
Describe the code path involved and why the current code fails. Describe behaviors and contracts, not just file paths.

### TDD Fix Plan
A numbered list of RED-GREEN cycles:
1. **RED**: Write a test that [describes expected behavior] **GREEN**: [Minimal change to make it pass]
...
**REFACTOR**: [Any cleanup needed]

### Acceptance Criteria
- [ ] All new tests pass
- [ ] Existing tests still pass
