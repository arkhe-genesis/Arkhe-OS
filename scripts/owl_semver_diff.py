
import sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL

def compare_owl(file1, file2):
    g1 = Graph()
    g1.parse(file1, format="xml")

    g2 = Graph()
    g2.parse(file2, format="xml")

    print(f"Comparing {file1} and {file2}")
    print(f"Graph 1 size: {len(g1)}")
    print(f"Graph 2 size: {len(g2)}")

    if len(g1) == len(g2):
        print("No changes detected.")
    else:
        print("Changes detected.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 owl_semver_diff.py <file1> <file2>")
        sys.exit(1)
    compare_owl(sys.argv[1], sys.argv[2])
