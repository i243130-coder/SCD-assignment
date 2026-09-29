"""Plot HPA scale-out during the k6 load test.

Usage:
    python plot_hpa.py                  # plot the embedded run (29 Sep 2026)
    python plot_hpa.py hpa_log.csv      # plot a timestamped capture (see below)

The embedded data is reconstructed from `kubectl get hpa -w`, whose AGE column
only has minute resolution, so events inside the same minute are spread evenly
and the k6 start time is inferred from when CPU first rose. For exact timing,
capture a log while the test runs (PowerShell):

    while ($true) {
      $h = kubectl get hpa backend-hpa -n civicpulse -o json | ConvertFrom-Json
      "$((Get-Date).ToString('o')),$($h.status.currentReplicas),$($h.status.currentMetrics[0].resource.current.averageUtilization)" |
        Add-Content hpa_log.csv
      Start-Sleep 5
    }

CSV columns (no header): ISO timestamp, replicas, cpu_percent
"""

import csv
import sys
from datetime import datetime

import matplotlib.pyplot as plt

# ── Run parameters ────────────────────────────────────────────
CPU_TARGET = 60          # hpa.yaml averageUtilization
MIN_REPLICAS, MAX_REPLICAS = 2, 10
K6_STAGES = [(1.0, 50), (2.0, 50), (0.5, 0)]   # (minutes, target VUs) from k6-script.js
K6_TOTAL_REQUESTS = 15348
K6_AVG_RPS = 72.8

# `kubectl get hpa -w` rows: (AGE minute, cpu %, replicas)
WATCH_ROWS = [
    (55, 2, 2), (56, 2, 2), (56, 24, 2), (56, 23, 2),
    (57, 106, 2), (57, 127, 4), (57, 100, 4), (57, 79, 5),
    (58, 76, 5), (58, 65, 5), (58, 62, 5),
    (59, 54, 5),
    (60, 10, 5), (60, 2, 5),
]
K6_START_AGE = 56.2      # inferred: first CPU rise in minute 56


def spread_rows(rows):
    """Spread same-minute rows evenly across that minute."""
    out, by_min = [], {}
    for m, *_ in rows:
        by_min[m] = by_min.get(m, 0) + 1
    seen = {}
    for m, cpu, reps in rows:
        i = seen.get(m, 0)
        seen[m] = i + 1
        out.append((m + i / by_min[m], cpu, reps))
    return out


def load_csv(path):
    rows = []
    with open(path, newline="") as f:
        for ts, reps, cpu in csv.reader(f):
            if not cpu:          # metric not yet available (<unknown>)
                continue
            rows.append((datetime.fromisoformat(ts.strip()), float(cpu), int(reps)))
    t0 = rows[0][0]
    return [((t - t0).total_seconds() / 60, c, r) for t, c, r in rows]


def k6_profile(start):
    """Piecewise-linear VU schedule from the k6 stages."""
    t, v = [start], [0]
    for dur, target in K6_STAGES:
        t.append(t[-1] + dur)
        v.append(target)
    return t, v


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            data = load_csv(path)
        except FileNotFoundError:
            sys.exit(f"{path} not found - run the capture loop from this file's docstring "
                     "during a k6 test first (it writes hpa_log.csv in the current folder).")
        if not data:
            sys.exit(f"{path} has no rows with a CPU value yet - let the capture run longer.")
        k6_start = None
        xlabel = "Minutes since capture started"
    else:
        data = spread_rows(WATCH_ROWS)
        k6_start = K6_START_AGE
        xlabel = "HPA age (minutes)  ·  reconstructed from kubectl get hpa -w"

    t = [d[0] for d in data]
    cpu = [d[1] for d in data]
    reps = [d[2] for d in data]

    blue, ink, muted, grid = "#2a78d6", "#0b0b0b", "#52514e", "#e6e5e1"
    plt.rcParams.update({
        "font.size": 10, "axes.edgecolor": grid, "axes.labelcolor": muted,
        "xtick.color": muted, "ytick.color": muted, "axes.titlecolor": ink,
        "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlelocation": "left",
    })

    n_panels = 3 if k6_start is not None else 2
    fig, axes = plt.subplots(n_panels, 1, sharex=True, figsize=(9, 2.4 * n_panels + 0.8),
                             facecolor="#fcfcfb")
    for ax in axes:
        ax.set_facecolor("#fcfcfb")
        ax.grid(axis="y", color=grid, linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(length=0)

    # 1 — replicas
    ax = axes[0]
    ax.step(t, reps, where="post", color=blue, linewidth=2)
    ax.plot(t, reps, "o", color=blue, markersize=4, markeredgecolor="#fcfcfb", markeredgewidth=1.5)
    ax.axhline(MIN_REPLICAS, color=muted, linewidth=1, linestyle=":")
    ax.text(t[0], MIN_REPLICAS + 0.15, f"minReplicas {MIN_REPLICAS}", color=muted, fontsize=8)
    ax.set_ylim(0, max(reps) + 1.5)
    ax.set_yticks(range(0, max(reps) + 2))
    ax.set_title(f"Backend replicas  ·  {min(reps)} → {max(reps)}")
    peak_i = reps.index(max(reps))
    ax.annotate(f"{max(reps)} pods", (t[peak_i], max(reps)), xytext=(6, 6),
                textcoords="offset points", color=ink, fontsize=9)

    # 2 — CPU vs target
    ax = axes[1]
    ax.plot(t, cpu, color=blue, linewidth=2, marker="o", markersize=4,
            markeredgecolor="#fcfcfb", markeredgewidth=1.5)
    ax.axhline(CPU_TARGET, color=muted, linewidth=1, linestyle="--")
    ax.text(t[0], CPU_TARGET + 4, f"target {CPU_TARGET}%", color=muted, fontsize=8)
    ax.set_ylim(0, max(cpu) * 1.15)
    ax.set_ylabel("% of CPU request")
    ax.set_title("Average CPU utilization")
    pk = cpu.index(max(cpu))
    ax.annotate(f"peak {max(cpu):.0f}%", (t[pk], cpu[pk]), xytext=(6, 2),
                textcoords="offset points", color=ink, fontsize=9)

    # 3 — k6 load
    if k6_start is not None:
        ax = axes[2]
        kt, kv = k6_profile(k6_start)
        ax.fill_between(kt, kv, color=blue, alpha=0.15, linewidth=0)
        ax.plot(kt, kv, color=blue, linewidth=2)
        ax.set_ylim(0, 60)
        ax.set_ylabel("virtual users")
        ax.set_title("k6 load  ·  scheduled VUs (start time inferred)")
        ax.text(kt[1] + 0.05, 53, f"{K6_TOTAL_REQUESTS:,} requests · {K6_AVG_RPS} req/s avg · 0% failed",
                color=ink, fontsize=9)

    axes[-1].set_xlabel(xlabel)
    fig.suptitle("CivicPulse HPA scale-out under load", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", color=ink)
    fig.tight_layout()
    out = "hpa_scaling.png"
    fig.savefig(out, dpi=160, facecolor=fig.get_facecolor())
    print(f"saved {out}")


if __name__ == "__main__":
    main()
