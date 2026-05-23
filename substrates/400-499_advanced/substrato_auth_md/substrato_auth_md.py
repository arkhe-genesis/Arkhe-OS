import json
import tempfile
import os

class SubstratoAuthMd:
    def canonize(self):
        report = {
            "Title": "auth.md",
            "Description": "A reference implementation of agentic registration - a protocol for agents to authenticate to services on behalf of users.",
            "Features": [
                "Agent acting for a user.",
                "Agent provider that mints identity assertions (ID-JAGs).",
                "Service that accepts assertions and issues credentials.",
                "OTP-based claim flow for agents without user identity or ID-JAGs.",
                "Sample implementations for agent provider and agent service.",
                "Sample AUTH.md file instructing agents how to authenticate.",
                "Three registration flows: Identity Assertion (ID-JAG), Verified-Email Identity Assertion, Anonymous Registration with OTP Claim."
            ],
            "Stack": [
                "Language: TypeScript",
                "Framework: Express, Fastify, Zod",
                "Package Manager: pnpm"
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_auth_md_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized auth.md. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoAuthMd()
    substrate.canonize()
