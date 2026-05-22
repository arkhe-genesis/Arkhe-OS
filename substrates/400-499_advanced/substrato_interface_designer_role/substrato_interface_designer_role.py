import json
import tempfile
import os

class SubstratoInterfaceDesignerRole:
    def canonize(self):
        report = {
            "Role": "Interface Designer",
            "Description": "You are an extraordinarily talented Interface Designer to help shape the software experiences at Arkhen. Working within our multi-disciplinary design team, you will help craft the interfaces people use every day to interact with our intelligence. Across a variety of platforms, and form factors. You care deeply about the details of interaction: how something feels to use, as much as how it works. You're as comfortable defining interaction patterns as you are pushing visual quality. You will help define what it means to interact with personal AI, bringing clarity, craft and intention to every screen, state and moment in the product.",
            "Responsibilities": [
                "Designing interfaces across Hark's software platforms, from early concept through to shipped product",
                "Collaborating closely with product, engineering and brand to ensure a cohesive, high-quality experience",
                "Building and maintaining design systems that scale across surfaces",
                "Exploring new interaction paradigms suited to agentic, voice-first and multimodal AI",
                "Contributing to the overall design culture and raising the bar for craft across the team"
            ],
            "Requirements": [
                "5+ years of experience designing interfaces for software products",
                "A portfolio demonstrating exceptional craft across visual design, interaction design and systems thinking",
                "Deep proficiency of design systems",
                "Experience shipping products across web and mobile platforms",
                "Ability to communicate design decisions clearly to cross-functional partners",
                "Comfortable working in ambiguity and moving quickly without sacrificing quality",
                "A genuine curiosity about AI and the future of human-computer interaction"
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
