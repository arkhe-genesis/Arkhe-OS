import argparse

def main():
    parser = argparse.ArgumentParser(description="Arkhe Enterprise CLI")
    parser.add_argument("--deploy", help="Deploy resources")
    args = parser.parse_args()
    print(f"Deploying enterprise resource: {args.deploy}")

if __name__ == "__main__":
    main()
