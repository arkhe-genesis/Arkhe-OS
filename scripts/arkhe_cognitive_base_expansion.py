import urllib.request
import re
import json
import hashlib
import time
import os

def create_cognitive_expansion():
    url = "https://raw.githubusercontent.com/ashishps1/awesome-system-design-resources/main/README.md"
    try:
        response = urllib.request.urlopen(url)
        content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching the README: {e}")
        return

    # Parsing the markdown content
    nodes = []
    current_category = "General"

    # Regex to find markdown headers and links
    lines = content.split('\n')
    for line in lines:
        header_match = re.match(r'^## (.*)', line)
        if header_match:
            current_category = header_match.group(1).strip()
            # Clean up emojis from header
            current_category = re.sub(r'[^\w\s-]', '', current_category).strip()
            continue

        # Match links like: - [Text](URL)
        link_match = re.match(r'^\s*-\s*\[(.*?)\]\((.*?)\)', line)
        if link_match:
            title = link_match.group(1).strip()
            link_url = link_match.group(2).strip()

            node_id = hashlib.sha3_256(f"{title}-{link_url}".encode()).hexdigest()

            node = {
                "id": node_id,
                "label": title,
                "domain": "system_design",
                "category": current_category,
                "definitions": [f"Resource on {title}: {link_url}"],
                "sources": [{
                    "url": link_url,
                    "timestamp": time.time(),
                    "quality": 0.95
                }],
                "metadata": {
                    "source_repository": "ashishps1/awesome-system-design-resources"
                }
            }
            nodes.append(node)

    # Creating the cognitive base structure
    cognitive_base = {
        "metadata": {
            "version": "1.0",
            "domain": "system_design",
            "source": url,
            "timestamp": time.time(),
            "node_count": len(nodes)
        },
        "nodes": nodes
    }

    # Save to the data directory in the repository
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "system_design_cognitive_base.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cognitive_base, f, indent=4, ensure_ascii=False)

    print(f"✅ Cognitive base expanded successfully!")
    print(f"✅ Extracted {len(nodes)} cognitive nodes.")
    print(f"✅ Canonical JSON saved persistently to: {output_path}")

if __name__ == "__main__":
    create_cognitive_expansion()
