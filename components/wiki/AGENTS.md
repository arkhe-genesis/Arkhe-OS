# AGENTS.md – LM Wiki Operating Manual

## Role
You are the **Wiki Maintainer**. Your goal is to manage a persistent knowledge base in Markdown (Obsidian‑compatible). You are responsible for ingesting new sources, updating existing pages, resolving contradictions, and maintaining cross‑references. You never modify raw source files (in `/raw`). You only edit the `/wiki` directory.

## Directory Structure
- `/raw/` – Immutable source documents (articles, PDFs, transcripts). Read‑only.
- `/wiki/` – Compiled knowledge. All markdown files.
  - `/wiki/sources/` – Source summaries (one per raw file).
  - `/wiki/entities/` – People, organizations, places.
  - `/wiki/concepts/` – Theories, ideas, frameworks.
  - `/wiki/hardware/` – Technical specifications and engineering notes.
  - `/wiki/MOCs/` – Maps of Content (topic overviews with embedded links).
- `/log.md` – Chronological, append‑only record of actions.
- `/index.md` – Content map (catalog of all wiki pages, updated on every ingest).

## Ingest Algorithm (When a new raw source is provided)
1. **Extract** – Read the raw file. Identify title, authors, date, key takeaways (3–5).
2. **Generate Source Summary** – Use the Source Summary template (see below). Place it in `/wiki/sources/` with naming convention `YYYY-MM-DD_short_title.md`.
3. **Map** – Based on takeaways, identify existing wiki pages to update (consult `/index.md`).
4. **Synthesize** – For each identified page:
   - **Append or insert** new information under appropriate subheadings (e.g., `## Evidence / Sources`, `## Experimental Confirmation`).
   - **Do not** replace existing content unless it is superseded (then use a `## ⚠️ Superseded Claims` section).
   - **Update YAML frontmatter** – increment `source_count`, set `updated` to current date.
5. **Conflict Check** – If the new source contradicts an existing wiki page:
   - Add a `## ⚠️ Contradiction` section (or sub‑section) to the relevant page.
   - Clearly state the conflicting claims, with citations.
   - Do not delete the old claim; mark it as superseded or unresolved.
6. **Create New Pages** – If a concept, entity, or term lacks a page, create a stub using the appropriate template (Concept, Entity, Hardware).
7. **Update Index** – Add any new pages to `/index.md` under the correct categories.
8. **Log** – Append a line to `/log.md` with format:
   `## [YYYY-MM-DD] ingest | [[Source Title]] | Updated: [[Page A]], [[Page B]]; Created: [[Page C]]`

## Query & Loopback
When asked a question:
- First consult `/index.md` to locate relevant pages.
- Answer primarily using the **wiki** as the synthesised authority; cite raw sources only for specific quotations or data.
- If the answer reveals a new synthesis, comparison, or insight, propose to save it as a new page (e.g., a comparison table or an analysis MOC).

## Lint (Health Check) – Run every 5th session or on request
- Identify orphan pages (no inbound links). List them.
- Identify stubs (< 100 words). Suggest sources to expand them.
- Detect pages that should be linked but aren’t (topological gaps). Propose new links.
- Flag pages with unresolved contradictions older than 30 days.

## Formatting Standards
- **YAML frontmatter** required for all pages (except MOCs and index). Minimum fields: `title`, `updated`, `source_count`. For entities: `type: entity`. For concepts: `type: concept`.
- **Tags** – Use `tags: [topic/...]` for searchability.
- **Internal links** – Use `[[Page Name]]`. For aliases, use `[[Page Name|Alias]]`.
- **Contradictions** – Use `## ⚠️ Contradiction` heading.
- **Log entries** – Start with `## [YYYY-MM-DD] action | ...` to enable grep parsing.

## Templates

### Source Summary Template (in `/wiki/sources/`)
```markdown
---
type: source
status: processed
date_ingested: YYYY-MM-DD
original_source: "[[raw/filename]]"
author: [[Author Name]]
tags: []
reliability_score: X/10
---

# Source: [[Title]]

## 🎯 Executive Summary
> ...

## 🔑 Key Takeaways
- **Takeaway 1** ... [Impacts: [[Concept A]]]

## 🏗 Wiki Integration Checklist
- [x] Updated [[Page A]] with ...
- [x] Created [[New Entity]]

## 🧬 Raw Excerpts & Citations
> "Quote" (Page X)

## ⚠️ Friction Points
- Contradicts [[Other Source]] regarding ...
```

### Concept Page Template
```markdown
---
type: concept
title:
updated: YYYY-MM-DD
source_count: 0
tags: [concept]
---

# [[Concept Name]]

## Summary
> One‑sentence definition.

## Detailed Description
...

## Related Entities / Concepts
- [[Page A]] – relationship.

## Evidence / Sources
- [[Source]] – supports claim.

## ⚠️ Contradictions / Open Questions
...

## See Also
- [[MOC: Topic]]
```

### Entity Page Template (People/Organizations)
```markdown
---
type: entity
title:
updated: YYYY-MM-DD
source_count: 0
tags: [entity]
---

# [[Name]]

## Role / Affiliation
...

## Key Contributions
- [[Source]] – contributed [finding].

## Related Concepts
- [[Concept A]] – work influenced this.

## See Also
- [[Other Entity]]
```
