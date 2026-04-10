from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from agent_core import run_agent_cycle
from data_source import SAMPLE_MATCHES, get_hardcoded_match_state, get_live_match_state_from_cricbuzz, list_live_matches_from_cricbuzz
from history_store import build_history_entry, get_match_key, load_history, save_history_entry
from prematch_advisor import build_pre_match_advice
from simulation_engine import generate_what_if_scenarios


LIVE_MODE = "Live Cricbuzz"
HARDCODED_MODE = "Hardcoded"

st.set_page_config(page_title="Cricket Match Analysis Agent", page_icon="🏏", layout="wide")


@st.cache_data(ttl=15, show_spinner=False)
def _cached_live_matches() -> list[dict]:
    return list_live_matches_from_cricbuzz()


def _load_state(source_mode: str, scenario: str, match_reference: str | None) -> dict:
    if source_mode == HARDCODED_MODE:
        return get_hardcoded_match_state(scenario)
    return get_live_match_state_from_cricbuzz(match_reference or None)


def _persist_history(state: dict, enriched_state: dict, plan: dict, agent_output: dict) -> tuple[dict, bool]:
    entry = build_history_entry(state, enriched_state, plan, agent_output)
    saved = save_history_entry(entry)
    return entry, saved


def _render_team_lists(title: str, teams: dict[str, list[str]], empty_message: str) -> None:
    st.markdown(f"**{title}**")
    team_columns = st.columns(2)
    for idx, (team_name, players) in enumerate(teams.items()):
        with team_columns[idx % 2]:
            st.markdown(f"**{team_name}**")
            if players:
                for player in players:
                    st.markdown(f"- {player}")
            else:
                st.caption(empty_message)


def _render_pre_match_advice(state: dict) -> None:
    advice = build_pre_match_advice(state)
    toss = advice["toss"]
    recommended_xi = advice["recommended_xi"]
    lineup = advice["lineup"]

    st.subheader("Pre-Match Advisor")
    col1, col2 = st.columns([1, 1])
    col1.metric("Toss Call", toss["decision"])
    col2.metric("Confidence", toss["confidence"])
    st.markdown(f"**Summary:** {toss['summary']}")
    for reason in toss.get("reasons", []):
        st.markdown(f"- {reason}")

    _render_team_lists(
        recommended_xi.get("lineup_type", "Agent Recommended XI"),
        recommended_xi.get("teams", {}),
        "The agent needs more squad detail to suggest a full XI.",
    )
    for reason in recommended_xi.get("reasoning", []):
        st.markdown(f"- **Selection logic:** {reason}")
    for team_name, notes in recommended_xi.get("comparison_notes", {}).items():
        for note in notes:
            st.markdown(f"- **{team_name}:** {note}")

    if any(lineup.get("teams", {}).values()):
        _render_team_lists(
            lineup.get("lineup_type", "Announced XI from Source"),
            lineup.get("teams", {}),
            "Lineup not available from source yet.",
        )


def _render_metrics(enriched_state: dict) -> None:
    batting_team = enriched_state.get("batting_team", "Team A")
    bowling_team = enriched_state.get("bowling_team", "Team B")
    probability = enriched_state.get("estimated_win_probability")
    bowling_probability = enriched_state.get("estimated_bowling_win_probability")
    rrr = enriched_state.get("required_run_rate")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score", f"{enriched_state['runs']}/{enriched_state['wickets']}")
    col2.metric("Phase", enriched_state["phase"].title())
    col3.metric("Current RR", enriched_state["current_run_rate"])
    col4.metric("Required RR", rrr if rrr is not None else "N/A")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Balls Left", enriched_state["balls_left"])
    if enriched_state.get("target") is not None:
        col6.metric("Runs Needed", enriched_state.get("runs_needed") if enriched_state.get("runs_needed") is not None else "N/A")
    else:
        projected_total = enriched_state.get("projected_total") or enriched_state.get("runs")
        par_score = enriched_state.get("par_score")
        col6.metric("Projected Total", projected_total, delta=f"Par {par_score}" if par_score is not None else None)
    col7.metric(f"{batting_team} Win %", f"{probability}%" if probability is not None else "N/A")
    col8.metric(f"{bowling_team} Win %", f"{bowling_probability}%" if bowling_probability is not None else "N/A")

    if enriched_state.get("match_context"):
        st.info(enriched_state["match_context"])


