import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

def plot_bcg_matrix(bcg_result):
    products = bcg_result["products"]

    # Maps
    share_map = {"Low": 0, "High": 1}
    growth_map = {"Low": 0, "High": 1}

    # Quadrant centers (fixed)
    quadrant_centers = {
        ("High", "High"): (0.75, 0.75),   # Star
        ("High", "Low"): (0.25, 0.75),    # Question Mark
        ("Low", "High"): (0.75, 0.25),    # Cash Cow
        ("Low", "Low"): (0.25, 0.25),     # Dog
    }

    # Group products by quadrant
    quadrant_groups = defaultdict(list)
    for p in products:
        key = (p["market_growth"], p["relative_market_share"])
        quadrant_groups[key].append(p)

    plt.figure(figsize=(9, 9))

    # Spread parameters
    spread_radius = 0.12

    for (growth, share), items in quadrant_groups.items():
        cx, cy = quadrant_centers[(growth, share)]

        # Generate offsets in a circular pattern
        angles = np.linspace(0, 2 * np.pi, len(items), endpoint=False)

        for i, p in enumerate(items):
            dx = spread_radius * np.cos(angles[i])
            dy = spread_radius * np.sin(angles[i])

            x = cx + dx
            y = cy + dy

            size = 3000 * p["confidence"]
            label_offset = 0.03 + (size / 3000) * 0.02

            plt.scatter(
                x, y,
                s=size,
                alpha=0.85,
                edgecolors="black"
            )

            plt.text(
                x,
                y + label_offset,
                p["product"],
                ha="center",
                fontsize=10,
                weight="bold"
            )

    # Mid lines
    plt.axhline(0.5, linestyle="--", linewidth=1)
    plt.axvline(0.5, linestyle="--", linewidth=1)

    # Quadrant labels (YOUR convention)
    plt.text(0.05, 0.95, "Question Mark", fontsize=14, weight="bold")
    plt.text(0.55, 0.95, "Star", fontsize=14, weight="bold")
    plt.text(0.05, 0.05, "Dog", fontsize=14, weight="bold")
    plt.text(0.55, 0.05, "Cash Cow", fontsize=14, weight="bold")

    plt.xticks([0, 1], ["Low Market Share", "High Market Share"])
    plt.yticks([0, 1], ["Low Market Growth", "High Market Growth"])

    plt.title(
        f"Product-Level BCG Matrix — {bcg_result['company']}",
        fontsize=16,
        weight="bold"
    )

    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
