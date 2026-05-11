---
name: gitnexus-exploring
description: Use when the user asks how code works, wants to understand architecture, trace execution flows, or explore unfamiliar parts of the codebase. Examples: "How does X work?", "What calls this function?", "Show me the auth flow"
---

# Exploring Codebases with GitNexus

## When to Use
- "How does authentication work?"
- "What's the project structure?"
- "Show me the main components"
- "Where is the database logic?"
- Understanding code you haven't seen before

## Workflow
1. **gitnexus_list_repos()** → Discover indexed repos
2. **gitnexus_query({query: "<what you want to understand>"})** → Find related execution flows
3. **gitnexus_context({name: "<symbol>"})** → Deep dive on specific symbol
4. **gitnexus_query({query: "process <name>"})** → Trace execution flow

*Note: If the index is stale, run `npx gitnexus analyze` in the terminal.*

## Checklist
- [ ] gitnexus_list_repos to see available indexes
- [ ] gitnexus_query for the concept you want to understand
- [ ] Review returned processes (execution flows)
- [ ] gitnexus_context on key symbols for callers/callees
- [ ] Read source files for implementation details

## Tools
### gitnexus_query
Find execution flows related to a concept.
`gitnexus_query({query: "payment processing"})`

### gitnexus_context
360-degree view of a symbol.
`gitnexus_context({name: "validateUser"})`
