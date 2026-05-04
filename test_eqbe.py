import requests

url = "http://localhost:5000/api/subagent/G4/ethics-impact"
data = {
    "proposal": "Chrono-Coil Biosensor Mesh for continuous cortisol and physiological monitoring.",
    "category": "Health Monitoring"
}

try:
    response = requests.post(url, json=data)
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
