import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--grid-name")
    parser.add_argument("--output")
    parser.add_argument("--extract-observables")
    parser.add_argument("--ml-reconstruction")
    parser.add_argument("--compare-cosmology")
    args = parser.parse_args()

    print(f"Simulating grid {args.grid_name}")
    # Touch the output h5 file to pretend we generated it
    with open(args.output, "w") as f:
        f.write("mock h5 file")

if __name__ == "__main__":
    main()
