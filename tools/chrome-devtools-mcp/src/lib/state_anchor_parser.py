import re
import os

class StateAnchorParser:
    """
    Bridges MEMORY.md and DREAMS.md with the Lean 4 formalization.
    """
    def __init__(self, memory_path="MEMORY.md", dreams_path="DREAMS.md"):
        self.memory_path = memory_path
        self.dreams_path = dreams_path

    def parse_current_identity(self):
        """Extracts current lambda and block height from MEMORY.md."""
        if not os.path.exists(self.memory_path):
            return None

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
