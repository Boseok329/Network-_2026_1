"""
delay_simulator.py
==================
Regenerates the two figures used in the README.

1. queueing-explosion.png
   The M/M/1 average queueing delay as a function of traffic intensity rho.
   This is the theoretical backbone of the "Problem" section: queueing delay
   stays near zero while rho is small, then blows up non-linearly as rho -> 1.

2. tcp-udp-p99-explosion.png
   TCP vs UDP P99 round-trip time, with and without 1% packet loss.
   These are our team's own measured numbers (Docker + tc netem, 1000 orders
   per run). The point is the asymmetry: a 1% loss rate barely moves UDP but
   pushes TCP's P99 from ~376 us to ~205 ms.

Run:  python3 delay_simulator.py
Output goes to ./figures/
"""

import os
import matplotlib

matplotlib.use("Agg")  # headless: write PNGs without a display
import matplotlib.pyplot as plt
import numpy as np

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ----- shared style -------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "figure.dpi": 130,
})

TCP_COLOR = "#d62828"   # red  -> the protocol that explodes under loss
UDP_COLOR = "#1d6fb8"   # blue -> the protocol that stays flat


def plot_queueing_explosion():
    """Average queueing delay (in units of L/R) vs traffic intensity rho.

    M/M/1 result:  E[w] = rho / (1 - rho) * (L / R)
    We plot the dimensionless factor rho / (1 - rho).
    """
    rho = np.linspace(0, 0.985, 500)
    delay = rho / (1 - rho)  # in multiples of (L / R)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(rho, delay, color="#c1121f", linewidth=2.6)

    # mark a "normal load" point and a "volatility spike" point
    for r, label in [(0.7, "normal load\nρ≈0.7"), (0.95, "volatility spike\nρ≈0.95")]:
        d = r / (1 - r)
        ax.scatter([r], [d], color="#003049", zorder=5, s=40)
        ax.annotate(label, xy=(r, d), xytext=(r - 0.32, d + 6),
                    fontsize=10, color="#003049",
                    arrowprops=dict(arrowstyle="->", color="#003049", lw=1.2))

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 70)
    ax.set_xlabel("Traffic intensity  ρ = La / R")
    ax.set_ylabel("Average queueing delay  (multiples of L/R)")
    ax.set_title("Queueing delay is non-linear: it explodes as ρ → 1", fontsize=13, weight="bold")
    ax.axvline(1.0, color="#888888", linestyle="--", linewidth=1)
    ax.text(0.965, 64, "ρ → 1\nbuffer overflow,\npacket loss", fontsize=9,
            color="#888888", ha="right", va="top")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "queueing-explosion.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def plot_tcp_udp_p99():
    """TCP vs UDP P99 RTT, no loss vs 1% loss. Our measured data."""
    # measured P99 in microseconds
    data = {
        "No loss":  {"TCP": 375.7,    "UDP": 386.1},
        "1% loss":  {"TCP": 204812.0, "UDP": 374.5},
    }
    scenarios = list(data.keys())
    x = np.arange(len(scenarios))
    width = 0.36

    tcp_vals = [data[s]["TCP"] for s in scenarios]
    udp_vals = [data[s]["UDP"] for s in scenarios]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    b1 = ax.bar(x - width / 2, tcp_vals, width, label="TCP", color=TCP_COLOR)
    b2 = ax.bar(x + width / 2, udp_vals, width, label="UDP", color=UDP_COLOR)

    ax.set_yscale("log")
    ax.set_ylim(100, 500000)
    ax.set_ylabel("P99 round-trip time  (µs, log scale)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_title("One percent packet loss inflates TCP's P99 by ~545×",
                 fontsize=13, weight="bold")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25, which="both")

    def label_bars(bars, vals):
        for bar, v in zip(bars, vals):
            txt = f"{v/1000:.0f} ms" if v >= 1000 else f"{v:.0f} µs"
            ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15, txt,
                    ha="center", va="bottom", fontsize=9.5)

    label_bars(b1, tcp_vals)
    label_bars(b2, udp_vals)

    # annotate the 545x gap
    ax.annotate("545×", xy=(1 - width / 2, 204812), xytext=(0.35, 90000),
                fontsize=14, weight="bold", color=TCP_COLOR,
                arrowprops=dict(arrowstyle="->", color=TCP_COLOR, lw=1.4))

    fig.tight_layout()
    out = os.path.join(FIG_DIR, "tcp-udp-p99-explosion.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    plot_queueing_explosion()
    plot_tcp_udp_p99()
    print("done")
