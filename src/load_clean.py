"""
Étape 1 — Chargement et nettoyage des données
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "input_files_for_participants_rpc" / "data"


def load_raw() -> dict[str, pd.DataFrame]:
    """Charge les 3 CSV bruts."""
    r21    = pd.read_csv(DATA_DIR / "tn_2021_results.csv",    dtype=str)
    r26    = pd.read_csv(DATA_DIR / "tn_2026_results.csv",    dtype=str)
    master = pd.read_csv(DATA_DIR / "constituency_master.csv", dtype=str)
    return {"r21": r21, "r26": r26, "master": master}


def audit(df: pd.DataFrame, name: str) -> None:
    """Rapport de qualité rapide."""
    print(f"\n{'─'*50}")
    print(f"  AUDIT : {name}  ({df.shape[0]} lignes × {df.shape[1]} cols)")
    print(f"{'─'*50}")
    print(df.dtypes.to_string())
    print("\nValeurs nulles :")
    print(df.isnull().sum().to_string())
    print(f"\nDoublons : {df.duplicated().sum()}")
    if "ac_number" in df.columns:
        print(f"ACs uniques : {df['ac_number'].nunique()}")
    if "party" in df.columns:
        print(f"Partis uniques : {df['party'].nunique()}")


def clean_results(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Nettoie un fichier résultats (2021 ou 2026)."""

    df = df.copy()

    # ── Typage ──────────────────────────────────────────────
    df["ac_number"] = pd.to_numeric(df["ac_number"], errors="coerce").astype("Int64")
    df["votes"]     = pd.to_numeric(df["votes"],     errors="coerce").astype("Int64")

    if "turnout" in df.columns:
        df["turnout"] = pd.to_numeric(df["turnout"], errors="coerce")

    # ── Nettoyage texte ──────────────────────────────────────
    for col in ["constituency", "candidate", "party", "reserved", "region"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # ── Suppression lignes sans votes ni AC ─────────────────
    before = len(df)
    df = df.dropna(subset=["ac_number", "votes"])
    dropped = before - len(df)
    if dropped:
        print(f"[{year}] {dropped} lignes supprimées (ac_number ou votes null)")

    # ── Votes négatifs ou zéro ───────────────────────────────
    neg = (df["votes"] <= 0).sum()
    if neg:
        print(f"[{year}] {neg} lignes avec votes ≤ 0 → supprimées")
        df = df[df["votes"] > 0]

    # ── Validation plage ac_number (1-234) ───────────────────
    out_of_range = ~df["ac_number"].between(1, 234)
    if out_of_range.sum():
        print(f"[{year}] ac_number hors [1-234] : {df.loc[out_of_range, 'ac_number'].unique()}")

    # ── Colonne année ────────────────────────────────────────
    df["year"] = year

    return df.reset_index(drop=True)


def clean_master(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ac_number"] = pd.to_numeric(df["ac_number"], errors="coerce").astype("Int64")
    for col in ["constituency", "district", "region", "reserved"]:
        df[col] = df[col].str.strip()
    return df.reset_index(drop=True)


def build_winners(df: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la table winners : 1 ligne par AC.
    - winner_party, winner_votes, total_votes, winner_share
    - margin_votes, margin_pct, num_candidates
    """
    # Total votes par AC
    ac_total = df.groupby("ac_number")["votes"].sum().rename("total_votes")

    # Gagnant = max votes par AC
    idx_winner = df.groupby("ac_number")["votes"].idxmax()
    winners = df.loc[idx_winner, ["ac_number", "party", "votes", "year"]].copy()
    winners.columns = ["ac_number", "winner_party", "winner_votes", "year"]

    # Runner-up
    def runner_up_votes(group):
        s = group.nlargest(2)
        return s.iloc[1] if len(s) > 1 else 0

    runner = (
        df.groupby("ac_number")["votes"]
        .apply(runner_up_votes)
        .rename("runner_votes")
    )

    # Nombre de candidats
    num_cands = df.groupby("ac_number")["candidate"].count().rename("num_candidates")

    # Assemblage
    winners = (
        winners
        .join(ac_total,    on="ac_number")
        .join(runner,      on="ac_number")
        .join(num_cands,   on="ac_number")
    )

    winners["winner_share"] = (winners["winner_votes"] / winners["total_votes"] * 100).round(2)
    winners["margin_votes"] = winners["winner_votes"] - winners["runner_votes"]
    winners["margin_pct"]   = (winners["margin_votes"]  / winners["total_votes"] * 100).round(2)

    # Joindre infos master
    winners = winners.merge(
        master[["ac_number", "constituency", "district", "region", "reserved"]],
        on="ac_number",
        how="left"
    )

    # Turnout 2021 (colonne unique par AC)
    if "turnout" in df.columns:
        turnout = (
            df.dropna(subset=["turnout"])
            .groupby("ac_number")["turnout"]
            .first()
            .rename("turnout")
        )
        winners = winners.join(turnout, on="ac_number")

    return winners.reset_index(drop=True)


def run() -> dict[str, pd.DataFrame]:
    """Point d'entrée principal — retourne toutes les tables propres."""

    raw = load_raw()

    print("\n" + "═"*50)
    print("  AUDIT DONNÉES BRUTES")
    print("═"*50)
    for name, df in raw.items():
        audit(df, name)

    print("\n" + "═"*50)
    print("  NETTOYAGE")
    print("═"*50)

    r21    = clean_results(raw["r21"],  2021)
    r26    = clean_results(raw["r26"],  2026)
    master = clean_master(raw["master"])

    print(f"\n[OK] 2021 : {len(r21)} lignes propres — {r21['ac_number'].nunique()} ACs")
    print(f"[OK] 2026 : {len(r26)} lignes propres — {r26['ac_number'].nunique()} ACs")
    print(f"[OK] Master : {len(master)} ACs")

    # Vérification couverture
    ac_21 = set(r21["ac_number"].dropna().astype(int))
    ac_26 = set(r26["ac_number"].dropna().astype(int))
    missing = ac_21.symmetric_difference(ac_26)
    if missing:
        print(f"[WARN] ACs présents dans un seul fichier : {missing}")
    else:
        print(f"[OK] Les 234 ACs présents dans les deux années")

    # Construction des tables winners
    w21 = build_winners(r21, master)
    w26 = build_winners(r26, master)

    print(f"\n[OK] Table winners 2021 : {len(w21)} ACs")
    print(f"[OK] Table winners 2026 : {len(w26)} ACs")

    return {
        "r21": r21, "r26": r26,
        "master": master,
        "w21": w21, "w26": w26,
    }


if __name__ == "__main__":
    tables = run()
    print("\n\nAperçu winners 2026 :")
    print(tables["w26"].head(5).to_string(index=False))
