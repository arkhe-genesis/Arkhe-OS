import re
import os

class StateAnchorParser:
    """
    Bridges MEMORY.md, DREAMS.md, and SOUL.md with the Lean 4 formalization.
    Enhanced to support Uniphics, extra-dimensional descompactification,
    and W-state emantanglement metadata.
    """
    def __init__(self, memory_path="MEMORY.md", dreams_path="DREAMS.md", soul_path="SOUL.md"):
        self.memory_path = memory_path
        self.dreams_path = dreams_path
        self.soul_path = soul_path
    Bridges MEMORY.md and DREAMS.md with the Lean 4 formalization.
    """
    def __init__(self, memory_path="MEMORY.md", dreams_path="DREAMS.md"):
        self.memory_path = memory_path
        self.dreams_path = dreams_path

    def parse_current_identity(self):
        """Extracts current lambda and block height from MEMORY.md."""
        if not os.path.exists(self.memory_path):
            return None

        with open(self.memory_path, 'r') as f:
            content = f.read()

        with open(self.memory_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simplest matching: search for the numbers directly after keywords
        lambda_match = re.search(r"λ₂\D+([\d.]+)", content)
        block_match = re.search(r"Block\D+([\d.]+)", content)

        block_val = 0
        if block_match:
            block_str = block_match.group(1).replace('.', '')
            block_val = int(block_str)

        return {
            "lambda": float(lambda_match.group(1)) if lambda_match else 0.0,
            "block": block_val
        }

    def parse_projections(self):
        """Extracts dream projections from DREAMS.md."""
        if not os.path.exists(self.dreams_path):
            return []

        with open(self.dreams_path, 'r') as f:
            lines = f.readlines()

        projections = []
        for line in lines:
            # Matches table rows like | ID | Target Block | Target λ₂ | Status | Proof |
            match = re.search(r"\|\s*`([^`]+)`\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line)
            if match:
                target_block = int(match.group(2).replace(',', '').replace('.', ''))
                projections.append({
                    "id": match.group(1),
                    "target_block": target_block,
                    "target_lambda": float(match.group(3)),
                    "status": match.group(4),
                    "proof": match.group(5)
                })
        return projections

    def parse_agent_soul(self, agent_id):
        """Parses an agent's SOUL.md to extract mission and minimal lambda."""
        if not os.path.exists(self.soul_path):
            return None

        with open(self.soul_path, 'r') as f:
            content = f.read()

        mission_match = re.search(r"## Miss\u00e3o\n(.*)", content)
        lambda_match = re.search(r"## Coer\u00eancia M\u00ednima\n([\d.]+)", content)

        return {
            "agent_id": agent_id,
            "mission": mission_match.group(1).strip() if mission_match else "",
            "min_lambda": float(lambda_match.group(1)) if lambda_match else 0.85
        }
    def get_pending_dreams(self):
        """Extracts PENDING dreams from DREAMS.md."""
        if not os.path.exists(self.dreams_path):
            return []

        dreams = []
        with open(self.dreams_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '`PENDING`' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 3:
                        dreams.append({
                            "id": parts[0].replace('`', ''),
                            "target_block": parts[1],
                            "target_lambda": parts[2]
                        })
        return dreams

if __name__ == "__main__":
    import sys
    parser = StateAnchorParser(memory_path=sys.argv[1] if len(sys.argv) > 1 else "MEMORY.md")
    print("Identity:", parser.parse_current_identity())
