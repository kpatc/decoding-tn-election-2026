"""
Step 2 — KPI Calculation (Arc A: Q1 + Q2 + Q6)
"""

import pandas as pd
import numpy as np
from pathlib import Path

KPI_DIR = Path(__file__).parent / "outputs" / "kpis"
KPI_DIR.mkdir(parents=True, exist_ok=True)


REGIONS = ["Chennai Metro", "North", "Central", "Kongu", "Delta", "South"]
TOP_PARTIES = ["TVK", "DMK", "AIADMK", "INC", "PMK", "VCK", "BJP", "CPI", "CPI(M)"]


# ─────────────────────────────────────────────────────────
# KPI 1 — SIÈGES PAR PARTI
# ─────────────────────────────────────────────────────────

def seats_by_party(w21: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    s21 = w21["winner_party"].value_counts().rename("seats_2021")
    s26 = w26["winner_party"].value_counts().rename("seats_2026")
    df  = pd.concat([s21, s26], axis=1).fillna(0).astype(int)
    df["delta"] = df["seats_2026"] - df["seats_2021"]
    df = df.sort_values("seats_2026", ascending=False)
    return df


# ─────────────────────────────────────────────────────────
# KPI 2 — VOTE SHARE ÉTAT ENTIER
# ─────────────────────────────────────────────────────────

def vote_share_state(r21: pd.DataFrame, r26: pd.DataFrame) -> pd.DataFrame:
    def _share(df):
        total = df["votes"].sum()
        return (df.groupby("party")["votes"].sum() / total * 100).round(2)

    vs21 = _share(r21).rename("vote_share_2021")
    vs26 = _share(r26).rename("vote_share_2026")
    df   = pd.concat([vs21, vs26], axis=1).fillna(0)
    df["delta_pts"] = (df["vote_share_2026"] - df["vote_share_2021"]).round(2)
    df = df.sort_values("vote_share_2026", ascending=False)
    return df


# ─────────────────────────────────────────────────────────
# KPI 3 — FLIPS : table de transition
# ─────────────────────────────────────────────────────────

def build_flip_table(w21: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    merged = w21[["ac_number", "constituency", "region", "reserved",
                  "winner_party", "winner_share", "margin_pct"]].merge(
        w26[["ac_number", "winner_party", "winner_share", "margin_pct",
             "total_votes", "num_candidates"]],
        on="ac_number",
        suffixes=("_2021", "_2026")
    )
    merged["flipped"]      = merged["winner_party_2021"] != merged["winner_party_2026"]
    merged["share_delta"]  = (merged["winner_share_2026"] - merged["winner_share_2021"]).round(2)
    merged["margin_delta"] = (merged["margin_pct_2026"]   - merged["margin_pct_2021"]).round(2)
    return merged


def flip_matrix(flip_table: pd.DataFrame) -> pd.DataFrame:
    """Matrice de transition : lignes = gagnant 2021, colonnes = gagnant 2026."""
    flipped_only = flip_table[flip_table["flipped"]]
    matrix = pd.crosstab(
        flipped_only["winner_party_2021"],
        flipped_only["winner_party_2026"]
    )
    return matrix


def flip_summary(flip_table: pd.DataFrame) -> dict:
    total   = len(flip_table)
    n_flips = flip_table["flipped"].sum()
    return {
        "total_acs":   total,
        "flipped":     int(n_flips),
        "stable":      int(total - n_flips),
        "flip_rate":   round(n_flips / total * 100, 1),
    }


def flips_by_region(flip_table: pd.DataFrame) -> pd.DataFrame:
    g = flip_table.groupby("region").agg(
        total   = ("flipped", "count"),
        flipped = ("flipped", "sum"),
    )
    g["stable"]    = g["total"] - g["flipped"]
    g["flip_rate"] = (g["flipped"] / g["total"] * 100).round(1)
    return g.loc[REGIONS]


def flips_toward_tvk(flip_table: pd.DataFrame) -> pd.DataFrame:
    """D'où viennent les 108 sièges TVK ?"""
    tvk = flip_table[
        (flip_table["winner_party_2026"] == "TVK") &
        (flip_table["flipped"])
    ]
    return tvk["winner_party_2021"].value_counts().rename("seats_taken_by_tvk")


# ─────────────────────────────────────────────────────────
# KPI 4 — GÉOGRAPHIE : sièges par région × parti
# ─────────────────────────────────────────────────────────

def seats_by_region_party(w21: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    """Table longue : region, party, seats_2021, seats_2026, delta."""
    s21 = (
        w21.groupby(["region", "winner_party"])
        .size()
        .reset_index(name="seats_2021")
    )
    s26 = (
        w26.groupby(["region", "winner_party"])
        .size()
        .reset_index(name="seats_2026")
    )
    df = s21.merge(s26, on=["region", "winner_party"], how="outer").fillna(0)
    df[["seats_2021", "seats_2026"]] = df[["seats_2021", "seats_2026"]].astype(int)
    df["delta"] = df["seats_2026"] - df["seats_2021"]
    df = df.sort_values(["region", "seats_2026"], ascending=[True, False])
    return df


def region_summary(w26: pd.DataFrame) -> pd.DataFrame:
    """Par région : total sièges, parti dominant, % du dominant."""
    g = w26.groupby("region").agg(
        total_seats    = ("ac_number", "count"),
        dominant_party = ("winner_party", lambda x: x.value_counts().index[0]),
        dominant_seats = ("winner_party", lambda x: x.value_counts().iloc[0]),
    )
    g["dominant_pct"] = (g["dominant_seats"] / g["total_seats"] * 100).round(1)
    return g.loc[REGIONS]


# ─────────────────────────────────────────────────────────
# KPI 5 — MARGES DE VICTOIRE (Q6)
# ─────────────────────────────────────────────────────────

def margin_global(w21: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    """Stats globales marges 2021 vs 2026."""
    def _stats(series, year):
        return pd.Series({
            "year":    year,
            "mean":    round(series.mean(), 2),
            "median":  round(series.median(), 2),
            "min":     round(series.min(), 2),
            "max":     round(series.max(), 2),
            "gt_50":   int((series > 50).sum()),
            "lt_35":   int((series < 35).sum()),
        })

    s21 = _stats(w21["winner_share"], 2021)
    s26 = _stats(w26["winner_share"], 2026)
    return pd.DataFrame([s21, s26]).set_index("year")


def margin_by_region(w26: pd.DataFrame) -> pd.DataFrame:
    g = w26.groupby("region").agg(
        mean_share   = ("winner_share", "mean"),
        median_share = ("winner_share", "median"),
        mean_margin  = ("margin_pct",   "mean"),
        lt35         = ("winner_share", lambda x: (x < 35).sum()),
        gt50         = ("winner_share", lambda x: (x > 50).sum()),
        total        = ("ac_number",    "count"),
    ).round(2)
    g["pct_lt35"] = (g["lt35"] / g["total"] * 100).round(1)
    g["pct_gt50"] = (g["gt50"] / g["total"] * 100).round(1)
    return g.loc[REGIONS]


def margin_by_party(w26: pd.DataFrame) -> pd.DataFrame:
    g = w26.groupby("winner_party").agg(
        seats        = ("ac_number",    "count"),
        mean_share   = ("winner_share", "mean"),
        mean_margin  = ("margin_pct",   "mean"),
    ).round(2)
    return g.sort_values("seats", ascending=False)


def tight_races(w26: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Sièges avec marge < threshold %."""
    return (
        w26[w26["margin_pct"] < threshold]
        [["constituency", "region", "reserved", "winner_party",
          "winner_share", "margin_pct", "total_votes"]]
        .sort_values("margin_pct")
        .reset_index(drop=True)
    )


def landslides(w26: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Top N victoires les plus larges."""
    return (
        w26.nlargest(top_n, "margin_pct")
        [["constituency", "region", "winner_party", "winner_share", "margin_pct"]]
        .reset_index(drop=True)
    )


def margin_distribution_comparison(w21: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    """Distribution winner_share en tranches de 5%."""
    bins = np.arange(25, 75, 5)
    labels = [f"{b}-{b+5}%" for b in bins[:-1]]

    def _dist(series, year):
        cut = pd.cut(series, bins=bins, labels=labels, right=False)
        return cut.value_counts().sort_index().rename(year)

    d21 = _dist(w21["winner_share"], 2021)
    d26 = _dist(w26["winner_share"], 2026)
    return pd.concat([d21, d26], axis=1)


# ─────────────────────────────────────────────────────────
# KPI 6 — BASTIONS (sièges stables)
# ─────────────────────────────────────────────────────────

def bastion_table(flip_table: pd.DataFrame, w26: pd.DataFrame) -> pd.DataFrame:
    stable = flip_table[~flip_table["flipped"]][["ac_number", "winner_party_2021", "region"]].copy()
    stable.columns = ["ac_number", "party", "region"]

    seats26 = w26["winner_party"].value_counts().rename("seats_2026")
    stable_count = stable["party"].value_counts().rename("stable")

    df = pd.concat([seats26, stable_count], axis=1).fillna(0).astype(int)
    df["retention_pct"] = (df["stable"] / df["seats_2026"] * 100).round(1)
    df = df[df["seats_2026"] > 0].sort_values("retention_pct", ascending=False)
    return df


# ─────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────

def run(tables: dict) -> dict:
    w21, w26 = tables["w21"], tables["w26"]
    r21, r26 = tables["r21"], tables["r26"]

    flip_table = build_flip_table(w21, w26)

    kpis = {
        "seats_by_party":      seats_by_party(w21, w26),
        "vote_share_state":    vote_share_state(r21, r26),
        "flip_table":          flip_table,
        "flip_matrix":         flip_matrix(flip_table),
        "flip_summary":        flip_summary(flip_table),
        "flips_by_region":     flips_by_region(flip_table),
        "flips_toward_tvk":    flips_toward_tvk(flip_table),
        "seats_by_region":     seats_by_region_party(w21, w26),
        "region_summary":      region_summary(w26),
        "margin_global":       margin_global(w21, w26),
        "margin_by_region":    margin_by_region(w26),
        "margin_by_party":     margin_by_party(w26),
        "tight_races":         tight_races(w26),
        "landslides":          landslides(w26),
        "margin_distribution": margin_distribution_comparison(w21, w26),
        "bastions":            bastion_table(flip_table, w26),
    }

    return kpis


def print_all(kpis: dict) -> None:
    sep = "═" * 60

    print(f"\n{sep}\nKPI 1 — SIÈGES PAR PARTI\n{sep}")
    print(kpis["seats_by_party"].to_string())

    print(f"\n{sep}\nKPI 2 — VOTE SHARE ÉTAT ENTIER\n{sep}")
    top = kpis["vote_share_state"].head(10)
    print(top.to_string())

    print(f"\n{sep}\nKPI 3 — FLIPS\n{sep}")
    s = kpis["flip_summary"]
    print(f"Flips : {s['flipped']}/{s['total_acs']} ({s['flip_rate']}%)")
    print(f"Stables : {s['stable']}")
    print("\nMatrice de transition :")
    print(kpis["flip_matrix"].to_string())
    print("\nOrigine des 108 sièges TVK :")
    print(kpis["flips_toward_tvk"].to_string())

    print(f"\n{sep}\nKPI 4 — FLIPS PAR RÉGION\n{sep}")
    print(kpis["flips_by_region"].to_string())

    print(f"\n{sep}\nKPI 5 — MARGES GLOBALES\n{sep}")
    print(kpis["margin_global"].to_string())

    print(f"\n{sep}\nKPI 6 — MARGES PAR RÉGION\n{sep}")
    print(kpis["margin_by_region"].to_string())

    print(f"\n{sep}\nKPI 7 — MARGES PAR PARTI\n{sep}")
    print(kpis["margin_by_party"].head(8).to_string())

    print(f"\n{sep}\nKPI 8 — SIÈGES SERRÉS (marge < 0.5%)\n{sep}")
    print(kpis["tight_races"].to_string(index=False))

    print(f"\n{sep}\nKPI 9 — BASTIONS\n{sep}")
    print(kpis["bastions"].to_string())

    print(f"\n{sep}\nKPI 10 — DISTRIBUTION WINNER SHARE\n{sep}")
    print(kpis["margin_distribution"].to_string())


# ─────────────────────────────────────────────────────────
# EXPORT — Save all KPI tables as CSV

# ─────────────────────────────────────────────────────────

def export_kpis(kpis: dict, tables: dict) -> None:
    """Export every KPI table + winners tables to src/outputs/kpis/."""

    def _save(df: pd.DataFrame, name: str):
        path = KPI_DIR / f"{name}.csv"
        df.to_csv(path)
        print(f"  [saved] {path.name}  ({len(df)} rows)")

    print("\n" + "═" * 55)
    print("  EXPORTING KPI DATASETS")
    print("═" * 55)

    # ── Winners tables (base analytique) ──────────────────
    _save(tables["w21"].sort_values("ac_number"), "winners_2021")
    _save(tables["w26"].sort_values("ac_number"), "winners_2026")

    # ── Q2 : Flips ─────────────────────────────────────────
    _save(kpis["flip_table"].sort_values("ac_number"),  "flip_table")
    _save(kpis["flip_matrix"],                          "flip_matrix")
    _save(kpis["flips_by_region"],                      "flips_by_region")

    flip_tvk = kpis["flips_toward_tvk"].reset_index()
    flip_tvk.columns = ["party_held_2021", "seats_flipped_to_tvk"]
    _save(flip_tvk, "flips_toward_tvk")

    # ── Q1 : Geography ─────────────────────────────────────
    _save(kpis["seats_by_party"],   "seats_by_party")
    _save(kpis["seats_by_region"],  "seats_by_region")
    _save(kpis["region_summary"],   "region_summary")

    # ── Q6 : Margins ───────────────────────────────────────
    _save(kpis["margin_global"],        "margin_global")
    _save(kpis["margin_by_region"],     "margin_by_region")
    _save(kpis["margin_by_party"],      "margin_by_party")
    _save(kpis["tight_races"],          "tight_races")
    _save(kpis["landslides"],           "landslides")
    _save(kpis["margin_distribution"],  "margin_distribution")

    # ── Summary scorecard (1 row per key metric) ───────────
    mg  = kpis["margin_global"]
    fs  = kpis["flip_summary"]
    tot21 = tables["r21"]["votes"].astype(int).sum()
    tot26 = tables["r26"]["votes"].astype(int).sum()

    scorecard = pd.DataFrame([
        {"metric": "total_constituencies",          "value_2021": 234,   "value_2026": 234},
        {"metric": "total_valid_votes",             "value_2021": int(tot21), "value_2026": int(tot26)},
        {"metric": "seats_flipped",                 "value_2021": None,  "value_2026": fs["flipped"]},
        {"metric": "flip_rate_pct",                 "value_2021": None,  "value_2026": fs["flip_rate"]},
        {"metric": "seats_won_over_50pct",          "value_2021": int(mg.loc[2021, "gt_50"]),
                                                     "value_2026": int(mg.loc[2026, "gt_50"])},
        {"metric": "seats_won_under_35pct",         "value_2021": int(mg.loc[2021, "lt_35"]),
                                                     "value_2026": int(mg.loc[2026, "lt_35"])},
        {"metric": "avg_winner_share_pct",          "value_2021": mg.loc[2021, "mean"],
                                                     "value_2026": mg.loc[2026, "mean"]},
        {"metric": "median_winner_share_pct",       "value_2021": mg.loc[2021, "median"],
                                                     "value_2026": mg.loc[2026, "median"]},
        {"metric": "tvk_seats",                     "value_2021": 0,     "value_2026": 108},
        {"metric": "dmk_seats",                     "value_2021": 133,   "value_2026": 59},
        {"metric": "aiadmk_seats",                  "value_2021": 66,    "value_2026": 47},
        {"metric": "tight_races_under_0p5pct_margin","value_2021": None, "value_2026": len(kpis["tight_races"])},
    ])
    _save(scorecard.set_index("metric"), "scorecard_summary")

    print(f"\n[OK] {len(list(KPI_DIR.glob('*.csv')))} CSV files saved to: {KPI_DIR}")


if __name__ == "__main__":
    from load_clean import run as load_run
    tables = load_run()
    kpis   = run(tables)
    print_all(kpis)
