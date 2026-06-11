"""
delay_simulator.py
README에 들어가는 그래프 2개 그리는 코드.

1. queueing-explosion.png
   - 트래픽 강도 rho 따라 큐잉지연 어떻게 변하는지 (M/M/1)
   - rho 작을때는 거의 0인데 1 가까워지면 확 터짐 -> Problem 파트 핵심 그림
2. tcp-udp-p99-explosion.png
   - 우리가 측정한 TCP vs UDP P99 (도커 + tc netem, 1000개 돌림)
   - 손실 1% 줬을때 UDP는 거의 그대론데 TCP는 376us -> 205ms 로 튐

그냥 python3 delay_simulator.py 하면 figures 폴더에 png 두개 나옴.
"""

import os
import matplotlib

matplotlib.use("Agg")  # 화면 없이 그냥 png로 저장하려고 Agg 씀
import matplotlib.pyplot as plt
import numpy as np

# 이 파일 기준으로 figures 폴더 경로 잡고, 없으면 만들기
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# 두 그림 공통 스타일 (폰트, 선 굵기 이런거 미리 박아둠)
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "figure.dpi": 130,
})

TCP_COLOR = "#d62828"   # TCP는 빨강 (손실나면 터지는 쪽)
UDP_COLOR = "#1d6fb8"   # UDP는 파랑 (계속 평평한 쪽)


def plot_queueing_explosion():
    """큐잉지연 vs 트래픽강도 rho 그래프. M/M/1 식 E[w] = rho/(1-rho) * (L/R)."""
    # rho 1 넘어가면 식이 발산해서 0.985 까지만 그림
    rho = np.linspace(0, 0.985, 500)
    delay = rho / (1 - rho)  # L/R 단위로 보는거라 그냥 비율만 계산

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(rho, delay, color="#c1121f", linewidth=2.6)

    # 평소(0.7)랑 변동성 터질때(0.95) 두 점 찍어서 화살표로 표시
    for r, label in [(0.7, "normal load\nρ≈0.7"), (0.95, "volatility spike\nρ≈0.95")]:
        d = r / (1 - r)
        ax.scatter([r], [d], color="#003049", zorder=5, s=40)
        ax.annotate(label, xy=(r, d), xytext=(r - 0.32, d + 6),
                    fontsize=10, color="#003049",
                    arrowprops=dict(arrowstyle="->", color="#003049", lw=1.2))

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 70)  # 너무 높이 올라가면 모양 안보여서 70에서 자름
    ax.set_xlabel("Traffic intensity  ρ = La / R")
    ax.set_ylabel("Average queueing delay  (multiples of L/R)")
    ax.set_title("Queueing delay is non-linear: it explodes as ρ → 1", fontsize=13, weight="bold")
    # rho=1 위치에 점선 긋고 버퍼 넘쳐서 손실난다고 메모
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
    """우리가 측정한 TCP vs UDP P99. 무손실 vs 손실1% 비교."""
    # 실측 P99 값 (단위 us). 손실 1%일때 TCP가 20만us 넘어감
    data = {
        "No loss":  {"TCP": 375.7,    "UDP": 386.1},
        "1% loss":  {"TCP": 204812.0, "UDP": 374.5},
    }
    scenarios = list(data.keys())
    x = np.arange(len(scenarios))
    width = 0.36

    # TCP / UDP 따로 막대 뽑아두기
    tcp_vals = [data[s]["TCP"] for s in scenarios]
    udp_vals = [data[s]["UDP"] for s in scenarios]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    b1 = ax.bar(x - width / 2, tcp_vals, width, label="TCP", color=TCP_COLOR)
    b2 = ax.bar(x + width / 2, udp_vals, width, label="UDP", color=UDP_COLOR)

    # 로그 스케일 안하면 UDP 막대가 너무 작아서 안보임 (차이가 545배라)
    ax.set_yscale("log")
    ax.set_ylim(100, 500000)
    ax.set_ylabel("P99 round-trip time  (µs, log scale)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_title("One percent packet loss inflates TCP's P99 by ~545×",
                 fontsize=13, weight="bold")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25, which="both")

    # 막대 위에 숫자 붙이는 부분. 1000us 넘으면 ms로 바꿔서 표기
    def label_bars(bars, vals):
        for bar, v in zip(bars, vals):
            txt = f"{v/1000:.0f} ms" if v >= 1000 else f"{v:.0f} µs"
            ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15, txt,
                    ha="center", va="bottom", fontsize=9.5)

    label_bars(b1, tcp_vals)
    label_bars(b2, udp_vals)

    # TCP 막대에 545배라고 화살표로 강조
    ax.annotate("545×", xy=(1 - width / 2, 204812), xytext=(0.35, 90000),
                fontsize=14, weight="bold", color=TCP_COLOR,
                arrowprops=dict(arrowstyle="->", color=TCP_COLOR, lw=1.4))

    fig.tight_layout()
    out = os.path.join(FIG_DIR, "tcp-udp-p99-explosion.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    # 두개 다 그리기
    plot_queueing_explosion()
    plot_tcp_udp_p99()
    print("done")
