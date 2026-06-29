"""
simulate.py — Headless batch SEIR simulator for Fake News Firewall
===================================================================
Reproduces the numerical results from the group report without
requiring a browser. Runs multiple strategies across N_RUNS
simulations and saves results to results/strategy_comparison.csv.

Usage
-----
  python3 simulate.py                        # all strategies, 100 runs
  python3 simulate.py --runs 50              # faster run
  python3 simulate.py --strategy betweenness # one strategy only
  python3 simulate.py --export-curve         # also save tick-by-tick curve
  python3 simulate.py --export-r0            # also save R0 per tick

Dependencies: numpy, networkx, pandas  (see requirements.txt)
"""

import argparse
import random
import math
import numpy as np
import networkx as nx
import pandas as pd
import os
from pathlib import Path

# ── Output directory ──────────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── Model constants ───────────────────────────────────────────────────────────
N          = 120       # nodes
M_ATTACH   = 2        # BA attachment parameter
N_CLUSTERS = 4        # community count
INTRA_PROB = 0.72     # probability edge stays within cluster

BETA       = 0.30     # base transmission rate
GAMMA      = 0.18     # recovery rate per tick
DELTA      = 0.09     # relapse rate (post-mutation)
HUB_AMP    = 2.6      # hub transmission multiplier
HUB_PCT    = 0.08     # top X% of degree → hub
MAX_TICKS  = 20
MUTATION_TICK = 10
WIN_THR    = 0.50     # infection < 50% → win
TOKENS     = 5        # fact-checker budget

# SEIR states
S, E, I, R, V = 0, 1, 2, 3, 4


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def build_graph(seed=None):
    """
    Barabási–Albert preferential attachment with community bias.
    Returns: G (networkx.Graph), cluster_map (dict: node→cluster),
             hub_set (set of hub node ids).
    """
    rng = random.Random(seed)
    np.random.seed(seed if seed is not None else 42)

    G = nx.Graph()
    cluster_map = {}

    # Assign clusters round-robin
    for i in range(N):
        G.add_node(i)
        cluster_map[i] = i % N_CLUSTERS

    # Seed ring: connect first 6 nodes
    for i in range(min(6, N)):
        G.add_edge(i, (i + 1) % 6)

    # Preferential attachment with cluster bias
    degrees = {i: G.degree(i) for i in G.nodes()}

    for i in range(6, N):
        ci = cluster_map[i]
        targets = set()
        attempts = 0
        while len(targets) < M_ATTACH and attempts < 300:
            attempts += 1
            same = rng.random() < INTRA_PROB
            pool = [n for n in range(i) if (cluster_map[n] == ci) == same or not same]
            if not pool:
                pool = list(range(i))
            total_deg = sum(degrees.get(n, 0) + 1 for n in pool)
            r = rng.random() * total_deg
            cumulative = 0
            for n in pool:
                cumulative += degrees.get(n, 0) + 1
                if cumulative >= r:
                    targets.add(n)
                    break

        for t in targets:
            if not G.has_edge(i, t):
                G.add_edge(i, t)
                degrees[i] = degrees.get(i, 0) + 1
                degrees[t] = degrees.get(t, 0) + 1

    # Hub identification: top HUB_PCT by degree
    deg_vals = sorted([d for _, d in G.degree()], reverse=True)
    threshold = deg_vals[max(0, int(N * HUB_PCT) - 1)]
    hub_set = {n for n, d in G.degree() if d >= threshold}

    return G, cluster_map, hub_set


def louvain_communities(G):
    """
    Louvain community detection via NetworkX.
    Returns dict: node → community_id.
    """
    try:
        from networkx.algorithms.community import louvain_communities
        comms = louvain_communities(G, seed=42)
        comm_map = {}
        for cid, comm in enumerate(comms):
            for node in comm:
                comm_map[node] = cid
        return comm_map
    except ImportError:
        # Fallback: use round-robin clusters
        return {n: n % N_CLUSTERS for n in G.nodes()}


