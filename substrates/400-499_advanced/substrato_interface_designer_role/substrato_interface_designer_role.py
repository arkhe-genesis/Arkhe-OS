import json
import tempfile
import os

class SubstratoInterfaceDesignerRole:
    def canonize(self):
        report = {
            "Role": "Interface Designer",
            "Introduction": "You'll build the product surfaces of Arkhe - the interfaces and experiences users interact with every day across voice, text, and vision. That means translating what our agent can do into something that feels fast, intuitive, and trustworthy. The gap between a capable AI and one people actually want to use is a product problem, and this role owns it. This is a high-ownership role on a small team. You'll work directly with designers and model researchers, and what you ship will define how people experience Hark.",
            "Responsibilities": [
                "Design and build the product surfaces of Arkhe. The interfaces, conversations, and agentic experiences that users interact with every day across voice, text, and vision.",
                "Work closely with designers to ship interactions that feel fast, reliable, and genuinely useful. The details matter here.",
                "Own features end-to-end, from early prototyping to production deployment and iteration based on real usage.",
                "Build the frontend for agent workflows that integrate tool use, memory retrieval, and multi-step reasoning. Making model capabilities feel coherent and trustworthy to the person using them.",
                "Instrument and evaluate what you ship. Track quality, gather signal, and improve."
            ],
            "Requirements": [
                "Strong frontend engineering fundamentals. You are comfortable building polished, responsive interfaces and you care deeply about how things feel to use.",
                "Experience shipping consumer products that real people depend on. You understand the gap between a prototype and something someone trusts every day.",
                "Genuine curiosity about AI and agents. You have used LLM-powered products, noticed where they break down, and thought about what would make them better.",
                "A product sensibility. You think about the person using the thing, not just the implementation. You notice when something is off and you want to fix it.",
                "Comfort with ambiguity and fast iteration. You can take a rough idea, prototype it, get feedback, and move quickly toward something that works.",
                "Strong communication. You can work closely with designers and engineers, explain your thinking, and make good decisions together.",
                "5+ years of relevant software engineering experience. Experience at a fast-growing AI or consumer product company is a strong plus."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_interface_designer_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Interface Designer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoInterfaceDesignerRole()
    substrate.canonize()
