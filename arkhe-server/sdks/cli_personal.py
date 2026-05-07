import argparse

def main():
    parser = argparse.ArgumentParser(description="Arkhe Personal CLI")
    parser.add_argument("--action", help="Action to perform")
    args = parser.parse_args()
    print(f"Executing personal action: {args.action}")

if __name__ == "__main__":
    main()
