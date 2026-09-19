import argparse
import sys
import json
import yaml
import importlib.util
import os

def main():
    parser = argparse.ArgumentParser(description="ARKHE Blockchain Z CLI")
    subparsers = parser.add_subparsers(dest="command")

    publish_parser = subparsers.add_parser("publish", help="Publish the decree")
    publish_parser.add_argument("--format", help="Format to output the decree in (json or yaml)", choices=["json", "yaml"], default="json")

    args = parser.parse_args()

    if args.command == "publish":
        file_path = os.path.abspath('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py')
        spec = importlib.util.spec_from_file_location("substrato_870_blockchain_z_glm", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        canonizer = module.Substrato_870_blockchain_z_glm()
        path = canonizer.canonize()
        with open(path, "r") as f:
            data = json.load(f)

        if args.format == "yaml":
            print(yaml.dump(data))
        else:
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
