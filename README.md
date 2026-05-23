# Decoding the 2026 Tamil Nadu Assembly Election

**Codebasics Resume Project Challenge #21 — AtliQ Media**

> *163 out of 234 constituencies changed their winning party in 2026. A party that did not exist in 2021 won 108 seats. Victory margins shrank to their lowest recorded level. This is the data story of how Tamil Nadu's electoral map was redrawn.*

---

## Table of Contents

- [Challenge Brief](#challenge-brief)
- [Key Findings](#key-findings)
- [Project Structure](#project-structure)
- [Data Sources](#data-sources)
- [Reproduce This Analysis](#reproduce-this-analysis)
- [Deliverables](#deliverables)
- [Data Limitations](#data-limitations)
- [Disclaimer](#disclaimer)

---

## Challenge Brief

AtliQ Media is producing a one-hour TV show on the 2026 Tamil Nadu Legislative Assembly election results. The brief: find the most compelling data stories, build clear charts for each, and pitch them to the editorial team — using only publicly available Election Commission of India (ECI) data, with strict political neutrality.

**Analytical arc chosen — Arc A (Q1 + Q2 + Q6):**

| Story | Question |
|---|---|
| **Where** did the map change? | Q1 — Geographic seat distribution shift across 6 regions |
| **What** changed? | Q2 — Seat flip analysis: which parties gained and lost, and where |
| **How** competitive was it? | Q6 — Victory margins and electoral fragmentation |

---

## Key Findings

| Metric | 2021 | 2026 |
|---|---|---|
| Constituencies that changed winner | — | **163 / 234 (69.7%)** |
| TVK seats | 0 *(party did not exist)* | **108** |
| DMK seats | 133 | **59** (−74) |
| AIADMK seats | 66 | **47** (−19) |
| Seats won with > 50% vote share | 70 | **13** |
| Seats won with < 35% vote share | 2 | **64** |
| Average winner vote share | 48.4% | **38.8%** (−9.6 pts) |
| Average victory margin | 11.7% | **7.7%** (−4.0 pts) |

**Regional highlights:**
- Chennai Metro recorded the highest flip rate: **93.8%** (30/32 seats changed winner)
- Delta was the most stable region: **45.5%** flip rate — DMK held 14/33 seats
- Kongu saw AIADMK's sharpest decline: 19 → 7 seats (−12)
- North and Central were the only regions where AIADMK held ground (15 seats each)
- South had the highest electoral fragmentation: 43% of seats won with less than 35% of the vote

---

## Project Structure

```
AtliQ-Challenge/
│
├── README.md
├── requirements.txt
│
├── input_files_for_participants_rpc/
│   ├── data/
│   │   ├── tn_2021_results.csv          # Candidate-level results, 2021 (4,232 rows)
│   │   ├── tn_2026_results.csv          # Candidate-level results, 2026 (4,257 rows)
│   │   └── constituency_master.csv      # AC reference table (234 rows)
│   └── metadata.txt                     # Column descriptions
│
└── src/
    ├── pipeline.py          # Main entry point — runs all 3 steps
    ├── load_clean.py        # Step 1: data loading, audit, cleaning, winners table
    ├── kpis.py              # Step 2: all KPI calculations (pandas/numpy)
    ├── visualisations.py    # Step 3: static charts (matplotlib/seaborn)
    ├── dashboard.py         # Interactive dashboard (Streamlit)
    │
    └── outputs/
        ├── charts/          # 9 PNG charts (high-res, 150 dpi)
        │   ├── V1_seats_by_party.png
        │   ├── V2_flip_matrix.png
        │   ├── V3_flip_rate_by_region.png
        │   ├── V4_seats_by_region.png
        │   ├── V5_winner_share_distribution.png
        │   ├── V6_fragmentation_by_region.png
        │   ├── V7_margin_scatter_by_party.png
        │   ├── V8_margin_evolution_by_region.png
        │   └── V9_tvk_source_seats.png
        │
        └── kpis/            # 18 CSV datasets
            ├── scorecard_summary.csv    # 12 headline KPIs
            ├── winners_2021.csv         # 1 row per constituency, 2021
            ├── winners_2026.csv         # 1 row per constituency, 2026
            ├── flip_table.csv           # Flip flag + margin delta per AC
            ├── flip_matrix.csv          # Seat transition matrix
            ├── flips_by_region.csv      # Flip count and rate by region
            ├── flips_toward_tvk.csv     # Origin of TVK's 108 seats
            ├── seats_by_party.csv       # Seats 2021 vs 2026 by party
            ├── seats_by_region.csv      # Seats by region × party
            ├── region_summary.csv       # Dominant party + stats per region
            ├── vote_share_state.csv     # State-wide vote share by party
            ├── margin_global.csv        # Global margin stats 2021 vs 2026
            ├── margin_by_region.csv     # Margin + fragmentation by region
            ├── margin_by_party.csv      # Margin stats by winning party
            ├── margin_distribution.csv  # Winner share distribution by band
            ├── tight_races.csv          # 14 seats won with margin < 0.5%
            ├── landslides.csv           # Top 10 widest victories
            └── bastions.csv            # Seat retention rate by party
```

---

## Data Sources

| File | Source | Notes |
|---|---|---|
| `tn_2021_results.csv` | [Trivedi Centre for Political Data](https://tcpd.ashoka.edu.in/) (via ECI) | Cleaned, candidate-level, all 234 ACs |
| `tn_2026_results.csv` | [ECI Live Results Portal](https://results.eci.gov.in/ResultAcGenMay2026) | Live data — Form-20 final audit not yet released |
| `constituency_master.csv` | ECI constituency master list | Reference table for AC → district/region/reserved |

**Primary join key:** `ac_number` (1–234). Constituency names are **not** used for joins — spelling varies between files.

**Supplementary references (not used in computation):**
- [ECI Statistical Reports](https://eci.gov.in/statistical-reports) — historical PDF reports
- [Chief Electoral Officer, Tamil Nadu](https://elections.tn.gov.in) — state-level data

---

## Reproduce This Analysis

### Prerequisites

Python 3.10 or higher.

### 1. Clone the repository

```bash
git clone https://github.com/kpatc/atliq-tn-election-2026.git
cd atliq-tn-election-2026
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the full pipeline

Generates all KPI datasets (18 CSV files) and static charts (9 PNG files):

```bash
python3 src/pipeline.py
```

**Output:**
- `src/outputs/charts/` — 9 high-resolution charts
- `src/outputs/kpis/` — 18 CSV datasets

### 4. Launch the interactive dashboard

```bash
streamlit run src/dashboard.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

The dashboard renders the exact same matplotlib/seaborn charts as the static pipeline. The sidebar filters (Region, Constituency Type) recompute all KPIs and regenerate all charts in real time.

### 5. Run individual steps

Each module can also be run independently:

```bash
python3 src/load_clean.py    # Step 1: audit + clean data
python3 src/kpis.py          # Step 2: compute and print all KPIs
python3 src/visualisations.py  # Step 3: generate and save charts
```

---

## Deliverables

| Deliverable | Location |
|---|---|
| Video walkthrough (5–7 min) | [YouTube link] |
| Stakeholder deck (8–10 slides) | [Google Slides / PDF link] |
| Interactive dashboard | `src/dashboard.py` — `streamlit run src/dashboard.py` |
| Analysis pipeline | `src/pipeline.py` |
| KPI datasets | `src/outputs/kpis/` |
| Static charts | `src/outputs/charts/` |

---

## Data Limitations

| Limitation | Impact on Analysis |
|---|---|
| 2026 Form-20 (final audited data) not yet released | Vote totals may shift marginally from the ECI live portal figures used here |
| `turnout` column is blank for all 2026 rows | Constituency-level turnout comparison (Q5) is not possible from this dataset alone |
| No polling-station-level data | Cannot identify within-constituency geographic patterns |
| No linked demographic data | All analysis is electoral — no claims about voter characteristics are made or implied |
| Co-movements ≠ causality | Patterns such as "TVK rose while AIADMK fell" are descriptive. No causal claims are made. |

---

## Disclaimer

This project is a non-partisan data analysis exercise based exclusively on publicly available Election Commission of India data. It does not endorse, criticise, or take any political position on any party, leader, alliance, community, religion, or region. Every chart title and data point is intended to read the same way to supporters of any party.

Produced as part of **Codebasics Resume Project Challenge #21**.

---

*Built with Python · pandas · numpy · matplotlib · seaborn · Streamlit*