def _render_agent_loop(agent_output: dict) -> None:
    st.subheader("Agent Loop")
    st.markdown(f"**Objective:** {agent_output['objective']}")

    evaluation = agent_output["evaluation"]
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Agent Confidence", f"{agent_output['confidence']}%")
    metric_col2.metric("Overall Eval", evaluation['status'].replace('-', ' ').title())
    metric_col3.metric("Batting Eval", evaluation.get('batting_status', 'n/a').replace('-', ' ').title())
    metric_col4.metric("Bowling Eval", evaluation.get('bowling_status', 'n/a').replace('-', ' ').title())

    st.markdown(f"- **Batting review:** {evaluation.get('batting_detail', evaluation['detail'])}")
    st.markdown(f"- **Bowling review:** {evaluation.get('bowling_detail', evaluation['detail'])}")

    for step in agent_output["reasoning_steps"]:
        st.markdown(f"**{step['step']}:** {step['detail']}")


def _render_reflection(agent_output: dict) -> None:
    reflection = agent_output["reflection"]
    st.subheader("Reflection Agent")

    col1, col2, col3 = st.columns(3)
    col1.metric("Previous Advice", reflection["verdict"])
    col2.metric("Batting Adjustment", reflection["batting_adjustment"])
    col3.metric("Bowling Adjustment", reflection["bowling_adjustment"])
    st.info(reflection["reflection"])


def _render_strategy(plan: dict, enriched_state: dict) -> None:
    st.subheader("Team Perspectives")

    if plan.get("recommended_action") or plan.get("bowling_recommended_action"):
        st.markdown("#### Decision Recommendation")
        st.info(
            f"Batting: {plan.get('recommended_action', 'N/A')}\n\n"
            f"Bowling: {plan.get('bowling_recommended_action', 'N/A')}\n\n"
            f"Window: {plan.get('decision_window', 'next over')} | Priority: {plan.get('priority', 'balanced')}"
        )

    if enriched_state.get("upcoming_phase_note"):
        st.info(f"Upcoming phase read: {enriched_state['upcoming_phase_note']}")

    batting_col, bowling_col = st.columns(2)
    with batting_col:
        st.markdown("### Batting Plan")
        st.success(plan["strategy"])
        st.markdown(f"**Next Over Target:** `{plan['target_runs']}`")
        st.markdown(f"**Risk Level:** `{plan['risk_level']}`")
        st.markdown(f"**Focus:** {plan['focus']}")
        st.markdown(f"**Batting Team:** {enriched_state.get('batting_team', 'Unknown')}")

    with bowling_col:
        st.markdown("### Bowling Counter-Plan")
        st.warning(plan.get("bowling_strategy", "N/A"))
        st.markdown(f"**Risk Level:** `{plan.get('bowling_risk_level', 'N/A')}`")
        st.markdown(f"**Focus:** {plan.get('bowling_focus', 'N/A')}")
        st.markdown(f"**Bowling Team:** {enriched_state.get('bowling_team', 'Unknown')}")

    if plan.get("current_batter_insight") or plan.get("current_bowler_insight"):
        insight_col1, insight_col2 = st.columns(2)
        with insight_col1:
            if plan.get("current_batter_insight"):
                st.markdown("#### Current Batter Insight")
                st.success(plan["current_batter_insight"])
        with insight_col2:
            if plan.get("current_bowler_insight"):
                st.markdown("#### Current Bowler Insight")
                st.warning(plan["current_bowler_insight"])

    if plan.get("batting_tactics"):
        st.markdown("#### Batting Tactics")
        for note in plan["batting_tactics"]:
            st.markdown(f"- {note}")

    if plan.get("bowling_tactics"):
        st.markdown("#### Bowling Tactics")
        for note in plan["bowling_tactics"]:
            st.markdown(f"- {note}")

    if plan.get("phase_watchouts"):
        st.markdown("#### Phase Watchouts")
        for note in plan["phase_watchouts"]:
            st.markdown(f"- {note}")

    if plan.get("matchup_insights"):
        st.markdown("#### Matchup Insights")
        for note in plan["matchup_insights"]:
            st.markdown(f"- {note}")

    if plan.get("awareness_notes"):
        st.markdown("#### Key Facts Driving This Call")
        for note in plan["awareness_notes"]:
            st.markdown(f"- {note}")


