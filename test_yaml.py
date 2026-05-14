import yaml
with open('.github/workflows/arkhe-ma-s2-check.yml', 'r') as f:
    try:
        yaml.safe_load(f)
        print("YAML is valid.")
    except Exception as e:
        print(f"Error parsing YAML: {e}")
