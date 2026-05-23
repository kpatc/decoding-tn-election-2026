"""
AtliQ Media — Decoding the 2026 Tamil Nadu Assembly Election
Streamlit Dashboard  |  Arc A: Q1 · Q2 · Q6

Displays the exact same matplotlib/seaborn charts from visualisations.py.
Filters regenerate the charts on filtered data in real time.

Run:
    cd "AtliQ Challenge"
    streamlit run src/dashboard.py
"""

import sys
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

from load_clean import run as load_data
from kpis import (
    build_flip_table, flip_matrix, flip_summary,
    flips_by_region, flips_toward_tvk,
    seats_by_party, seats_by_region_party,
    margin_by_region, margin_by_party,
    vote_share_state, tight_races,
)
from visualisations import (
    plot_seats_by_party,
    plot_flip_matrix,
    plot_flip_rate_by_region,
    plot_seats_by_region,
    plot_winner_share_distribution,
    plot_fragmentation_by_region,
    plot_margin_by_party,
    plot_margin_evolution_by_region,
    plot_tvk_source,
)

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TN Election 2026 — AtliQ Media",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

REGIONS = ["Chennai Metro", "North", "Central", "Kongu", "Delta", "South"]


# ─────────────────────────────────────────────────────────
# DATA LOADING (cached)
# ─────────────────────────────────────────────────────────

@st.cache_data
def get_base_data():
    tables = load_data()
    return tables


def filter_tables(tables: dict, region_filter: list, reserved_filter: list) -> dict:
    """Return a filtered copy of w21, w26, r21, r26."""
    mask21 = (
        tables["w21"]["region"].isin(region_filter) &
        tables["w21"]["reserved"].isin(reserved_filter)
    )
    mask26 = (
        tables["w26"]["region"].isin(region_filter) &
        tables["w26"]["reserved"].isin(reserved_filter)
    )
    mask_r21 = (
        tables["r21"]["region"].isin(region_filter) &
        tables["r21"]["reserved"].isin(reserved_filter)
    )
    mask_r26 = (
        tables["r26"]["region"].isin(region_filter) &
        tables["r26"]["reserved"].isin(reserved_filter)
    )
    return {
        "w21": tables["w21"][mask21].copy(),
        "w26": tables["w26"][mask26].copy(),
        "r21": tables["r21"][mask_r21].copy(),
        "r26": tables["r26"][mask_r26].copy(),
    }


def compute_filtered_kpis(ft: dict) -> dict:
    """Recompute all KPIs on filtered data."""
    w21, w26 = ft["w21"], ft["w26"]
    r21, r26 = ft["r21"], ft["r26"]
    flip_tbl = build_flip_table(w21, w26)
    return {
        "seats_by_party":   seats_by_party(w21, w26),
        "flip_table":       flip_tbl,
        "flip_matrix":      flip_matrix(flip_tbl),
        "flip_summary":     flip_summary(flip_tbl),
        "flips_by_region":  flips_by_region(flip_tbl),
        "flips_toward_tvk": flips_toward_tvk(flip_tbl),
        "seats_by_region":  seats_by_region_party(w21, w26),
        "margin_by_region": margin_by_region(w26),
        "margin_by_party":  margin_by_party(w26),
        "tight_races":      tight_races(w26, threshold=1.0),
    }


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────

def render_sidebar() -> tuple[list, list]:
    st.sidebar.title("🗳️ TN Election 2026")
    st.sidebar.markdown("**AtliQ Media · Analysis Dashboard**")
    st.sidebar.markdown("---")

    st.sidebar.subheader("Filters")
    region_filter = st.sidebar.multiselect(
        "Region",
        options=REGIONS,
        default=REGIONS,
    )
    reserved_filter = st.sidebar.multiselect(
        "Constituency Type",
        options=["GEN", "SC", "ST"],
        default=["GEN", "SC", "ST"],
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigate")
    st.sidebar.markdown("""
- [Scorecards](#scorecards)
- [Q2 — Flips](#q2-flips)
- [Q1 — Geography](#q1-geography)
- [Q6 — Margins](#q6-margins)
- [Data Limitations](#limitations)
    """)
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Data:** Election Commission of India  \n"
        "2021: Trivedi Centre for Political Data  \n"
        "2026: ECI live results portal  \n"
        "⚠️ Form-20 final data not yet released"
    )
    return region_filter, reserved_filter