def _render_what_if(enriched_state: dict) -> None:
    st.subheader("What-If Simulation")
    scenarios = generate_what_if_scenarios(enriched_state)
    columns = st.columns(min(len(scenarios), 4)) if scenarios else []
    for idx, scenario in enumerate(scenarios):
        with columns[idx % len(columns)]:
            st.markdown(f"**{scenario['label']}**")
            st.caption(scenario.get("summary", ""))
            st.metric("Win %", f"{scenario.get('win_probability', 'N/A')}%", delta=f"{scenario.get('win_probability_delta', 0)}%")
            st.markdown(f"`{scenario.get('projected_score', 'N/A')}`")


def _render_over_change(entry: dict, saved: bool) -> None:
    st.subheader("Over-by-Over Insight")
    if entry.get("change_reason"):
        st.info(entry["change_reason"])
    elif saved:
        st.info("Baseline snapshot saved. The next completed over will explain the shift.")
    else:
        st.caption("Waiting for the current over to finish before logging a new over-level explanation.")


def _render_history(match_key: str) -> None:
    st.subheader("Previous Overs + Recommendation History")
    rows = load_history(match_key=match_key, limit=50)

    if not rows:
        st.info("No saved history yet for this match.")
        return

    history_df = pd.DataFrame(rows)
    history_df = history_df.sort_values("timestamp", ascending=False)

    display_columns = [
        "timestamp",
        "score",
        "overs",
        "total_overs",
        "phase",
        "win_probability",
        "win_probability_delta",
        "strategy",
        "bowling_strategy",
        "target_runs",
        "risk_level",
        "agent_confidence",
        "agent_batting_evaluation_headline",
        "agent_bowling_evaluation_headline",
        "change_reason",
        "focus",
        "bowling_focus",
    ]
    available_columns = [column for column in display_columns if column in history_df.columns]
    st.dataframe(history_df[available_columns], use_container_width=True, hide_index=True)

    if {"overs", "runs"}.issubset(history_df.columns):
        st.markdown("#### Runs by Over")
        trend_df = history_df[["overs", "runs"]].dropna().sort_values("overs")
        st.line_chart(trend_df, x="overs", y="runs", use_container_width=True)

    if {"overs", "win_probability"}.issubset(history_df.columns):
        latest_team = rows[-1].get("batting_team", "Current Team")
        st.markdown(f"#### {latest_team} Win % by Over")
        win_df = history_df[["overs", "win_probability"]].dropna().sort_values("overs")
        st.line_chart(win_df, x="overs", y="win_probability", use_container_width=True)


def _select_live_reference(manual_reference: str | None) -> str | None:
    match_reference = manual_reference.strip() or None if manual_reference else None

    try:
        live_matches = _cached_live_matches()
    except Exception as exc:
        st.warning(f"Could not load live match list: {exc}")
        return match_reference

    if not live_matches:
        return match_reference

    options = {
        f"{match['batting_team']} vs {match['bowling_team']} | {match['runs']}/{match['wickets']} ({match['overs']})": match
        for match in live_matches
    }
    selected_label = st.selectbox("Detected live matches", list(options.keys()), index=0)
    selected_match = options[selected_label]
    return match_reference or selected_match.get("source_url") or selected_match.get("match_id")


