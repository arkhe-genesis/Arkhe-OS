import json
import os
import tempfile

def canonize_firmware_role():
    role_description = {
        "title": "Firmware Engineer Role",
        "description": "You'll be building the core application that runs on our hardware device -- the software layer that bridges user-facing experiences with the underlying firmware and embedded systems. Think of it as the single app that makes the robot do what it needs to do. You've shipped a product before. You know what it takes to go from prototype to production, and you thrive in that process.",
        "responsibilities": [
            "Own the development of the primary application running on Arkhe's hardware device, from architecture through production deployment",
            "Build and optimize Android-based software that interfaces directly with embedded systems, sensors, and firmware layers",
            "Work at the crossover between application-level code and firmware -- writing software that runs on the device, not in the cloud",
            "Collaborate closely with hardware, embedded software, and AI teams to deliver a tightly integrated product experience",
            "Manage the full lifecycle of getting software onto a physical device: flashing, OTA updates, boot sequences, and device provisioning",
            "Debug across the full android stack -- from Android framework issues down to hardware-level communication protocols",
            "Drive the product from development through manufacturing and into the hands of users"
        ],
        "requirements": [
            "Strong communication skills to translate the requirements from XFN teams into designs.",
            "5+ years of experience in Android development, with deep experience beyond standard mobile apps -- ideally on embedded or custom hardware devices",
            "Strong understanding of the Android platform at the system level: AOSP, system services, HAL, native libraries, and device drivers",
            "Hands-on experience with embedded systems, firmware integration, or low-level hardware/software interfaces",
            "You have shipped a physical product. You know what it takes to get software running reliably on hardware in production -- not just in a lab",
            "Experience with communication protocols common in embedded devices (UART, SPI, I2C, BLE, USB)",
            "Proficiency in Java/Kotlin for application development and C/C++ for lower-level systems work",
            "Comfort working in a fast-moving, cross-functional team where you'll touch hardware, firmware, and product decisions daily"
        ],
        "bonus_qualifications": [
            "Experience with Android Things, AOSP board bring-up, or custom Android device builds",
            "Background in robotics, consumer electronics, or IoT hardware",
            "Experience with real-time operating systems (RTOS) or hybrid RTOS/Linux environments",
            "Familiarity with AI/ML model deployment on edge devices",
            "Hands-on experience analyzing and deconstructing Android device systems at the platform level"
        ]
    }

    fd, path = tempfile.mkstemp(suffix=".json", prefix="canon_firmware_role_")
    with os.fdopen(fd, 'w') as f:
        json.dump(role_description, f, indent=4)

    print("Canonical Firmware Engineer Role output securely to: " + path)
    return path

if __name__ == '__main__':
    canonize_firmware_role()
