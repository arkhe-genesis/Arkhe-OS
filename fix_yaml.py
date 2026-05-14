import yaml
try:
    with open(".github/workflows/arkhe-ma-s2-check.yml", "r") as f:
        data = yaml.safe_load(f)
    print("YAML is valid.")
except yaml.YAMLError as exc:
    print(exc)
