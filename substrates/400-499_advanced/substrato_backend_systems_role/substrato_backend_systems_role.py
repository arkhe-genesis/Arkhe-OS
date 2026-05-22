import json
import tempfile
import os

class SubstratoBackendSystemsRole:
    def canonize(self):
        report = {
            "Title": "Backend Systems Engineer",
            "Context": "You will build the backend systems that make Arkhe AI agent actually work reliable, fast, and production-grade. That means the hard infrastructure problems: high-concurrency services, low-latency streaming, state management for long-running agent workflows, and the execution layer that connects model outputs to real-world actions. You are building the nervous system of an agentic product. This is a high-ownership role on a small team. You will work directly with model researchers and platform engineers, and the systems you build will determine whether Arkhe feels like a slow chatbot or something genuinely new.",
            "Responsibilities": [
                "Core Runtime Architecture: Design and build the high-concurrency backend services responsible for agent orchestration, tool execution, and real-time streaming.",
                "Systems Reliability: Develop robust failure-handling, retry logic, and state management for long-running agentic workflows.",
                "Platform Primitives: Architect the foundational APIs and services including memory retrieval systems and sandboxed execution environments that power the entire Hark ecosystem.",
                "Performance Engineering: Optimize the stack for low-latency streaming and high-throughput data processing to ensure seamless agent-user interactions.",
                "Full-Cycle Ownership: Lead features from low-level design and prototyping to production deployment, monitoring, and performance tuning.",
                "System Observability: Implement deep instrumentation and automated evaluation frameworks to track system health and model quality regressions."
            ],
            "Requirements": [
                "Backend & Systems Mastery: 5+ years of experience building mission-critical backend systems. You are an expert in concurrency, networking protocols, and distributed systems.",
                "Production at Scale: Proven track record of shipping APIs and infrastructure that handle real-world traffic, with a deep understanding of horizontal scaling and day 2 operations.",
                "AI System Intuition: Experience integrating LLMs into backend pipelines. You understand the unique failure modes of non-deterministic systems and how to wrap them in deterministic, reliable code.",
                "Language Proficiency: Strong experience in at least one systems-level language (e.g., Go, Rust, C++, or Java).",
                "Infrastructure Mindset: Comfort with cloud-native architectures (AWS/GCP), container orchestration, and building secure, isolated execution sandboxes.",
                "Technical Communication: Ability to articulate complex architectural tradeoffs and collaborate with model researchers to bridge the gap between AI and production-grade software."
            ],
            "Bonus_Qualifications": [
                "Hands-on experience with gRPC, WebSockets for high-performance streaming.",
                "Prior work with vector databases, distributed caching, or custom memory management systems.",
                "Deep knowledge of Kubernetes, microservices security, or serverless execution patterns.",
                "Experience building developer-facing APIs or SDKs."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_backend_systems_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Backend Systems Engineer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoBackendSystemsRole()
    substrate.canonize()
