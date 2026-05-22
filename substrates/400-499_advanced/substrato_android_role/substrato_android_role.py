import json
import tempfile
import os

class SubstratoAndroidRole:
    def canonize(self):
        report = {
            "Title": "Android Experience for Arkhe",
            "Intro": "You'll build the Android experience for Arkhe: a native app that brings a real-time, multimodal AI agent into people's pockets. That means shipping an app that feels instant, handles streaming AI responses gracefully, and integrates voice, text, and vision into a single coherent experience. The bar is high: this is the primary way millions of people will interact with Hark. This is a high-ownership role on a small team. You'll work directly with designers, platform engineers, and the people building the models. What you ship will define how Arkhe feels in someone's hand.",
            "Responsibilities": [
                "Architect and develop a high-performance native Android application using Kotlin and Jetpack Compose.",
                "Implement real-time speech, audio, and video streaming capabilities for multimodal AI interactions.",
                "Build efficient interfaces to backend AI services, optimizing for latency and responsiveness.",
                "Own the full mobile lifecycle from development through deployment, monitoring, and iteration.",
                "Collaborate with design to create intuitive UI that showcases advanced AI capabilities.",
                "Champion Android development best practices including testing, code quality, and accessibility.",
                "Optimize performance at every level of the stack - UI rendering, network calls, background processing, and power consumption."
            ],
            "Requirements": [
                "5+ years of professional Android development experience.",
                "Expert-level proficiency in Kotlin, Jetpack Compose, and the Android SDK.",
                "Strong understanding of Android architecture patterns (MVVM, Clean Architecture) and dependency injection.",
                "Experience building apps with real-time features - streaming, WebSockets, or live audio/video.",
                "Track record of shipping polished, high-quality applications to the Play Store.",
                "Deep understanding of Android performance optimization, memory management, and battery efficiency.",
                "Comfortable working across the stack when needed, including interfacing with backend services.",
                "Strong communication skills and ability to work effectively in a fast-paced, collaborative environment."
            ],
            "Bonus_Qualifications": [
                "Experience integrating ML/AI features into mobile applications.",
                "Background in audio/video processing, real-time communication, or 3D graphics on mobile.",
                "Contributions to open-source Android projects or published technical writing.",
                "Experience building 0-to-1 products at early-stage companies.",
                "Passion for exploring new interaction paradigms between humans and AI systems."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_android_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Android Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoAndroidRole()
    substrate.canonize()
