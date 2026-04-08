from datetime import datetime
import time

from agent_core import run_agent_cycle
from data_source import (
    SAMPLE_MATCHES,
    get_hardcoded_match_state,
    get_live_match_state_from_cricbuzz,
    list_live_matches_from_cricbuzz,
)
from history_store import build_history_entry, load_history, save_history_entry
from prematch_advisor import build_pre_match_advice
from strategy_engine import generate_report


def _print_hardcoded_scenarios() -> None:
    print("\nAvailable hardcoded scenarios:")
    for idx, name in enumerate(SAMPLE_MATCHES, start=1):
        print(f"  {idx}. {name}")


def _print_pre_match_advice(state: dict) -> None:
    advice = build_pre_match_advice(state)
    toss = advice["toss"]
    recommended_xi = advice["recommended_xi"]
    lineup = advice["lineup"]

    print("\nPre-Match Advisor")
    print(f"- Toss Recommendation: {toss['decision']} ({toss['confidence']} confidence)")
    print(f"- Summary: {toss['summary']}")
    for reason in toss.get("reasons", []):
        print(f"  • {reason}")

    print(f"- {recommended_xi.get('lineup_type', 'Agent Recommended XI')}: ")
    for team_name, players in recommended_xi.get("teams", {}).items():
        if players:
            print(f"  • {team_name}: {', '.join(players)}")
        else:
            print(f"  • {team_name}: the agent does not yet have enough squad detail to suggest a full XI")

    for reason in recommended_xi.get("reasoning", []):
        print(f"  • Selection logic: {reason}")

    for team_name, notes in recommended_xi.get("comparison_notes", {}).items():
        for note in notes:
            print(f"  • {team_name}: {note}")

    if any(lineup.get("teams", {}).values()):
        print(f"- {lineup.get('lineup_type', 'Announced XI')}: ")
        for team_name, players in lineup.get("teams", {}).items():
            if players:
                print(f"  • {team_name}: {', '.join(players)}")


def _print_win_history(match_key: str) -> None:
    rows = [row for row in load_history(match_key=match_key, limit=6) if row.get("win_probability") is not None]
    if not rows:
        return

    team_name = rows[-1].get("batting_team", "Current Team")
    print(f"\n{team_name} Win% by Over")
    for row in rows[-5:]:
        reason = row.get("change_reason") or "Baseline snapshot."
        print(f"- Over {row.get('overs')}: {row.get('win_probability')}% | {reason}")


def _show_report(state: dict) -> None:
    agent_output = run_agent_cycle(state)
    enriched_state = agent_output["state"]
    plan = agent_output["plan"]
    entry = build_history_entry(state, enriched_state, plan, agent_output)
    history_saved = save_history_entry(entry)

    _print_pre_match_advice(state)

    print("\nAgent Loop")
    print(f"- Objective: {agent_output['objective']}")
    print(f"- Observe: {agent_output['observation']}")
    print(f"- Recall: {agent_output['memory']}")
    print(f"- Evaluate: {agent_output['evaluation']['headline']}")
    print(f"- Reflect: {agent_output['reflection']['reflection']}")
    print(f"- Confidence: {agent_output['confidence']}%")

    print("\nReflection Agent")
    print(f"- Was previous advice correct? {agent_output['reflection']['verdict']}")
    print(f"- Batting next-over adjustment: {agent_output['reflection']['batting_adjustment']}")
    print(f"- Bowling next-over adjustment: {agent_output['reflection']['bowling_adjustment']}")

    print("\n" + generate_report(enriched_state, plan))
    if entry.get("change_reason"):
        print(f"\nOver-by-Over Insight: {entry['change_reason']}")
    elif history_saved:
        print("\nOver-by-Over Insight: Baseline snapshot saved. The next completed over will explain the shift.")
    else:
        print("\nOver-by-Over Insight: Waiting for the current over to finish before saving a new over-level explanation.")

    print(f"\nAgent Evaluation Detail: {agent_output['evaluation']['detail']}")
    print(f"Agent Action Summary: {agent_output['action_summary']}")
    _print_win_history(agent_output["match_key"])

    if state.get("source_url"):
        print(f"\nSource URL: {state['source_url']}")
    status_line = "saved new over-level snapshot" if history_saved else "same over, so no new snapshot was saved"
    print(f"\nHistory Status: {status_line}")