def betweenness_ranking(G):
    """
    Compute betweenness centrality using NetworkX (Brandes algorithm).
    Returns list of nodes sorted by betweenness descending.
    """
    bc = nx.betweenness_centrality(G, normalized=True)
    return sorted(bc.keys(), key=lambda n: bc[n], reverse=True), bc


def degree_ranking(G):
    """Nodes sorted by degree descending."""
    return sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# EPIDEMIC SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def run_simulation(G, hub_set, strategy='none', token_budget=TOKENS, rng=None):
    """
    Run one SEIR simulation.

    strategy: 'betweenness' | 'degree' | 'random' | 'none'

    Returns dict with simulation results.
    """
    if rng is None:
        rng = random.Random()

    nodes = list(G.nodes())
    adj = {n: list(G.neighbors(n)) for n in nodes}

    # Initial state: all Susceptible
    state = {n: S for n in nodes}

    # Patient Zero: random node
    pz = rng.choice(nodes)
    state[pz] = I

    # Pre-compute vaccination targets based on strategy
    if strategy == 'betweenness':
        ranked, _ = betweenness_ranking(G)
    elif strategy == 'degree':
        ranked = degree_ranking(G)
    elif strategy == 'random':
        ranked = nodes[:]
        rng.shuffle(ranked)
    else:
        ranked = []

    tokens_left = token_budget
    mut_fired = False
    exposed_timer = {n: 0 for n in nodes}

    # Deploy tokens for automated strategies (simulate optimal early deployment)
    # Tokens are deployed at tick 1 (before simulation starts) for fair comparison
    vaccinated_count = 0
    if strategy != 'none' and ranked:
        for candidate in ranked:
            if tokens_left <= 0:
                break
            if state[candidate] == S and candidate != pz:
                state[candidate] = V
                tokens_left -= 1
                vaccinated_count += 1

    # Tick-by-tick records
    history = []
    r0_history = []
    prev_infected = 1
    new_infections = 0

    for tick in range(1, MAX_TICKS + 1):
        if tick == MUTATION_TICK:
            mut_fired = True

        new_infections = 0
        next_state = dict(state)

        for n in nodes:
            if state[n] == V:
                continue
            if state[n] == I:
                for nb in adj[n]:
                    if state[nb] == S:
                        b = BETA * (HUB_AMP if n in hub_set else 1.0)
                        if rng.random() < b:
                            next_state[nb] = E
                            new_infections += 1
                if rng.random() < GAMMA:
                    next_state[n] = R
            elif state[n] == E:
                exposed_timer[n] += 1
                if exposed_timer[n] >= 2:
                    next_state[n] = I
                    exposed_timer[n] = 0
            elif state[n] == R and mut_fired:
                if rng.random() < DELTA:
                    next_state[n] = I
                    new_infections += 1

        state = next_state

        counts = {s: sum(1 for v in state.values() if v == s) for s in [S, E, I, R, V]}
        inf_pct = counts[I] / N

        # Rolling R0 estimate
        if prev_infected > 0:
            r0_est = new_infections / prev_infected
            r0_history.append(r0_est)
        prev_infected = counts[I]

        history.append({
            'tick': tick,
            'S': counts[S], 'E': counts[E], 'I': counts[I],
            'R': counts[R], 'V': counts[V],
            'inf_pct': inf_pct,
            'r0': r0_history[-1] if r0_history else 0,
        })

        if inf_pct >= WIN_THR:
            # Early loss
            return {
                'won': False,
                'final_inf_pct': inf_pct,
                'tokens_used': vaccinated_count,
                'ticks_to_threshold': tick,
                'history': history,
                'r0_history': r0_history,
            }

        if counts[I] == 0:
            break

    final_inf = history[-1]['inf_pct']
    return {
        'won': final_inf < WIN_THR,
        'final_inf_pct': final_inf,
        'tokens_used': vaccinated_count,
        'ticks_to_threshold': MAX_TICKS,
        'history': history,
        'r0_history': r0_history,
    }