# ─────────────────────────────────────────────────────────
# SECTION 0 — SCORECARDS
# ─────────────────────────────────────────────────────────

def render_scorecards(ft: dict, kpis: dict):
    st.markdown('<h2 id="scorecards">At a Glance</h2>', unsafe_allow_html=True)

    w21, w26 = ft["w21"], ft["w26"]
    fs = kpis["flip_summary"]

    tvk_26   = int((w26["winner_party"] == "TVK").sum())
    dmk_26   = int((w26["winner_party"] == "DMK").sum())
    dmk_21   = int((w21["winner_party"] == "DMK").sum())
    aiadmk_26 = int((w26["winner_party"] == "AIADMK").sum())
    aiadmk_21 = int((w21["winner_party"] == "AIADMK").sum())
    avg_m21  = round(w21["margin_pct"].mean(), 1)
    avg_m26  = round(w26["margin_pct"].mean(), 1)
    total    = fs["total_acs"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Constituencies Flipped",
              f"{fs['flipped']} / {total}",
              f"{fs['flip_rate']}%")
    c2.metric("TVK Seats (2026)", tvk_26,
              "New party — 0 in 2021")
    c3.metric("DMK Seats", dmk_26,
              f"{dmk_26 - dmk_21:+d} vs 2021")
    c4.metric("AIADMK Seats", aiadmk_26,
              f"{aiadmk_26 - aiadmk_21:+d} vs 2021")
    c5.metric("Avg Victory Margin", f"{avg_m26}%",
              f"{avg_m26 - avg_m21:+.1f} pts vs 2021")


# ─────────────────────────────────────────────────────────
# SECTION 1 — Q2 : FLIPS
# ─────────────────────────────────────────────────────────

def render_flips(ft: dict, kpis: dict):
    st.markdown("---")
    st.markdown('<h2 id="q2-flips">Q2 — The Flip Story: Who Changed Hands?</h2>',
                unsafe_allow_html=True)
    st.caption(
        "A constituency is 'flipped' when the winning party in 2026 differs from 2021. "
        f"**{kpis['flip_summary']['flipped']} / {kpis['flip_summary']['total_acs']} "
        f"constituencies ({kpis['flip_summary']['flip_rate']}%) changed winner.**"
    )

    # Row 1: flip rate + matrix side by side
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Flip Rate by Region")
        fig = plot_flip_rate_by_region(kpis["flips_by_region"])
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    with col2:
        st.subheader("Seat Transition Matrix (Flipped Seats Only)")
        fig = plot_flip_matrix(kpis["flip_matrix"])
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    # Row 2: TVK origin full width
    st.subheader("Origin of TVK Seats — Which Party Held Them in 2021")
    fig = plot_tvk_source(kpis["flips_toward_tvk"])
    st.pyplot(fig, use_container_width=True, clear_figure=True)

    # Row 3: overall seats full width
    st.subheader("Seats Won by Party — 2021 vs 2026")
    fig = plot_seats_by_party(kpis["seats_by_party"])
    st.pyplot(fig, use_container_width=True, clear_figure=True)


# ─────────────────────────────────────────────────────────
# SECTION 2 — Q1 : GEOGRAPHY
# ─────────────────────────────────────────────────────────

def render_geography(ft: dict, kpis: dict):
    st.markdown("---")
    st.markdown('<h2 id="q1-geography">Q1 — The Geographic Story: Where Did the Map Change?</h2>',
                unsafe_allow_html=True)

    # Stacked bars side by side — full width
    st.subheader("Seat Distribution by Region and Party — 2021 vs 2026")
    fig = plot_seats_by_region(kpis["seats_by_region"])
    st.pyplot(fig, use_container_width=True, clear_figure=True)