def _render_sidebar() -> tuple[str, bool, int, str, str | None, bool]:
    with st.sidebar:
        st.header("Controls")
        source_mode = st.radio("Data source", [LIVE_MODE, HARDCODED_MODE], index=0)
        auto_refresh = st.checkbox("Auto-refresh", value=(source_mode == LIVE_MODE))
        refresh_interval = st.slider("Refresh interval (seconds)", min_value=10, max_value=120, value=30, step=5)
        manual_reference = st.text_input("Optional match URL / match_id / team name")
        refresh_now = st.button("Refresh now")

        scenario = "chase_pressure"
        match_reference = manual_reference.strip() or None

        if source_mode == HARDCODED_MODE:
            scenario = st.selectbox("Scenario", list(SAMPLE_MATCHES.keys()), index=0)
        else:
            match_reference = _select_live_reference(manual_reference)

    return source_mode, auto_refresh, refresh_interval, scenario, match_reference, refresh_now


def _render_snapshot(state: dict) -> None:
    st.subheader("Match Snapshot")
    total_overs = int(state.get("total_overs") or 20)
    st.markdown(
        f"**{state.get('batting_team', 'Unknown')}** vs **{state.get('bowling_team', 'Unknown')}**  \\n"
        f"Score: `{state['runs']}/{state['wickets']}` in `{state['overs']}` overs"
    )

    highlight = state.get("result_summary") or state.get("status")
    if highlight:
        if state.get("is_match_complete"):
            st.success(highlight)
        elif state.get("is_innings_complete"):
            st.info(highlight)
        else:
            st.caption(highlight)

    if total_overs != 20:
        st.warning(f"Rain-impacted match: reduced to **{total_overs} overs per side**.")
    if state.get("upcoming_phase_note") and not state.get("is_match_complete"):
        st.info(state["upcoming_phase_note"])
    if state.get("conditions_note"):
        st.caption(state["conditions_note"])
    if state.get("striker") or state.get("bowler"):
        st.markdown(
            f"**Current matchup:** {state.get('striker', 'N/A')} `{state.get('striker_score', '')}` | "
            f"{state.get('non_striker', 'N/A')} `{state.get('non_striker_score', '')}` | "
            f"Bowler: {state.get('bowler', 'N/A')} `{state.get('bowler_score', '')}`"
        )
    if state.get("venue"):
        st.markdown(f"**Venue:** {state['venue']}")
    if state.get("source_url"):
        st.markdown(f"**Source:** [Cricbuzz link]({state['source_url']})")


def main() -> None:
    st.title("🏏 Cricket Match Analysis Agent")
    st.caption("Live strategy suggestions, win probability heuristic, and recommendation history.")

    source_mode, auto_refresh, refresh_interval, scenario, match_reference, refresh_now = _render_sidebar()

    if refresh_now:
        st.cache_data.clear()
        st.rerun()

    if source_mode == LIVE_MODE and not match_reference:
        st.info(
            "No active scored cricket match is available right now from Cricbuzz. "
            "Paste a Cricbuzz match URL to analyze a delayed or pre-start match, or switch to Hardcoded mode."
        )

    try:
        state = _load_state(source_mode, scenario, match_reference)
    except Exception as exc:
        st.error(f"Could not load match state: {exc}")
        return

    agent_output = run_agent_cycle(state)
    enriched_state = agent_output["state"]
    plan = agent_output["plan"]
    latest_entry, history_saved = _persist_history(state, enriched_state, plan, agent_output)

    match_key = get_match_key(state)
    _render_snapshot(state)
    if enriched_state.get("is_pre_match"):
        _render_pre_match_advice(state)
    _render_metrics(enriched_state)
    _render_agent_loop(agent_output)
    _render_reflection(agent_output)
    _render_strategy(plan, enriched_state)
    _render_what_if(enriched_state)
    _render_over_change(latest_entry, history_saved)
    _render_history(match_key)

    st.caption(f"Last updated from source at app refresh time. Match key: `{match_key}`")

    if source_mode == LIVE_MODE and auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
