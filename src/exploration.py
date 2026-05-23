"""
AtliQ Media — Decoding the 2026 Tamil Nadu Assembly Election
Arc A : Q1 (géographie) + Q2 (flips) + Q6 (marges)
"""

import csv
from collections import defaultdict, Counter

# ─────────────────────────────────────────────
# 0. CHARGEMENT DES DONNÉES
# ─────────────────────────────────────────────

DATA = "input_files_for_participants_rpc/data/"

def load_csv(filename):
    with open(DATA + filename, encoding="utf-8") as f:
        return list(csv.DictReader(f))

r21    = load_csv("tn_2021_results.csv")
r26    = load_csv("tn_2026_results.csv")
master = load_csv("constituency_master.csv")

# Table de référence : ac_number → {district, region, reserved, constituency}
master_map = {r["ac_number"]: r for r in master}

print(f"2021 : {len(r21)} lignes | {len(set(r['ac_number'] for r in r21))} ACs")
print(f"2026 : {len(r26)} lignes | {len(set(r['ac_number'] for r in r26))} ACs")
print(f"Master : {len(master)} ACs\n")


# ─────────────────────────────────────────────
# 1. TABLE WINNERS — 1 ligne par AC par année
# ─────────────────────────────────────────────

def build_winners(rows):
    """Pour chaque AC, calcule le gagnant, total votes, winner share, marge."""
    by_ac = defaultdict(list)
    for r in rows:
        try:
            by_ac[r["ac_number"]].append({
                "party":  r["party"],
                "votes":  int(r["votes"]),
            })
        except ValueError:
            pass

    winners = {}
    for ac, candidates in by_ac.items():
        candidates.sort(key=lambda x: x["votes"], reverse=True)
        total      = sum(c["votes"] for c in candidates)
        w1         = candidates[0]
        w2_votes   = candidates[1]["votes"] if len(candidates) > 1 else 0
        margin     = w1["votes"] - w2_votes
        m          = master_map.get(ac, {})

        winners[ac] = {
            "ac_number":      ac,
            "constituency":   m.get("constituency", ""),
            "region":         m.get("region", ""),
            "district":       m.get("district", ""),
            "reserved":       m.get("reserved", ""),
            "winner_party":   w1["party"],
            "winner_votes":   w1["votes"],
            "total_votes":    total,
            "winner_share":   round(w1["votes"] / total * 100, 2),
            "margin_votes":   margin,
            "margin_pct":     round(margin / total * 100, 2),
            "num_candidates": len(candidates),
        }
    return winners

w21 = build_winners(r21)
w26 = build_winners(r26)

print("=" * 60)
print("KPI 1 — SIÈGES PAR PARTI (2021 vs 2026)")
print("=" * 60)

seats21 = Counter(w["winner_party"] for w in w21.values())
seats26 = Counter(w["winner_party"] for w in w26.values())

top_parties = ["TVK", "DMK", "AIADMK", "INC", "PMK", "VCK", "BJP", "CPI", "CPI(M)", "IUML"]
print(f"{'Parti':<12} {'2021':>6} {'2026':>6} {'Delta':>7}")
print("-" * 35)
for p in top_parties:
    s21 = seats21.get(p, 0)
    s26 = seats26.get(p, 0)
    d   = s26 - s21
    print(f"{p:<12} {s21:>6} {s26:>6} {('+' if d>0 else '')+str(d):>7}")

print(f"\nTotal 2021 : {sum(seats21.values())} | Total 2026 : {sum(seats26.values())}")


# ─────────────────────────────────────────────
# 2. TABLE FLIPS — matrice de transition
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 2 — FLIPS : MATRICE DE TRANSITION 2021 → 2026")
print("=" * 60)

flips = []
for ac in w21:
    if ac not in w26:
        continue
    p21      = w21[ac]["winner_party"]
    p26      = w26[ac]["winner_party"]
    flipped  = (p21 != p26)
    flips.append({
        "ac_number":    ac,
        "constituency": w26[ac]["constituency"],
        "region":       w21[ac]["region"],
        "reserved":     w21[ac]["reserved"],
        "winner_2021":  p21,
        "winner_2026":  p26,
        "flipped":      flipped,
    })

total_flips  = sum(1 for f in flips if f["flipped"])
total_stable = sum(1 for f in flips if not f["flipped"])

