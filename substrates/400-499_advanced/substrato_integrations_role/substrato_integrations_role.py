import json
import tempfile
import os

class SubstratoIntegrationsRole:
    def canonize(self):
        report = {
            "Title": "Integrations Engineer Role",
            "Description": "You'll build and own the integrations layer that makes Arkhe's AI agent genuinely useful in the real world. That means connecting it to the tools, services, and data sources people actually use every day. That means designing and shipping the protocols, connectors, and execution primitives that let Arkhe take real actions: reading and writing email, managing calendars, interacting with third-party APIs, and coordinating across services on a user's behalf. The power of an agentic system is only as broad as what it can reach. This is a high-ownership role on a small team. You'll work directly with platform engineers and model researchers, and the integrations you build will define the boundaries of what Arkhe can do.",
            "Responsibilities": [
                "Design and build the integration layer that connects Arkhe's agent to third-party services, including email, calendar, productivity tools, communication platforms, developer tools, and more.",
                "Own the full lifecycle of integrations: authentication flows, API clients, schema normalization, action execution, and error handling. Build for reliability, not just the happy path.",
                "Define and implement the tool and action protocols that let the agent interact with external systems safely and consistently. Make it easy to add new integrations without rewriting the stack.",
                "Work closely with platform engineers to integrate connectors cleanly into the agent runtime. Tool execution needs to be fast, observable, and sandboxed appropriately.",
                "Collaborate with model researchers to define tool schemas and action semantics that models can reason about reliably. The quality of the interface shapes model behavior.",
                "Instrument integrations for reliability and correctness. Track failures, surface regressions, and close the loop with the team quickly.",
                "Identify the highest-leverage integrations to prioritize, and drive the roadmap that expands what Hark can do in the world."
            ],
            "Requirements": [
                "Strong backend engineering fundamentals. You are comfortable designing APIs, handling OAuth flows, working with webhooks and rate limits, and building systems that stay reliable across third-party dependencies.",
                "Experience building integrations at scale. You've shipped connectors to real external services, and you know what breaks in production: auth token expiry, API schema drift, inconsistent error codes, flaky uptime. You build defensively.",
                "Systems thinking. You can design an integrations framework that scales to dozens of services without becoming unmaintainable. You think in abstractions, not just one-off implementations.",
                "Genuine curiosity about AI and agents. You understand how tool use works in LLM systems, you've thought about how action schemas affect model behavior, and you have opinions about what makes integrations reliable for autonomous agents.",
                "Comfort with ambiguity and fast iteration. This space moves fast. You can ship something real quickly, learn from production, and improve without waiting for perfect specs.",
                "Strong communication. You can collaborate across platform, research, and product, represent integration constraints clearly, and make sure the right tradeoffs get made.",
                "5+ years of relevant software engineering experience. Experience building integrations or developer platforms is a strong plus."
            ],
            "Bonus_Qualifications": [
                "Experience building OAuth flows, webhook infrastructure, or API gateway layers.",
                "Familiarity with integration standards and protocols such as REST, GraphQL, gRPC, and MCP.",
                "Experience designing tool-use schemas or function-calling interfaces for LLMs.",
                "Prior work on developer platforms, integration marketplaces, or iPaaS systems.",
                "Experience with execution sandboxing or permission-scoped action frameworks.",
                "Background at a fast-moving AI company or a company where integrations were core to the product."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_integrations_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Integrations Engineer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoIntegrationsRole()
    substrate.canonize()
