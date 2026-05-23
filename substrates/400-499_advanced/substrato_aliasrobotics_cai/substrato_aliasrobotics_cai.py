import json
import tempfile
import os

class SubstratoCai:
    def canonize(self):
        report = {
            "Title": "Cybersecurity AI (CAI)",
            "Description": "CAI is a lightweight, open-source framework that empowers security professionals to build and deploy AI-powered offensive and defensive automation. It provides the building blocks to create specialized AI agents that can assist with mitigation, vulnerability discovery, exploitation, and security assessment.",
            "Features": [
                "300+ AI Models Support: Supports OpenAI, Anthropic, DeepSeek, Ollama, and more via LiteLLM.",
                "Built-in Security Tools: Ready-to-use tools for reconnaissance, exploitation, and privilege escalation.",
                "Battle-tested: Proven in HackTheBox CTFs, bug bounties, and real-world security case studies.",
                "Agent-based Architecture: Modular framework design to build specialized agents for different security tasks.",
                "Guardrails Protection: Built-in defenses against prompt injection and dangerous command execution.",
                "Research-oriented: Research foundation to democratize cybersecurity AI for the community."
            ],
            "Architecture": [
                "Agents: Intelligent systems that interact with environments based on ReACT model.",
                "Tools: Interfaces to execute system commands, run security scans, interact with APIs (LinuxCmd, WebSearch, Code, SSHTunnel).",
                "Handoffs: Allows an Agent to delegate tasks to another agent.",
                "Patterns: Structured design paradigm for agent operation (Swarm, Hierarchical, Chain-of-Thought, Auction-Based, Recursive).",
                "Turns and Interactions: Sequential exchanges between agents.",
                "Tracing: AI observability using Phoenix and OpenTelemetry.",
                "Guardrails: Input and output validation to prevent prompt injection and dangerous commands.",
                "Human-In-The-Loop (HITL): Allows human operator interaction and teleoperation via Ctrl+C."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_cai_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Cybersecurity AI (CAI). Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoCai()
    substrate.canonize()
