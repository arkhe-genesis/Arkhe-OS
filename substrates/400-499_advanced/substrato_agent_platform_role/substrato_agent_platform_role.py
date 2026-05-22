import json
import tempfile
import os

class SubstratoAgentPlatformRole:
    def canonize(self):
        report = {
            "Title": "Agent Platform Engineer",
            "Description": "You'll build the platform that powers Arkhe's AI agent - the runtime, the infrastructure, the primitives. Everything that makes the intelligence actually works in production. That means owning the hard systems problems, such as low-latency streaming, reliable tool execution, memory and context at scale, and orchestration logic that holds up under real usage. You will be building the foundation that everything else runs on. This is a high-ownership role on a small team. You'll work directly with the people building the models and the people shipping the product, and the systems you build will define what's possible for both.",
            "Responsibilities": [
                "Build the core runtime that powers Arkhe's agent platform. Orchestration, tool execution, memory retrieval, streaming, and the systems that make all of it work reliably together.",
                "Own features end-to-end, from early prototyping alongside model researchers to production deployment and iteration based on real usage.",
                "Architect the platform primitives that the rest of the product team builds on. Agent runtimes, execution sandboxes, memory APIs, streaming pipelines.",
                "Instrument and evaluate the product. Write evals, track quality regressions, and feed signals back into the model and product loop.",
                "Work across the stack when the problem requires it."
            ],
            "Requirements": [
                "Strong systems engineering fundamentals. You are comfortable designing APIs, building reliable infrastructure, and reasoning about performance, concurrency, and failure modes.",
                "Experience building production systems that real users depend on. You know the difference between something that works in a demo and something that works at scale.",
                "Genuine curiosity about AI and agents. You have built with LLMs, thought about how they fail, and have opinions about what makes agentic systems reliable.",
                "Comfort with ambiguity and fast iteration. You can start with a rough problem, build something real, learn from it, and improve quickly.",
                "Strong communication. You can explain tradeoffs clearly, collaborate across teams, and make good decisions with incomplete information.",
                "5+ years of relevant software engineering experience. Experience at a fast-growing AI or infrastructure-focused company is a strong plus.",
                "Bonus: hands-on experience with agent frameworks, streaming architectures, execution sandboxes, memory systems, or tool integration protocols."
            ],
            "Bonus_Qualifications": [
                "Experience at a fast-growing AI or infrastructure-focused company.",
                "Hands-on experience with agent frameworks.",
                "Experience with streaming architectures.",
                "Experience with execution sandboxes.",
                "Experience with memory systems or tool integration protocols."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_agent_platform_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Agent Platform Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoAgentPlatformRole()
    substrate.canonize()
