# 🔥 Fake News Firewall

> **Modelling Misinformation Propagation as a Modified SEIR Epidemic on Scale-Free Social Networks**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Language: JavaScript](https://img.shields.io/badge/Language-JavaScript-f7df1e.svg)]()
[![No Dependencies](https://img.shields.io/badge/Dependencies-None-green.svg)]()

A browser-based interactive epidemic simulator where misinformation spreads like a virus across a social network. Players deploy fact-checker tokens to contain the outbreak before it reaches 50% of nodes.

**Course:** Computer Networks — National Chung Cheng University, Spring 2026  
**Group Members:**
| Member | Student ID | Role |
|--------|-----------|------|
| Manaswi | 614410168 | Graph & Network Engine |
| [Member 2] | — | Epidemic Model (SEIR) |
| [Member 3] | — | Frontend & Game UI |
| [Member 4] | — | Analysis & Results |

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Overview](#-project-overview)
- [Repository Structure](#-repository-structure)
- [How to Run](#-how-to-run)
- [Reproducing Results](#-reproducing-results)
- [Technical Architecture](#-technical-architecture)
- [Model Parameters](#-model-parameters)
- [Acknowledgments](#-acknowledgments)

---

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fake-news-firewall.git
cd fake-news-firewall

# Open the game directly in your browser — no server needed
open src/FakeNewsFirewall.html        # macOS
xdg-open src/FakeNewsFirewall.html   # Linux
start src/FakeNewsFirewall.html       # Windows
```

That's it. No installation, no dependencies, no build step.

---

## 🎯 Project Overview

### Motivation

In 2016, the **Pizzagate conspiracy theory** reached 1.7 million Facebook users before being debunked, resulting in a real-world armed incident. We argue this is not a *content* problem but a **network topology problem** — the structure of who is connected to whom determines how far misinformation spreads, not what the story says.

### Core Idea

We model misinformation propagation as a **modified SEIR epidemic** on a **Barabási–Albert scale-free graph** with **Louvain community structure** (echo chambers). Players act as fact-checking organisations with a limited budget of 5 tokens and must decide strategically which nodes to vaccinate.

### Key Finding

> **Betweenness centrality outperforms degree centrality by 2.7× in win rate (84% vs 31%).**  
> Targeting bridge nodes between echo chambers is more effective than targeting high-degree influencer hubs.

---

## 📁 Repository Structure

```
fake-news-firewall/
│
├── src/
│   └── FakeNewsFirewall.html        # Complete game — single self-contained file
│
├── scripts/
│   ├── simulate.py                  # Headless Python SEIR batch simulator
│   ├── plot_results.py              # Generates all result figures
│   └── requirements.txt            # Python dependencies
│
├── results/
│   ├── strategy_comparison.csv      # Raw simulation data (100 runs × 4 strategies)
│   ├── infection_curves.csv         # Tick-by-tick SEIR state counts
│   └── figures/
│       ├── strategy_comparison.png  # Bar chart: mean infection % by strategy
│       ├── infection_curve.png      # SEIR curve over 20 ticks
│       └── r0_over_time.png        # R₀ estimate per tick
│
├── docs/
│   ├── FakeNewsFirewall_Report_Manaswi.pdf   # Individual final report
│   ├── FakeNewsFirewall_Presentation.pptx   # Group slide deck
│   └── FakeNewsFirewall_Poster.pdf          # A0 group poster
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🚀 How to Run

### Option 1: Browser (Recommended — Zero Setup)

Open `src/FakeNewsFirewall.html` in any modern browser (Chrome, Firefox, Safari, Edge).

**Works on:**
- 💻 Laptop / Desktop — full side-by-side layout
- 📱 Mobile / Tablet — responsive stacked layout with larger touch targets
- 🔴 QR code scan — same URL, auto-detects mobile

**No internet connection required.** All code is self-contained in a single HTML file.

### Option 2: Local HTTP Server (Optional)

If your browser blocks local file access:

```bash
# Python 3
cd fake-news-firewall
python3 -m http.server 8080
# Then open: http://localhost:8080/src/FakeNewsFirewall.html
```

### Option 3: Python Headless Simulation

To reproduce the numerical results from the report without the browser UI:

```bash
cd fake-news-firewall
pip install -r scripts/requirements.txt
python3 scripts/simulate.py
python3 scripts/plot_results.py
```

Output figures are saved to `results/figures/`.

---

## 📊 Reproducing Results

### Main Result: Strategy Comparison (Table in report, slide 16)

```bash
python3 scripts/simulate.py --runs 100 --strategies all
```

Produces `results/strategy_comparison.csv` with columns:
`strategy, run_id, final_infection_pct, tokens_used, ticks_to_50pct, won`

Expected output:
| Strategy | Mean Infection% | Win Rate |
|----------|----------------|----------|
| Betweenness Centrality | 29% ± 8% | 84% |
| Degree Centrality | 61% ± 11% | 31% |
| Random Placement | 74% ± 9% | 12% |
| No Intervention | 88% ± 5% | 0% |

### SEIR Infection Curve (Figure in report)

```bash
python3 scripts/simulate.py --strategy betweenness --runs 1 --export-curve
python3 scripts/plot_results.py --figure infection_curve
```

### R₀ Tracking

```bash
python3 scripts/simulate.py --strategy betweenness --runs 20 --export-r0
python3 scripts/plot_results.py --figure r0_over_time
```

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FakeNewsFirewall.html                       │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                   │
│  │  Graph Engine    │   │  Epidemic Engine  │                   │
│  │  (Member 1)      │──▶│  (Member 2)       │                   │
│  │                  │   │                   │                   │
│  │ • BA generation  │   │ • SEIR state FSM  │                   │
│  │ • Louvain        │   │ • β, γ, δ params  │                   │
│  │ • Betweenness    │   │ • Hub amplify 2.6x│                   │
│  │ • FR layout      │   │ • Mutation tick10 │                   │
│  └──────────────────┘   └──────────────────┘                   │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌──────────────────────────────────────────┐                   │
│  │          HTML5 Canvas Renderer           │                   │
│  │          (Member 3)                      │                   │
│  │  • Pulse-ring animations on infected     │                   │
│  │  • Cluster background wash               │                   │
│  │  • Amber bridge edges                    │                   │
│  │  • Live HUD: tick, R₀, tokens, %         │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1: Graph Engine (Member 1 — Manaswi)

**Barabási–Albert Preferential Attachment**
- Start with 6 seed nodes in a small ring
- Each new node attaches to m=2 existing nodes
- P(attach to j) = k_j / Σk (preferential attachment)
- 72% probability same-cluster attachment → echo chambers
- Result: power-law degree distribution P(k) ~ k⁻³

**Louvain Community Detection**
- Maximises modularity Q = (1/2m) Σ[A_ij - k_i·k_j/2m]·δ(c_i,c_j)
- Achieves Q ≈ 0.52 on generated graphs
- Used to colour nodes and identify bridge edges

**Betweenness Centrality (Brandes' Algorithm)**
- C_B(v) = Σ σ(s,t|v) / σ(s,t)
- Identifies bridge nodes between clusters
- O(VE) time complexity

**Force-Directed Layout (Modified Fruchterman–Reingold)**
- 140 iterations with cooling schedule
- Added cluster-pull term: f_pull(v) = α·(centroid_cluster - x_v)
- Visually separates echo chambers without fixing node positions

### Layer 2: Epidemic Model (Member 2)

| Transition | Rule |
|-----------|------|
| S → E | P = β × (2.6 if hub) per infected neighbour per tick |
| E → I | After 2 ticks in E state |
| I → R | P = γ = 0.18 per tick |
| R → I | P = δ = 0.09 per tick (post tick-10 mutation only) |
| Any → V | Player vaccination (permanent, absorbing state) |

Basic R₀ = β·⟨k⟩/γ ≈ 6.3 (without intervention)

### Layer 3: Rendering (Member 3)

- **HTML5 Canvas** — no external libraries
- Pulse-ring animations on infected nodes
- Radial gradient glow on infected hub nodes
- Amber dashed lines for cross-cluster bridge edges
- Responsive: desktop (side-panel) and mobile (stacked) layouts

---

## ⚙️ Model Parameters

| Parameter | Value | Justification |
|-----------|-------|---------------|
| N (nodes) | 120 | Large enough for community structure, fast enough for browser |
| K (clusters) | 4 | Matches typical social media community segmentation |
| m (attachment) | 2 | Standard BA parameter; produces sparse scale-free graph |
| β (transmission) | 0.30 | Calibrated to produce R₀ ≈ 6.3, consistent with viral misinformation |
| γ (recovery) | 0.18 | ~5 ticks to recover; models debunking half-life |
| δ (relapse) | 0.09 | Post-mutation relapse; models story mutation |
| Hub amplifier | 2.6× | Simulates algorithmic amplification |
| Tokens T | 5 | Balanced to make game challenging; prevents trivial wins |
| Ticks | 20 | Long enough for meaningful spread; short enough for one sitting |
| Win threshold | 50% | Majority-belief threshold |
| Mutation tick | 10 | Mid-game; forces players to reserve tokens |

---

## 🧪 Software Environment

### Browser (Main Game)
- **Language:** JavaScript (ES6+), HTML5, CSS3
- **Dependencies:** None (zero external libraries)
- **Fonts:** Google Fonts (JetBrains Mono, Inter) — loaded from CDN
- **Tested on:** Chrome 124+, Firefox 125+, Safari 17+, Edge 124+
- **Mobile:** iOS Safari 17+, Android Chrome 124+

### Python (Batch Simulation & Plotting)
- **Python:** 3.9+
- **Packages:** See `scripts/requirements.txt`
  - `numpy` — numerical simulation
  - `networkx` — graph construction and centrality
  - `matplotlib` — figure generation
  - `pandas` — results aggregation

---

## 📚 References and Acknowledgments

### Academic References

1. A.-L. Barabási and R. Albert, "Emergence of scaling in random networks," *Science*, vol. 286, no. 5439, pp. 509–512, 1999.
2. V. D. Blondel et al., "Fast unfolding of communities in large networks," *J. Stat. Mech.*, P10008, 2008.
3. U. Brandes, "A faster algorithm for betweenness centrality," *Journal of Mathematical Sociology*, vol. 25, no. 2, pp. 163–177, 2001.
4. T. M. J. Fruchterman and E. M. Reingold, "Graph drawing by force-directed placement," *Software: Practice and Experience*, vol. 21, no. 11, 1991.
5. W. O. Kermack and A. G. McKendrick, "A contribution to the mathematical theory of epidemics," *Proc. Royal Soc. A*, 1927.
6. S. Vosoughi, D. Roy, and S. Aral, "The spread of true and false news online," *Science*, vol. 359, no. 6380, 2018.
7. M. E. J. Newman, "The structure and function of complex networks," *SIAM Review*, vol. 45, no. 2, 2003.

### AI Assistance Acknowledgment

This project used Claude (Anthropic) as a coding assistant for:
- Generating boilerplate HTML/CSS/JS structure
- Debugging force-directed layout algorithm
- Generating the LaTeX report template
- Generating the poster PDF (ReportLab)
- Generating the PowerPoint slide deck (pptxgenjs)

All generated code was reviewed, tested, modified, and understood by the group members before submission. The core algorithmic implementations (BA graph generation, Louvain, Brandes' betweenness, SEIR transitions) were designed, verified, and debugged by the students. The use of AI assistance is acknowledged in accordance with course guidelines.

### Open Source Libraries

- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) — open-source monospace font (Apache 2.0)
- [Inter](https://rsms.me/inter/) — open-source UI font (OFL 1.1)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Live Demo:** [Open FakeNewsFirewall.html](src/FakeNewsFirewall.html)
- **Individual Report:** [docs/FakeNewsFirewall_Report_Manaswi.pdf](docs/FakeNewsFirewall_Report_Manaswi.pdf)
- **Course:** Computer Networks, NCCU, Spring 2026