# ─────────────────────────────────────────────────────────
# SECTION 3 — Q6 : MARGINS
# ─────────────────────────────────────────────────────────

def render_margins(ft: dict, kpis: dict):
    st.markdown("---")
    st.markdown('<h2 id="q6-margins">Q6 — The Margin Story: How Competitive Was 2026?</h2>',
                unsafe_allow_html=True)
    st.caption(
        "Victory margin = (winner votes − runner-up votes) / total valid votes.  "
        "Winner share = winner votes / total valid votes."
    )

    w21, w26 = ft["w21"], ft["w26"]

    # Row 1: histogram + fragmentation
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Winner's Vote Share Distribution")
        fig = plot_winner_share_distribution(w21, w26)
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    with col2:
        st.subheader("Electoral Fragmentation by Region")
        fig = plot_fragmentation_by_region(kpis["margin_by_region"])
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    # Row 2: margin evolution + scatter
    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.subheader("Average Victory Margin by Region — 2021 vs 2026")
        fig = plot_margin_evolution_by_region(w21, w26)
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    with col4:
        st.subheader("Vote Share vs Victory Margin by Party")
        fig = plot_margin_by_party(w26)
        st.pyplot(fig, use_container_width=True, clear_figure=True)

    # Tight races table
    tight = kpis["tight_races"]
    if not tight.empty:
        with st.expander(f"📋  Tight Races — {len(tight)} seats won with margin < 1%"):
            display = tight.copy().reset_index(drop=True)
            display.index += 1
            display["winner_share"] = display["winner_share"].map("{:.2f}%".format)
            display["margin_pct"]   = display["margin_pct"].map("{:.2f}%".format)
            display["total_votes"]  = display["total_votes"].map("{:,}".format)
            st.dataframe(
                display.rename(columns={
                    "constituency": "Constituency",
                    "region":       "Region",
                    "reserved":     "Type",
                    "winner_party": "Winner",
                    "winner_share": "Vote Share",
                    "margin_pct":   "Margin",
                    "total_votes":  "Total Votes",
                }),
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────
# SECTION 4 — DATA LIMITATIONS
# ─────────────────────────────────────────────────────────

def render_limitations():
    st.markdown("---")
    st.markdown('<h2 id="limitations">⚠️ Data Limitations</h2>', unsafe_allow_html=True)
    st.markdown("""
| Limitation | Impact |
|---|---|
| 2026 Form-20 (final audited data) not yet released | Vote totals may shift marginally |
| 2026 turnout column is blank in source CSV | Per-constituency turnout comparison not possible |
| No polling-station level data | Cannot identify within-constituency patterns |
| No demographic data | Cannot make any claims about voter characteristics |
| No causal inference | All patterns are descriptive — not explanatory |
    """)


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main():
    st.markdown(
        """
        <h1 style='margin-bottom:2px'>
            Decoding the 2026 Tamil Nadu Assembly Election
        </h1>
        <p style='color:#888; font-size:15px; margin-top:0'>
            AtliQ Media · Data Analysis Dashboard ·
            Source: Election Commission of India
        </p>
        <hr style='margin-top:6px; margin-bottom:20px'>
        """,
        unsafe_allow_html=True,
    )

    region_filter, reserved_filter = render_sidebar()

    if not region_filter or not reserved_filter:
        st.warning("Please select at least one region and one constituency type.")
        st.stop()

    with st.spinner("Loading data..."):
        tables = get_base_data()

    ft   = filter_tables(tables, region_filter, reserved_filter)
    kpis = compute_filtered_kpis(ft)

    render_scorecards(ft, kpis)
    render_flips(ft, kpis)
    render_geography(ft, kpis)
    render_margins(ft, kpis)
    render_limitations()

    st.caption(
        "Built with Python · Streamlit · Matplotlib · Seaborn  |  "
        "Data: ECI 2021 & 2026  |  "
        "⚠️ Non-partisan data analysis exercise — Codebasics RPC #21"
    )


if __name__ == "__main__":
    main()