print(f"Flips   : {total_flips} / 234  ({total_flips/234*100:.1f}%)")
print(f"Stables : {total_stable} / 234  ({total_stable/234*100:.1f}%)")

# Matrice transition
matrix = defaultdict(Counter)
for f in flips:
    if f["flipped"]:
        matrix[f["winner_2021"]][f["winner_2026"]] += 1

cols = ["TVK", "DMK", "AIADMK", "INC", "PMK", "Autres"]
print(f"\n{'2021 → 2026':<12}" + "".join(f"{c:>8}" for c in cols))
print("-" * (12 + 8 * len(cols)))
for p21 in ["DMK", "AIADMK", "INC", "PMK", "VCK", "BJP"]:
    row    = matrix.get(p21, Counter())
    others = sum(v for k, v in row.items() if k not in ["TVK","DMK","AIADMK","INC","PMK"])
    if sum(row.values()) == 0:
        continue
    vals = [row.get(c, 0) for c in cols[:-1]] + [others]
    print(f"{p21:<12}" + "".join(f"{v:>8}" for v in vals))

# Détail flips vers TVK
tvk_flips = [f for f in flips if f["winner_2026"] == "TVK" and f["flipped"]]
print(f"\nFlips vers TVK : {len(tvk_flips)}")
for source in ["DMK", "AIADMK", "INC"]:
    n = sum(1 for f in tvk_flips if f["winner_2021"] == source)
    print(f"  depuis {source:<8} : {n}")
autres = sum(1 for f in tvk_flips if f["winner_2021"] not in ["DMK","AIADMK","INC"])
print(f"  depuis autres   : {autres}")


# ─────────────────────────────────────────────
# 3. GÉOGRAPHIE — sièges et taux de flip par région
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 3 — GÉOGRAPHIE : SIÈGES ET FLIPS PAR RÉGION")
print("=" * 60)

REGIONS = ["Chennai Metro", "North", "Central", "Kongu", "Delta", "South"]

region21 = defaultdict(Counter)
region26 = defaultdict(Counter)
for ac, w in w21.items():
    region21[w["region"]][w["winner_party"]] += 1
for ac, w in w26.items():
    region26[w["region"]][w["winner_party"]] += 1

for region in REGIONS:
    r21c = region21[region]
    r26c = region26[region]
    total = sum(r26c.values())
    print(f"\n{region} ({total} sièges)")
    print(f"  {'Parti':<10} {'2021':>5} {'2026':>5} {'Δ':>5}")
    print(f"  {'-'*28}")
    for p in ["TVK", "DMK", "AIADMK", "INC", "PMK"]:
        s21 = r21c.get(p, 0)
        s26 = r26c.get(p, 0)
        if s21 == 0 and s26 == 0:
            continue
        d = s26 - s21
        print(f"  {p:<10} {s21:>5} {s26:>5} {('+' if d>0 else '')+str(d):>5}")
    o21 = sum(v for k,v in r21c.items() if k not in ["TVK","DMK","AIADMK","INC","PMK"])
    o26 = sum(v for k,v in r26c.items() if k not in ["TVK","DMK","AIADMK","INC","PMK"])
    if o21 or o26:
        d = o26 - o21
        print(f"  {'Autres':<10} {o21:>5} {o26:>5} {('+' if d>0 else '')+str(d):>5}")

# Taux de flip par région
print(f"\n{'Région':<16} {'Flips':>7} {'Total':>7} {'%':>7}")
print("-" * 40)
flip_by_region = defaultdict(lambda: {"flip": 0, "total": 0})
for f in flips:
    flip_by_region[f["region"]]["total"] += 1
    if f["flipped"]:
        flip_by_region[f["region"]]["flip"] += 1
for region in REGIONS:
    d2 = flip_by_region[region]
    pct = d2["flip"] / d2["total"] * 100
    print(f"{region:<16} {d2['flip']:>7} {d2['total']:>7} {pct:>6.1f}%")


# ─────────────────────────────────────────────
# 4. MARGES DE VICTOIRE (Q6)
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 4 — MARGES DE VICTOIRE")
print("=" * 60)

shares21 = sorted(w["winner_share"] for w in w21.values())
shares26 = sorted(w["winner_share"] for w in w26.values())
margins26 = sorted(w["margin_pct"] for w in w26.values())
margins21 = sorted(w["margin_pct"] for w in w21.values())

