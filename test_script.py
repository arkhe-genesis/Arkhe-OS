import sys

adapters = [
    ("MistralAdapter", 0.89, 2),
    ("CohereAdapter", 0.87, 2),
    ("StabilityAdapter", 0.85, 2),
    ("EleutherAIAdapter", 0.88, 2),
    ("AI2Adapter", 0.90, 1),
    ("CerebrasAdapter", 0.91, 1),
    ("MITIBMWatsonAdapter", 0.90, 1),
    ("KimiAdapter", 0.93, 1),
    ("AnthropicAdapter", 0.92, 1),
    ("NvidiaAdapter", 0.92, 1),
    ("OpenAIAdapter", 0.91, 1),
    ("GoogleAdapter", 0.91, 1),
    ("SpaceXAdapter", 0.90, 2),
    ("DeepSeekAdapter", 0.88, 2),
    ("MicrosoftAdapter", 0.89, 2),
    ("AppleAdapter", 0.88, 2),
    ("HuaweiAdapter", 0.87, 2),
    ("XAIAdapter", 0.87, 2),
    ("SamsungAdapter", 0.86, 2),
    ("PalantirAdapter", 0.86, 2),
    ("AndurilAdapter", 0.85, 2),
    ("MetaAdapter", 0.85, 2),
    ("ZAIAdapter", 0.85, 2),
    ("AlibabaAdapter", 0.84, 3),
    ("IBMAdapter", 0.84, 3),
    ("XiaomiAdapter", 0.83, 3),
]

for name, phi, tier in adapters:
    if tier == 1 and not (phi >= 0.90): print(f"{name} Tier 1 failed: {phi}")
    if tier == 2 and not (phi >= 0.85 and phi < 0.90): print(f"{name} Tier 2 failed: {phi}")
    if tier == 3 and not (phi < 0.85): print(f"{name} Tier 3 failed: {phi}")

