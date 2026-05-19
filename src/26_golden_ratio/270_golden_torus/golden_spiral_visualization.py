import sys
import os
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from torus_engine import GoldenTorusEngine

def main():
    engine = GoldenTorusEngine()
    nodes = engine._generate_golden_spiral_nodes(233, "viz")

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    xs = [n.x for n in nodes]
    ys = [n.y for n in nodes]
    zs = [n.z for n in nodes]

    ax.scatter(xs, ys, zs, c='gold', marker='o', s=50, alpha=0.8, edgecolors='orange')

    # Plot gaps for a subset to show connectivity without cluttering
    # Limit max_distance to show local connections
    gaps = engine._generate_gaps(nodes, permeability_base=1.0, max_distance=0.3)

    # Pre-compute positions for faster line plotting
    pos_map = {n.id: (n.x, n.y, n.z) for n in nodes}
    for gap in gaps:
        p1 = pos_map[gap.node1_id]
        p2 = pos_map[gap.node2_id]
        # Line width based on resonance
        lw = gap.resonance * 0.5
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                color='teal', alpha=0.3, linewidth=lw)

    ax.set_title("Golden Torus Spiral (233 Nodes + 1D Gaps)")
    ax.set_axis_off()

    out_file = os.path.join(os.path.dirname(__file__), "golden_spiral.png")
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {out_file}")

if __name__ == "__main__":
    main()