# ══════════════════════════════════════════════════════════════════════════════
# BATCH RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def batch_run(strategies, n_runs, export_curve=False, export_r0=False):
    print(f"\n{'='*60}")
    print(f"  Fake News Firewall — Batch Simulation")
    print(f"  Strategies: {strategies}")
    print(f"  Runs per strategy: {n_runs}")
    print(f"{'='*60}\n")

    all_results = []
    curve_data = []
    r0_data = []

    for strategy in strategies:
        wins = 0
        inf_pcts = []
        print(f"  Running strategy: {strategy:15s} ", end="", flush=True)

        for run_id in range(n_runs):
            seed = run_id * 1000 + hash(strategy) % 1000
            G, cluster_map, hub_set = build_graph(seed=seed)
            rng = random.Random(seed + 1)
            result = run_simulation(G, hub_set, strategy=strategy, rng=rng)

            if result['won']:
                wins += 1
            inf_pcts.append(result['final_inf_pct'] * 100)

            all_results.append({
                'strategy': strategy,
                'run_id': run_id,
                'won': int(result['won']),
                'final_infection_pct': round(result['final_inf_pct'] * 100, 2),
                'tokens_used': result['tokens_used'],
                'ticks_to_threshold': result['ticks_to_threshold'],
            })

            if export_curve and run_id == 0:
                for row in result['history']:
                    curve_data.append({'strategy': strategy, **row})

            if export_r0 and run_id == 0:
                for t, r0 in enumerate(result['r0_history'], 1):
                    r0_data.append({'strategy': strategy, 'tick': t, 'r0': r0})

            if (run_id + 1) % 10 == 0:
                print(".", end="", flush=True)

        mean_inf = np.mean(inf_pcts)
        std_inf  = np.std(inf_pcts)
        win_rate = wins / n_runs * 100

        print(f"  ✓")
        print(f"    Mean infection: {mean_inf:.1f}% ± {std_inf:.1f}%  |  "
              f"Win rate: {win_rate:.0f}%  ({wins}/{n_runs})")

    # Save results
    df = pd.DataFrame(all_results)
    out_path = RESULTS_DIR / "strategy_comparison.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  Results saved → {out_path}")

    if export_curve and curve_data:
        curve_path = RESULTS_DIR / "infection_curves.csv"
        pd.DataFrame(curve_data).to_csv(curve_path, index=False)
        print(f"  Curves saved  → {curve_path}")

    if export_r0 and r0_data:
        r0_path = RESULTS_DIR / "r0_over_time.csv"
        pd.DataFrame(r0_data).to_csv(r0_path, index=False)
        print(f"  R0 data saved → {r0_path}")

    # Summary table
    print(f"\n{'='*60}")
    print(f"  SUMMARY TABLE")
    print(f"  {'Strategy':<22} {'Mean Inf%':>10} {'Std':>8} {'Win Rate':>10}")
    print(f"  {'-'*52}")
    summary = df.groupby('strategy').agg(
        mean_inf=('final_infection_pct', 'mean'),
        std_inf=('final_infection_pct', 'std'),
        win_rate=('won', 'mean'),
    ).reset_index()
    for _, row in summary.iterrows():
        print(f"  {row['strategy']:<22} {row['mean_inf']:>9.1f}% "
              f"{row['std_inf']:>7.1f}%  {row['win_rate']*100:>8.0f}%")
    print(f"{'='*60}\n")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Fake News Firewall — Headless SEIR Batch Simulator')
    parser.add_argument('--runs', type=int, default=100,
                        help='Number of simulation runs per strategy (default: 100)')
    parser.add_argument('--strategy', type=str, default='all',
                        choices=['all', 'betweenness', 'degree', 'random', 'none'],
                        help='Strategy to simulate (default: all)')
    parser.add_argument('--export-curve', action='store_true',
                        help='Export tick-by-tick SEIR state data')
    parser.add_argument('--export-r0', action='store_true',
                        help='Export R0 estimate per tick')
    args = parser.parse_args()

    if args.strategy == 'all':
        strategies = ['betweenness', 'degree', 'random', 'none']
    else:
        strategies = [args.strategy]

    batch_run(
        strategies=strategies,
        n_runs=args.runs,
        export_curve=args.export_curve,
        export_r0=args.export_r0,
    )


if __name__ == '__main__':
    main()
