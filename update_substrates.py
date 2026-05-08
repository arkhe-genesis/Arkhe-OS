import json

with open('.claude/SUBSTRATES.json', 'r') as f:
    data = json.load(f)

# Update version (bumping minor)
data['version'] = 'v1.1.0'

new_substrates = [
    {
      "id": 322,
      "name": "Cosmological Timeline of the Cathedral",
      "status": "active",
      "location": "agi/system32/integrity/"
    },
    {
      "id": 323,
      "name": "Cross-Cathedral Sync Protocol",
      "status": "active",
      "location": "agi/system32/integrity/"
    },
    {
      "id": 324,
      "name": "Zero-Downtime Rollout Strategy",
      "status": "active",
      "location": "agi/system32/integrity/"
    }
]

data['substrates'].extend(new_substrates)
data['substrates'].sort(key=lambda x: x['id'])

with open('.claude/SUBSTRATES.json', 'w') as f:
    json.dump(data, f, indent=2)
