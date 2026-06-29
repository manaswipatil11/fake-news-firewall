"""
plot_results.py — Figure generator for Fake News Firewall results
==================================================================
Reads CSVs produced by simulate.py and generates publication-quality
figures matching those in the group report and slide deck.

Usage
-----
  python3 plot_results.py                    # all figures
  python3 plot_results.py --figure strategy  # strategy comparison bar chart
  python3 plot_results.py --figure curve     # SEIR infection curve
  python3 plot_results.py --figure r0        # R0 over time

Output: results/figures/*.png
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
PALETTE = {
    'betweenness': '#00C98D',   # green
    'degree':      '#F0364A',   # red
    'random':      '#7B8BA5',   # slate
    'none':        '#F5A623',   # amber
}
LABELS = {
    'betweenness': 'Betweenness\nCentrality',
    'degree':      'Degree\nCentrality',
    'random':      'Random\nPlacement',
    'none':        'No\nIntervention',
}

plt.rcParams.update({
    'font.family':      'DejaVu Sans',
    'axes.spines.top':  False,
    'axes.spines.right': False,
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'figure.dpi':       150,
})


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: Strategy Comparison Bar Chart
# ══════════════════════════════════════════════════════════════════════════════

def plot_strategy_comparison():
    csv = RESULTS_DIR / "strategy_comparison.csv"
    if not csv.exists():
        print(f"  [!] {csv} not found. Run simulate.py first.")
        return

    df = pd.read_csv(csv)
    summary = df.groupby('strategy').agg(
        mean=('final_infection_pct', 'mean'),
        std=('final_infection_pct', 'std'),
        win_rate=('won', 'mean'),
    ).reset_index()

    order = ['betweenness', 'degree', 'random', 'none']
    summary['_ord'] = summary['strategy'].map({s: i for i, s in enumerate(order)})
    summary = summary.sort_values('_ord').reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Mean Infection %
    bars = ax1.bar(
        range(len(summary)),
        summary['mean'],
        yerr=summary['std'],
        color=[PALETTE[s] for s in summary['strategy']],
        capsize=5, width=0.55, error_kw={'linewidth': 1.5},
        alpha=0.88,
    )
    ax1.axhline(50, color='#F5A623', linestyle='--', linewidth=1.5, label='50% threshold')
    ax1.set_xticks(range(len(summary)))
    ax1.set_xticklabels([LABELS[s] for s in summary['strategy']], fontsize=11)
    ax1.set_ylabel('Mean Final Infection %', fontsize=12)
    ax1.set_ylim(0, 105)
    ax1.set_title('Final Infection % by Strategy', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    for i, (_, row) in enumerate(summary.iterrows()):
        ax1.text(i, row['mean'] + row['std'] + 2, f"{row['mean']:.0f}%",
                 ha='center', fontsize=11, fontweight='bold',
                 color=PALETTE[row['strategy']])

    # Right: Win Rate
    ax2.bar(
        range(len(summary)),
        summary['win_rate'] * 100,
        color=[PALETTE[s] for s in summary['strategy']],
        width=0.55, alpha=0.88,
    )
    ax2.set_xticks(range(len(summary)))
    ax2.set_xticklabels([LABELS[s] for s in summary['strategy']], fontsize=11)
    ax2.set_ylabel('Win Rate (%)', fontsize=12)
    ax2.set_ylim(0, 105)
    ax2.set_title('Win Rate by Strategy', fontsize=14, fontweight='bold')
    for i, (_, row) in enumerate(summary.iterrows()):
        ax2.text(i, row['win_rate'] * 100 + 2, f"{row['win_rate']*100:.0f}%",
                 ha='center', fontsize=11, fontweight='bold',
                 color=PALETTE[row['strategy']])

    fig.suptitle('Fake News Firewall — Strategy Comparison (n=100 runs)',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = FIGURES_DIR / "strategy_comparison.png"
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  ✓ Saved: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2: SEIR Infection Curve
# ══════════════════════════════════════════════════════════════════════════════

def plot_infection_curve():
    csv = RESULTS_DIR / "infection_curves.csv"
    if not csv.exists():
        print(f"  [!] {csv} not found. Run simulate.py --export-curve first.")
        # Generate theoretical curve as fallback
        _plot_theoretical_curve()
        return

    df = pd.read_csv(csv)
    strategies = df['strategy'].unique()

    fig, axes = plt.subplots(1, len(strategies), figsize=(6 * len(strategies), 5),
                             sharey=True)
    if len(strategies) == 1:
        axes = [axes]

    state_cols = {'S': '#3B82F6', 'I': '#F0364A', 'R': '#00C98D', 'V': '#9B6EFF'}

    for ax, strategy in zip(axes, strategies):
        sdf = df[df['strategy'] == strategy]
        for state, col in state_cols.items():
            if state in sdf.columns:
                ax.plot(sdf['tick'], sdf[state] / 120 * 100,
                        color=col, linewidth=2.5, label=state)
        ax.axhline(50, color='#F5A623', linestyle='--', linewidth=1.5,
                   label='50% threshold')
        ax.axvline(10, color='#F5A623', linestyle=':', linewidth=1,
                   alpha=0.7, label='Mutation (tick 10)')
        ax.set_xlabel('Tick', fontsize=11)
        ax.set_ylabel('Population %', fontsize=11)
        ax.set_title(f'Strategy: {LABELS.get(strategy, strategy).replace(chr(10), " ")}',
                     fontsize=12, fontweight='bold')
        ax.set_xlim(1, 20)
        ax.set_ylim(0, 105)
        ax.legend(fontsize=9)

    fig.suptitle('SEIR State Curves Over Simulation', fontsize=14, fontweight='bold')
    plt.tight_layout()
    out = FIGURES_DIR / "infection_curve.png"
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  ✓ Saved: {out}")


def _plot_theoretical_curve():
    """Fallback: plot theoretical continuous SIR curves."""
    ticks = 20
    sv, iv, rv = [1.0], [0.008], [0.0]
    b, g = 0.30, 0.18
    for _ in range(ticks - 1):
        s, i, r = sv[-1], iv[-1], rv[-1]
        sv.append(max(0, s - b*s*i))
        iv.append(max(0, i + b*s*i - g*i))
        rv.append(min(1, r + g*i))

    t = range(1, ticks + 1)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t, [v*100 for v in sv], color='#3B82F6', linewidth=2.5, label='Susceptible')
    ax.plot(t, [v*100 for v in iv], color='#F0364A', linewidth=3,   label='Infected')
    ax.plot(t, [v*100 for v in rv], color='#00C98D', linewidth=2.5, label='Recovered')
    ax.axhline(50, color='#F5A623', linestyle='--', linewidth=1.5, label='50% threshold')
    ax.axvline(10, color='#F5A623', linestyle=':', linewidth=1, alpha=0.7,
               label='Mutation event (tick 10)')
    ax.set_xlabel('Tick', fontsize=12)
    ax.set_ylabel('Population %', fontsize=12)
    ax.set_title('Theoretical SEIR Infection Curve (no intervention)',
                 fontsize=14, fontweight='bold')
    ax.set_xlim(1, 20); ax.set_ylim(0, 105)
    ax.legend(fontsize=11)
    plt.tight_layout()
    out = FIGURES_DIR / "infection_curve.png"
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  ✓ Saved (theoretical): {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3: R₀ Over Time
# ══════════════════════════════════════════════════════════════════════════════

def plot_r0_over_time():
    csv = RESULTS_DIR / "r0_over_time.csv"
    if not csv.exists():
        print(f"  [!] {csv} not found. Run simulate.py --export-r0 first.")
        return

    df = pd.read_csv(csv)
    fig, ax = plt.subplots(figsize=(9, 5))

    for strategy in df['strategy'].unique():
        sdf = df[df['strategy'] == strategy]
        ax.plot(sdf['tick'], sdf['r0'],
                color=PALETTE.get(strategy, 'gray'),
                linewidth=2, label=LABELS.get(strategy, strategy).replace('\n', ' '))

    ax.axhline(1.0, color='black', linestyle='--', linewidth=1.5,
               label='R₀ = 1 (epidemic threshold)')
    ax.axvline(10, color='#F5A623', linestyle=':', linewidth=1.2,
               alpha=0.8, label='Mutation (tick 10)')
    ax.set_xlabel('Tick', fontsize=12)
    ax.set_ylabel('Effective R₀', fontsize=12)
    ax.set_title('Effective R₀ Over Simulation by Strategy', fontsize=14, fontweight='bold')
    ax.set_xlim(1, 20)
    ax.legend(fontsize=10)
    plt.tight_layout()
    out = FIGURES_DIR / "r0_over_time.png"
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  ✓ Saved: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Fake News Firewall — Figure Generator')
    parser.add_argument('--figure', type=str, default='all',
                        choices=['all', 'strategy', 'curve', 'r0'],
                        help='Which figure to generate (default: all)')
    args = parser.parse_args()

    print("\n  Fake News Firewall — Plot Generator")
    print(f"  Output directory: {FIGURES_DIR}\n")

    if args.figure in ('all', 'strategy'):
        print("  [1/3] Strategy comparison chart...")
        plot_strategy_comparison()

    if args.figure in ('all', 'curve'):
        print("  [2/3] Infection curve...")
        plot_infection_curve()

    if args.figure in ('all', 'r0'):
        print("  [3/3] R₀ over time...")
        plot_r0_over_time()

    print("\n  Done. Open results/figures/ to view outputs.\n")


if __name__ == '__main__':
    main()
