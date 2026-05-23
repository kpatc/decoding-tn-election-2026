"""
Pipeline principal — AtliQ Media : Decoding the 2026 Tamil Nadu Election
Arc A : Q1 (géographie) + Q2 (flips) + Q6 (marges)

Usage :
    cd "AtliQ Challenge"
    python3 src/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from load_clean    import run as step1
from kpis          import run as step2, print_all, export_kpis
from visualisations import run as step3


def main():
    print("\n" + "█"*60)
    print("  ATLIQ MEDIA — TN ELECTION 2026 : ANALYSIS PIPELINE")
    print("█"*60)

    # Step 1 — Load & clean
    print("\n[STEP 1] Loading and cleaning data...")
    tables = step1()

    # Step 2 — KPI calculation
    print("\n[STEP 2] Computing KPIs...")
    kpis = step2(tables)
    print_all(kpis)

    # Step 2b — Export KPI datasets
    print("\n[STEP 2b] Exporting KPI datasets...")
    export_kpis(kpis, tables)

    # Step 3 — Charts
    print("\n[STEP 3] Generating charts...")
    step3(tables, kpis)

    print("\n" + "█"*60)
    print("  PIPELINE COMPLETE")
    print("  Charts  → src/outputs/charts/")
    print("  KPIs    → src/outputs/kpis/")
    print("█"*60)


if __name__ == "__main__":
    main()
