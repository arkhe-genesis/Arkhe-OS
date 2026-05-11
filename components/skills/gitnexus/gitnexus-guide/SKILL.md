---
name: gitnexus-guide
description: Use when the user asks about GitNexus itself — available tools, how to query the knowledge graph, MCP resources, graph schema, or workflow reference. Examples: "What GitNexus tools are available?", "How do I use GitNexus?"
---

# GitNexus Guide

Quick reference for all GitNexus MCP tools, resources, and the knowledge graph schema.

## Always Start Here

For any task involving code understanding, debugging, impact analysis, or refactoring:
1. READ `gitnexus://repo/{name}/context` — codebase overview + check index freshness
2. Match your task to a skill below and read that skill file
3. Follow the skill's workflow and checklist

*Note: If step 1 warns the index is stale, run `npx gitnexus analyze` in the terminal first.*

## Skills
| Task | Skill to read |
|------|---------------|
| Understand architecture / "How does X work?" | `gitnexus-exploring` |
| Blast radius / "What breaks if I change X?" | `gitnexus-impact-analysis` |
| Trace bugs / "Why is X failing?" | `gitnexus-debugging` |
| Rename / extract / split / refactor | `gitnexus-refactoring` |
| Tools, resources, schema reference | `gitnexus-guide` (this file) |

## Tools Reference
| Tool | What it gives you |
|------|-------------------|
| `gitnexus_query` | Process-grouped code intelligence — execution flows related to a concept |
| `gitnexus_context` | 360-degree symbol view — categorized refs, processes it participates in |
| `gitnexus_impact` | Symbol blast radius — what breaks at depth 1/2/3 with confidence |
| `gitnexus_detect_changes` | Git-diff impact — what do your current changes affect |
| `gitnexus_rename` | Multi-file coordinated rename with confidence-tagged edits |
| `gitnexus_cypher` | Raw graph queries |
| `gitnexus_list_repos` | Discover indexed repos |

## Graph Schema
- **Nodes**: `File`, `Function`, `Class`, `Interface`, `Method`, `Community`, `Process`
- **Edges** (via `CodeRelation.type`): `CALLS`, `IMPORTS`, `EXTENDS`, `IMPLEMENTS`, `DEFINES`, `MEMBER_OF`, `STEP_IN_PROCESS`

Example:
`MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "myFunc"}) RETURN caller.name, caller.filePath`