def stats(vals, label):
    n = len(vals)
    print(f"{label}: moy={sum(vals)/n:.2f}%  médiane={vals[n//2]:.2f}%  min={vals[0]:.2f}%  max={vals[-1]:.2f}%")

stats(shares21, "Winner share 2021")
stats(shares26, "Winner share 2026")
stats(margins21, "Marge %      2021")
stats(margins26, "Marge %      2026")

over50_21 = sum(1 for v in shares21 if v > 50)
over50_26 = sum(1 for v in shares26 if v > 50)
under35_21 = sum(1 for v in shares21 if v < 35)
under35_26 = sum(1 for v in shares26 if v < 35)

print(f"\nSièges winner share > 50% :  2021={over50_21}  →  2026={over50_26}  (Δ={over50_26-over50_21})")
print(f"Sièges winner share < 35% :  2021={under35_21}  →  2026={under35_26}  (Δ={'+' if under35_26-under35_21>0 else ''}{under35_26-under35_21})")

print(f"\nDistribution winner share 2026 :")
buckets = defaultdict(int)
for v in shares26:
    buckets[int(v // 10) * 10] += 1
for b in sorted(buckets):
    bar = "█" * buckets[b]
    print(f"  {b:>3}-{b+10}% : {buckets[b]:>3} ACs  {bar}")


# ─────────────────────────────────────────────
# 5. MARGES PAR RÉGION ET PAR PARTI
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 5 — MARGES PAR RÉGION (2026)")
print("=" * 60)

print(f"\n{'Région':<16} {'Moy share':>10} {'<35% ACs':>9} {'<35%':>6} {'>50% ACs':>9} {'>50%':>6}")
print("-" * 62)
by_region26 = defaultdict(list)
for w in w26.values():
    by_region26[w["region"]].append(w)
for region in REGIONS:
    wl = by_region26[region]
    n  = len(wl)
    avg   = sum(w["winner_share"] for w in wl) / n
    u35   = sum(1 for w in wl if w["winner_share"] < 35)
    o50   = sum(1 for w in wl if w["winner_share"] > 50)
    print(f"{region:<16} {avg:>9.1f}% {u35:>9} {u35/n*100:>5.1f}% {o50:>9} {o50/n*100:>5.1f}%")

print(f"\n{'Parti':<12} {'Sièges':>7} {'Moy share':>10} {'Moy marge':>10}")
print("-" * 43)
by_party26 = defaultdict(list)
for w in w26.values():
    by_party26[w["winner_party"]].append(w)
for p in ["TVK", "DMK", "AIADMK", "INC", "PMK", "CPI", "VCK", "CPI(M)"]:
    wl = by_party26.get(p, [])
    if not wl:
        continue
    avg_share  = sum(w["winner_share"] for w in wl) / len(wl)
    avg_margin = sum(w["margin_pct"]   for w in wl) / len(wl)
    print(f"{p:<12} {len(wl):>7} {avg_share:>9.1f}% {avg_margin:>9.1f}%")


# ─────────────────────────────────────────────
# 6. TOP SIÈGES SERRÉS ET LARGES
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 6 — TOP SIÈGES SERRÉS ET LARGES (2026)")
print("=" * 60)

all26_sorted = sorted(w26.values(), key=lambda x: x["margin_pct"])

print(f"\nTop 10 — plus serrés :")
print(f"{'Circonscription':<24} {'Région':<14} {'Gagnant':>10} {'Share':>7} {'Marge':>7}")
print("-" * 66)
for w in all26_sorted[:10]:
    print(f"{w['constituency']:<24} {w['region']:<14} {w['winner_party']:>10} {w['winner_share']:>6.1f}% {w['margin_pct']:>6.2f}%")

print(f"\nTop 10 — plus larges :")
print(f"{'Circonscription':<24} {'Région':<14} {'Gagnant':>10} {'Share':>7} {'Marge':>7}")
print("-" * 66)
for w in reversed(all26_sorted[-10:]):
    print(f"{w['constituency']:<24} {w['region']:<14} {w['winner_party']:>10} {w['winner_share']:>6.1f}% {w['margin_pct']:>6.2f}%")

# Sièges avec marge < 0.5%
ties = [w for w in w26.values() if w["margin_pct"] < 0.5]
print(f"\nSièges avec marge < 0.5% en 2026 : {len(ties)}")
for w in sorted(ties, key=lambda x: x["margin_pct"]):
    print(f"  {w['constituency']:<24} {w['region']:<14} {w['winner_party']:>10}  marge={w['margin_pct']}%")


# ─────────────────────────────────────────────
# 7. SIÈGES STABLES — bastions
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 7 — BASTIONS (sièges stables)")
print("=" * 60)

stable = [f for f in flips if not f["flipped"]]
by_party_stable  = Counter(s["party"] for s in [
    {"party": w21[f["ac_number"]]["winner_party"]} for f in stable
])

print(f"\n{'Parti':<12} {'Stables':>8} {'Total 2026':>11} {'Rétention':>10}")
print("-" * 45)
for p, n in by_party_stable.most_common():
    total = seats26.get(p, 0)
    if total == 0:
        continue
    print(f"{p:<12} {n:>8} {total:>11} {n/total*100:>9.0f}%")

print(f"\nSièges stables par région :")
region_stable = Counter(f["region"] for f in stable)
region_total  = Counter(w["region"] for w in w26.values())
print(f"{'Région':<16} {'Stables':>8} {'Total':>7} {'%':>7}")
print("-" * 40)
for region in REGIONS:
    n     = region_stable.get(region, 0)
    total = region_total[region]
    print(f"{region:<16} {n:>8} {total:>7} {n/total*100:>6.0f}%")


# ─────────────────────────────────────────────
# 8. VOTE SHARE ÉTAT ENTIER
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("KPI 8 — VOTE SHARE PAR PARTI (état entier)")
print("=" * 60)

def state_vote_share(rows):
    pv = defaultdict(int)
    total = 0
    for r in rows:
        try:
            v = int(r["votes"])
            pv[r["party"]] += v
            total += v
        except ValueError:
            pass
    return {p: round(v / total * 100, 2) for p, v in pv.items()}, total

vs21, tot21 = state_vote_share(r21)
vs26, tot26 = state_vote_share(r26)

print(f"\n{'Parti':<12} {'2021':>9} {'2026':>9} {'Δ pts':>8}")
print("-" * 42)
for p in ["TVK", "DMK", "AIADMK", "NTK", "INC", "BJP", "PMK", "VCK", "AMMK"]:
    s21 = vs21.get(p, 0)
    s26 = vs26.get(p, 0)
    d   = round(s26 - s21, 1)
    print(f"{p:<12} {s21:>8.1f}% {s26:>8.1f}% {('+' if d>0 else '')+str(d):>7}%")

print(f"\nTotal votes 2021 : {tot21:,}")
print(f"Total votes 2026 : {tot26:,}")
print(f"Hausse absolue   : +{tot26-tot21:,} votes ({(tot26/tot21-1)*100:.1f}%)")


# ─────────────────────────────────────────────
# 9. FACT SHEET FINALE
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("FACT SHEET — DECK SLIDES")
print("=" * 60)

print("""
HOOK
  163 / 234 circonscriptions ont changé de gagnant (69.7%)
  TVK : 0 siège en 2021 → 108 sièges en 2026
  89.7% des ACs ont vu leur winner share baisser

Q2 — LES FLIPS
  TVK remporte 108 sièges (tous issus de flips)
    dont 65 pris à DMK | 26 à AIADMK | 11 à INC
  DMK : 133 → 59 (-74 sièges)
  AIADMK : 66 → 47 (-19 sièges)

Q1 — LA GÉOGRAPHIE
  Chennai Metro : 93.8% de flip — TVK 29/32
  Kongu : 81.8% — AIADMK effondré (19 → 7)
  Delta : 45.5% — la plus stable (bastion DMK : 14/33)
  North + Central : AIADMK résiste (15 + 15 sièges)

Q6 — LES MARGES
  Winner share moyen : 48.4% → 38.8% (-9.6 pts)
  Sièges > 50% : 70 (2021) → 13 (2026)
  Sièges < 35% : 2 (2021) → 64 (2026)
  Marge moyenne : 11.7% → 7.7% (-4.0 pts)
  14 sièges avec marge < 0.5%
  TVK gagne plus large (marge moy 10%) que DMK (5%)
  South : région la plus fragmentée (43% des sièges <35%)
  Chennai Metro : aucun siège <35% winner share
""")
