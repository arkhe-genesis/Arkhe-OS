import json
import tempfile
import os

class SubstratoOpenXiv:
    def canonize(self):
        report = {
            "Title": "OpenXiv",
            "Description": "A preprint server that lives in your social feed. Built on the AT Protocol. Preprints federate to Bluesky. OpenXiv is an AT Protocol App View for science. Papers, threads, endorsements, disclosures, and reviews are real app.openxiv.* records that live in each author's PDS (Bluesky's or their own) and federate to the wider AT Protocol network.",
            "Features": [
                "OpenXiv ids allocated per (subject, year).",
                "Profile pages /@handle with unified All / Papers / Posts tabs.",
                "Submit wizard, 6 idempotent stages, per-stage retry endpoint.",
                "Read flow at /abs/id with PDF, HTML, three explainer tiers, saga timeline.",
                "Trust Passport with lanes for transparency, identity, provenance, citations, math, integrity, social review, public disputes, external attestations.",
                "Provenance Timeline, eight publicly visible stages from upload to Bluesky bridge.",
                "Real OAuth: ORCID, Google, Bluesky (did:plc), Mastodon (cross-post link).",
                "OAI-PMH 2.0 endpoint at /oai-pmh with oai_dc metadata, transient deletes, ISO 8601 datestamps.",
                "Bluesky feed generator.",
                "Refusal packets at /refusals/id for AI-slop and policy violations.",
                "Browser extension that injects OpenXiv Trust Passport badges onto arxiv.org/abs/* pages.",
                "Multi-tier summaries (school, undergrad, expert) generated at submission, editable by author."
            ],
            "Stack": [
                "Language: TypeScript strict, Node 22.",
                "API: Fastify 5 with fastify-type-provider-zod.",
                "Database: PostgreSQL 16 + pgvector via Drizzle ORM.",
                "Queues: BullMQ on Redis 7.",
                "Storage: S3 compatible. MinIO locally, Hetzner Object Storage in production.",
                "LaTeX to PDF: tectonic running in a sandboxed Docker container.",
                "LaTeX to HTML: latexml.",
                "Metadata extraction: GROBID.",
                "LLM: DeepSeek V4 Flash for explainer tier generation; Gemini gemini-embedding-001 for semantic similarity.",
                "Undisclosed AI detector: ensemble (perplexity burst + Binoculars-style ratio + stylometric).",
                "Auth: OAuth via ORCID, Google, and Bluesky.",
                "Web: Astro 5 server-rendered with React 19 islands.",
                "Edge: Caddy 2."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_openxiv_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized OpenXiv. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoOpenXiv()
    substrate.canonize()
