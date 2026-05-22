import json
import tempfile
import os

class SubstratoIOSEngineerRole:
    def canonize(self):
        report = {
            "Title": "iOS Engineer Role at Arkhe",
            "Intro": "You will build the iOS experience for Arkhe: a native app that brings a real-time, multimodal AI agent into people's pockets. That means shipping an app that feels instant, handles streaming AI responses gracefully, and integrates voice, text, and vision into a single coherent experience. The bar is high: this is the primary way millions of people will interact with Arkhe. This is a high-ownership role on a small team. You will work directly with designers, platform engineers, and the people building the models. What you ship will define how Hark feels in someone's hand.",
            "Responsibilities": [
                "Build and own the Arkhe iOS app. Architecture, UI, performance, and the end-to-end experience.",
                "Ship features that integrate real-time AI capabilities: streaming responses, voice input, tool invocations, and multimodal interactions.",
                "Work closely with designers to craft interfaces that feel fast, polished, and trustworthy. Sweat the details.",
                "Optimize for performance at every layer: startup time, animation smoothness, memory efficiency, and network latency.",
                "Own components end-to-end, from design and implementation through testing, launch, and iteration.",
                "Collaborate with platform and backend engineers on APIs, data contracts, and integration with the agent runtime.",
                "Instrument what you ship. Track performance, catch regressions, and improve based on real-world usage."
            ],
            "Requirements": [
                "Strong expertise in Swift, with deep knowledge of UIKit and SwiftUI, and a solid understanding of iOS system design.",
                "Proven ability to build high-performance, responsive mobile applications, with experience optimizing for latency, memory, and real-time interactions.",
                "Experience designing and shipping intuitive, high-quality user experiences, with strong attention to detail and product craft.",
                "Familiarity with concurrency patterns (async/await, Combine) for building real-time, interactive applications.",
                "Experience integrating with backend systems and AI-powered services (REST, streaming APIs), ensuring smooth and reliable data flow.",
                "Demonstrated ability to own features end-to-end, from initial concept and architecture through implementation and deployment.",
                "5+ years of iOS engineering experience."
            ],
            "Bonus_Qualifications": [
                "Experience building or contributing to AI-powered or agent-driven applications, especially involving voice, multimodal input, or real-time interaction.",
                "Strong product intuition, with the ability to translate emerging AI capabilities into user-facing experiences that feel natural and useful.",
                "Experience working in early-stage or 0-to-1 environments, with a track record of shipping quickly and iterating based on user feedback.",
                "Familiarity with the Apple ecosystem, including frameworks such as AVFoundation, Core ML, or real-time media processing.",
                "Comfortable working across the stack or collaborating closely with backend and AI teams to deliver end-to-end features.",
                "High bar for engineering craft, with a track record of building polished, performant, and reliable mobile products."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_ios_engineer_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized iOS Engineer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoIOSEngineerRole()
    substrate.canonize()