def _summarize_change(previous_state: dict | None, current_state: dict) -> str:
    if previous_state is None:
        return "Initial live snapshot loaded."

    changes = []
    tracked_fields = {
        "runs": "Runs",
        "wickets": "Wickets",
        "overs": "Overs",
        "target": "Target",
    }

    for field, label in tracked_fields.items():
        old_value = previous_state.get(field)
        new_value = current_state.get(field)
        if old_value != new_value:
            changes.append(f"{label}: {old_value} -> {new_value}")

    return " | ".join(changes) if changes else "No scoreboard change since the last refresh."


def _watch_live_match(match_reference: str | None, refresh_interval: int) -> None:
    previous_state = None
    print("\nAuto-refresh is live. Press Ctrl+C to stop.\n")

    try:
        while True:
            state = get_live_match_state_from_cricbuzz(match_reference)
            print("=" * 72)
            print(f"Refresh Time: {datetime.now().strftime('%H:%M:%S')}")
            print(_summarize_change(previous_state, state))
            print("=" * 72)
            _show_report(state)
            previous_state = state
            time.sleep(refresh_interval)
    except KeyboardInterrupt:
        print("\nStopped live auto-refresh.")


def _select_live_mode() -> tuple[dict, str | None, bool, int]:
    live_matches = list_live_matches_from_cricbuzz()

    if live_matches:
        print("\nDetected cricket matches from Cricbuzz:")
        for idx, match in enumerate(live_matches, start=1):
            print(
                f"  {idx}. {match['batting_team']} vs {match['bowling_team']} | "
                f"{match['runs']}/{match['wickets']} ({match['overs']})"
            )
            print(f"     match_id={match.get('match_id')} | {match.get('source_url')}")
    else:
        print("\nNo current live cricket match was detected from the live list.")
        print("You can still paste a Cricbuzz match URL or match_id for a delayed or recently completed game.")

    match_reference = input(
        "\nPaste a Cricbuzz match URL/id/team name, or press Enter for the first detected match: "
    ).strip()
    if not live_matches and not match_reference:
        raise ValueError("Paste a Cricbuzz match URL or match_id when no live match list is available.")

    state = get_live_match_state_from_cricbuzz(match_reference or None)

    auto_refresh_answer = input("Enable auto-refresh for live mode? (Y/n): ").strip().lower()
    auto_refresh = auto_refresh_answer in {"", "y", "yes"}

    refresh_interval = 30
    if auto_refresh:
        interval_input = input("Refresh interval in seconds (default 30): ").strip()
        if interval_input:
            refresh_interval = max(10, int(interval_input))

    return state, (match_reference or state.get("match_id")), auto_refresh, refresh_interval


def _select_match_state() -> tuple[dict, str, str | None, bool, int]:
    print("Choose input mode:")
    print("  1. Hardcoded scenario")
    print("  2. Live Cricbuzz cricket feed")

    mode = input("\nEnter mode (1/2, press Enter for 1): ").strip() or "1"

    if mode == "2":
        state, match_reference, auto_refresh, refresh_interval = _select_live_mode()
        return state, "live", match_reference, auto_refresh, refresh_interval

    _print_hardcoded_scenarios()
    selected = input("\nChoose a scenario name (press Enter for chase_pressure): ").strip()
    state = get_hardcoded_match_state(selected or "chase_pressure")
    return state, "hardcoded", None, False, 0


def main() -> None:
    print("=" * 72)
    print("Cricket Match Analysis Agent (v4 - real agent loop enabled)")
    print("=" * 72)

    try:
        state, source_mode, match_reference, auto_refresh, refresh_interval = _select_match_state()
    except Exception as exc:
        print(f"\nCould not load match state: {exc}")
        return

    _show_report(state)

    if source_mode == "live" and auto_refresh:
        _watch_live_match(match_reference, refresh_interval)
        return

    print("\nTip: choose live mode and enable auto-refresh to watch the strategy update continuously.")


if __name__ == "__main__":
    main()
