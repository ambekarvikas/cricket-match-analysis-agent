from __future__ import annotations

import re
from typing import Any, Dict, Optional


def overs_to_balls(overs: float) -> int:
    """Convert cricket overs notation like 15.3 into balls bowled."""
    overs_str = str(overs)
    if "." in overs_str:
        whole, part = overs_str.split(".", 1)
        balls = int(part[:1]) if part else 0
    else:
        whole, balls = overs_str, 0

    whole_overs = int(whole)
    if balls > 5:
        raise ValueError(f"Invalid over value: {overs}")

    return whole_overs * 6 + balls


def balls_to_overs(balls: int) -> str:
    return f"{balls // 6}.{balls % 6}"


def calculate_current_rr(runs: int, overs: float) -> float:
    balls_bowled = overs_to_balls(overs)
    if balls_bowled == 0:
        return 0.0
    return round((runs / balls_bowled) * 6, 2)


def calculate_required_rr(runs_needed: int, balls_left: int) -> float:
    if balls_left <= 0 or runs_needed <= 0:
        return 0.0
    return round((runs_needed / balls_left) * 6, 2)


def get_phase(overs: float, total_overs: float = 20) -> str:
    total_overs = total_overs or 20
    powerplay_limit = max(2.0, round(total_overs * 0.30, 1))
    death_start = max(powerplay_limit + 2.0, round(total_overs * 0.75, 1))

    if overs < powerplay_limit:
        return "powerplay"
    if overs < death_start:
        return "middle"
    return "death"


def _estimate_par_score(total_overs: float) -> int:
    if total_overs <= 8:
        par_rr = 9.4
    elif total_overs <= 12:
        par_rr = 9.0
    elif total_overs <= 16:
        par_rr = 8.6
    else:
        par_rr = 8.4
    return int(round(total_overs * par_rr))


def _estimate_projected_total(state: Dict[str, Any]) -> int:
    total_overs = float(state.get("total_overs") or 20)
    runs = int(state.get("runs") or 0)
    overs = float(state.get("overs") or 0)
    crr = float(state.get("current_run_rate") or 0)
    wickets_in_hand = int(state.get("wickets_in_hand") or 0)

    if overs <= 0 or crr <= 0:
        return runs

    overs_left = max(total_overs - overs, 0)
    base_projection = runs + (crr * overs_left)
    finishing_bonus = max(wickets_in_hand - 5, 0) * (1.6 if overs_left >= 2 else 0.8)
    collapse_penalty = max(5 - wickets_in_hand, 0) * 2.2
    return int(round(base_projection + finishing_bonus - collapse_penalty))


def enrich_match_state(state: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(state)
    total_overs = float(enriched.get("total_overs") or 20)
    total_balls = int(total_overs * 6)
    balls_bowled = overs_to_balls(enriched["overs"])
    balls_left = max(total_balls - balls_bowled, 0)
    status_text = str(enriched.get("status", "")).lower()
    conditions_note = enriched.get("conditions_note") or ""
    is_pre_match = bool(enriched.get("is_pre_match")) or (
        enriched.get("runs", 0) == 0
        and enriched.get("overs", 0) == 0
        and any(token in status_text for token in ("delay", "preview", "rain"))
    )

    enriched["total_overs"] = total_overs
    enriched["is_pre_match"] = is_pre_match
    enriched["balls_bowled"] = balls_bowled
    enriched["balls_left"] = balls_left
    enriched["overs_left"] = balls_to_overs(balls_left)
    enriched["phase"] = "pre-match" if is_pre_match else get_phase(enriched["overs"], total_overs=total_overs)
    enriched["current_run_rate"] = calculate_current_rr(enriched["runs"], enriched["overs"])
    enriched["wickets_in_hand"] = max(10 - enriched["wickets"], 0)
    enriched["match_context"] = (
        f"Rain-shortened to {int(total_overs)} overs per side. {conditions_note}".strip()
        if total_overs != 20
        else (conditions_note.strip() or "Standard 20-over match")
    )

    target = enriched.get("target")
    if target is not None:
        runs_needed = max(target - enriched["runs"], 0)
        enriched["runs_needed"] = runs_needed
        enriched["required_run_rate"] = calculate_required_rr(runs_needed, balls_left)
    else:
        enriched["runs_needed"] = None
        enriched["required_run_rate"] = None

    enriched["par_score"] = _estimate_par_score(total_overs)
    enriched["projected_total"] = _estimate_projected_total(enriched)

    batting_probability = estimate_win_probability(enriched)
    bowling_probability = 100 - batting_probability if batting_probability is not None else None
    enriched["estimated_win_probability"] = batting_probability
    enriched["estimated_bowling_win_probability"] = bowling_probability
    enriched["win_probability_by_team"] = {
        enriched.get("batting_team", "Team A"): batting_probability,
        enriched.get("bowling_team", "Team B"): bowling_probability,
    }
    return enriched


def estimate_win_probability(state: Dict[str, Any]) -> Optional[int]:
    """Heuristic win probability for pre-match, first-innings, and chase states."""
    if state.get("is_pre_match"):
        return 50

    if state.get("target") is None:
        total_overs = float(state.get("total_overs") or 20)
        par_score = int(state.get("par_score") or _estimate_par_score(total_overs))
        projected_total = int(state.get("projected_total") or state.get("runs") or 0)
        wickets_in_hand = int(state.get("wickets_in_hand") or 0)
        balls_bowled = int(state.get("balls_bowled") or 0)
        total_balls = max(int(total_overs * 6), 1)
        sample_factor = min((balls_bowled / total_balls) / 0.55, 1.0)
        par_progress = par_score * (balls_bowled / total_balls)

        score = 50
        score += (projected_total - par_score) * 0.55 * max(sample_factor, 0.35)
        score += (int(state.get("runs") or 0) - par_progress) * 0.25
        score += (wickets_in_hand - 5) * 2.5

        if state.get("phase") == "death":
            score += 4
        if wickets_in_hand <= 4:
            score -= 6

        return max(1, min(99, int(round(score))))

    runs_needed = state["runs_needed"]
    balls_left = state["balls_left"]
    wickets_in_hand = state["wickets_in_hand"]
    rrr = state["required_run_rate"] or 0
    crr = state["current_run_rate"] or 0

    if runs_needed <= 0:
        return 99
    if balls_left <= 0:
        return 1

    score = 50
    score += (wickets_in_hand - 5) * 4
    score -= max(rrr - crr, 0) * 6
    score += max(crr - rrr, 0) * 3

    if state["phase"] == "death" and rrr > 10:
        score -= 10
    if state["phase"] == "powerplay" and wickets_in_hand >= 8:
        score += 5
    if runs_needed <= 20 and wickets_in_hand >= 3:
        score += 12

    return max(1, min(99, int(round(score))))


BOWLER_STYLE_HINTS = {
    "Jasprit Bumrah": "fast",
    "Trent Boult": "left-arm pace",
    "Deepak Chahar": "swing pace",
    "Shardul Thakur": "pace",
    "Jofra Archer": "fast",
    "Nandre Burger": "left-arm pace",
    "Mitchell Santner": "left-arm spin",
    "AM Ghazanfar": "spin",
    "Ravindra Jadeja": "left-arm spin",
    "Yuzvendra Chahal": "leg-spin",
    "Varun Chakaravarthy": "mystery spin",
    "Sunil Narine": "spin",
    "Kuldeep Yadav": "wrist-spin",
    "Ravi Bishnoi": "leg-spin",
    "Harshal Patel": "slower-ball pace",
    "Bhuvneshwar Kumar": "swing pace",
    "Mohammed Shami": "seam pace",
    "Arshdeep Singh": "left-arm pace",
}

BATTER_MATCHUP_HINTS = {
    "Yashasvi Jaiswal": "Yashasvi Jaiswal is strongest when pace sits in his arc, so change of pace and wider lines are safer than slot balls.",
    "Vaibhav Sooryavanshi": "Vaibhav Sooryavanshi is playing high-tempo cricket, so denying pace-on length is critical.",
    "Rohit Sharma": "Rohit Sharma enjoys width and pace in the powerplay, especially if bowlers miss full outside off.",
    "Suryakumar Yadav": "Suryakumar Yadav punishes predictable pace and fixed fields, so bowlers must vary angle and pace.",
    "Tilak Varma": "Tilak Varma handles spin well through the middle overs, so seamers must hit hard lengths or wide yorkers.",
    "Hardik Pandya": "Hardik Pandya looks for pace-on access down the ground in short formats, so cutters into the pitch are safer.",
    "Shimron Hetmyer": "Shimron Hetmyer is most dangerous when bowlers feed the leg-side arc, so keep the ball wide and into the surface.",
}


def _parse_batter_score(score_text: Optional[str]) -> tuple[int, int, float]:
    if not score_text:
        return 0, 0, 0.0

    match = re.search(r"(\d+)\((\d+)\)", str(score_text))
    if not match:
        return 0, 0, 0.0

    runs = int(match.group(1))
    balls = int(match.group(2))
    strike_rate = round((runs / balls) * 100, 1) if balls else 0.0
    return runs, balls, strike_rate


def _parse_bowler_figures(figures_text: Optional[str]) -> tuple[float, int, int, float]:
    if not figures_text:
        return 0.0, 0, 0, 0.0

    match = re.search(r"(\d+(?:\.\d+)?)\-(\d+)\-(\d+)\-(\d+)", str(figures_text))
    if not match:
        return 0.0, 0, 0, 0.0

    overs_bowled = float(match.group(1))
    runs_conceded = int(match.group(3))
    wickets = int(match.group(4))
    economy = round(runs_conceded / overs_bowled, 2) if overs_bowled else 0.0
    return overs_bowled, runs_conceded, wickets, economy


def _infer_bowler_style(name: Optional[str]) -> str:
    if not name:
        return ""
    if name in BOWLER_STYLE_HINTS:
        return BOWLER_STYLE_HINTS[name]

    lowered = name.lower()
    if any(token in lowered for token in ("chahal", "bishnoi", "kuldeep", "chakaravarthy", "santner", "jadeja", "narine")):
        return "spin"
    if any(token in lowered for token in ("bumrah", "boult", "archer", "thakur", "chahar", "shami", "arshdeep", "harshal")):
        return "pace"
    return "pace"


def _build_matchup_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    notes: list[str] = []
    batting_note = ""
    bowling_note = ""

    total_overs = int(state.get("total_overs") or 20)
    if total_overs != 20:
        notes.append(f"This is a reduced {total_overs}-over game, so each over has amplified impact.")
        batting_note += f" In a {total_overs}-over game there is no room for a slow reset."
        bowling_note += f" In a {total_overs}-over game, one quiet over is match-shaping."

    striker = state.get("striker")
    striker_score = state.get("striker_score")
    non_striker = state.get("non_striker")
    non_striker_score = state.get("non_striker_score")
    bowler = state.get("bowler")
    bowler_score = state.get("bowler_score")
    bowler_style = _infer_bowler_style(bowler)

    if striker and striker_score:
        runs, balls, strike_rate = _parse_batter_score(striker_score)
        if balls:
            notes.append(f"{striker} is {runs}({balls}) at SR {strike_rate:.0f}.")
        hint = BATTER_MATCHUP_HINTS.get(striker)
        if hint:
            notes.append(hint)

        if balls >= 8 and strike_rate >= 180:
            batting_note += f" Keep {striker} on strike because he is already dictating terms at {runs}({balls})."
            if bowler and "pace" in bowler_style:
                bowling_note += f" {striker} is taking on {bowler}'s {bowler_style}; bring on a slower bowler or cutters into the pitch now."
            elif bowler and "spin" in bowler_style:
                bowling_note += f" {striker} is reading spin early, so switch to hard-length pace or wide yorkers instead of feeding his arc."
        elif balls >= 8 and strike_rate <= 115:
            batting_note += f" {striker} is not fully settled at {runs}({balls}), so let the better timer of the ball control strike."
            if bowler:
                bowling_note += f" {striker} is not settled yet, so keep {bowler} attacking the stumps with a catching ring."

    if non_striker and non_striker_score:
        nruns, nballs, nstrike_rate = _parse_batter_score(non_striker_score)
        if nballs and nstrike_rate >= 160:
            notes.append(f"{non_striker} is also moving well at {nruns}({nballs}) at SR {nstrike_rate:.0f}.")
            batting_note += f" {non_striker} is also set, so avoid exposing a new batter unnecessarily."

    if bowler and bowler_score:
        overs_bowled, runs_conceded, wickets, economy = _parse_bowler_figures(bowler_score)
        if overs_bowled:
            notes.append(f"Current bowler {bowler} has figures {bowler_score} (economy {economy:.1f}).")
            if economy >= 12:
                if "pace" in bowler_style:
                    bowling_note += f" {bowler} is going at {economy:.1f}; take pace off or go to spin/change-ups immediately."
                elif "spin" in bowler_style:
                    bowling_note += f" {bowler} is being lined up despite the slower pace; switch to your best hard-length seamer."
            elif wickets >= 1 and economy <= 8:
                bowling_note += f" {bowler} is controlling the matchup well, so keep him in the contest if an over remains."

    return {
        "batting_note": " ".join(batting_note.split()).strip(),
        "bowling_note": " ".join(bowling_note.split()).strip(),
        "awareness_notes": notes,
    }


def _first_innings_strategy(phase: str, total_overs: float = 20) -> Dict[str, str]:
    shortened_game = total_overs <= 12
    finishing_window = max(2, int(round(total_overs * 0.25)))

    if phase == "powerplay":
        return {
            "strategy": "POWERPLAY ATTACK",
            "target_runs": "10-12" if shortened_game else "9-11",
            "risk_level": "Medium-High" if shortened_game else "Medium",
            "focus": "Use field restrictions and attack loose deliveries",
        }
    if phase == "middle":
        return {
            "strategy": "BUILD PLATFORM",
            "target_runs": "9-11" if shortened_game else "7-9",
            "risk_level": "Medium" if shortened_game else "Low-Medium",
            "focus": f"Preserve wickets and set up the last {finishing_window} overs",
        }
    return {
        "strategy": "DEATH-OVERS MAXIMIZATION",
        "target_runs": "13-16" if shortened_game else "12-15",
        "risk_level": "High",
        "focus": "Target boundary matchups and finish strongly",
    }


def _powerplay_strategy(wickets_down: int, rrr: float) -> Dict[str, str]:
    if wickets_down >= 2:
        return {
            "strategy": "POWERPLAY RECOVERY",
            "target_runs": "8-10",
            "risk_level": "Medium",
            "focus": "Stabilize, avoid another wicket, punish bad balls",
        }
    if rrr > 9.5:
        return {
            "strategy": "POWERPLAY PRESSURE RELEASE",
            "target_runs": "10-12",
            "risk_level": "Medium-High",
            "focus": "Rotate strike and find at least two boundaries",
        }
    return {
        "strategy": "POWERPLAY ATTACK",
        "target_runs": "9-11",
        "risk_level": "Medium",
        "focus": "Capitalize on the infield and keep scoreboard moving",
    }


def _middle_strategy(wickets_down: int, rrr: float) -> Dict[str, str]:
    if wickets_down >= 6:
        return {
            "strategy": "STABILIZE AND SURVIVE",
            "target_runs": "6-8",
            "risk_level": "Low",
            "focus": "Bat deep, reduce dot balls, avoid collapse",
        }
    if rrr > 10:
        return {
            "strategy": "CONTROLLED AGGRESSION",
            "target_runs": "10-12",
            "risk_level": "Medium",
            "focus": "Rotate strike and target one boundary option this over",
        }
    if rrr > 7:
        return {
            "strategy": "BALANCED BUILD",
            "target_runs": "8-10",
            "risk_level": "Low-Medium",
            "focus": "Keep wickets in hand and build toward the finish",
        }
    return {
        "strategy": "LOW-RISK CHASE",
        "target_runs": "7-8",
        "risk_level": "Low",
        "focus": "Singles, twos, and wait for the release ball",
    }


def _death_strategy(rrr: float) -> Dict[str, str]:
    if rrr > 12:
        return {
            "strategy": "ALL-OUT ATTACK",
            "target_runs": "13-16",
            "risk_level": "High",
            "focus": "Take on the weaker matchup and maximize boundaries",
        }
    if rrr > 8:
        return {
            "strategy": "SMART FINISH",
            "target_runs": "10-12",
            "risk_level": "Medium-High",
            "focus": "Prioritize boundary options while keeping one set batter on strike",
        }
    return {
        "strategy": "CALM CLOSE-OUT",
        "target_runs": "7-9",
        "risk_level": "Medium",
        "focus": "Avoid panic, chase with controlled shot selection",
    }


def _bowling_counter_strategy(state: Dict[str, Any]) -> Dict[str, str]:
    phase = state["phase"]
    wickets_in_hand = state.get("wickets_in_hand", 0)
    required_rr = state.get("required_run_rate") or 0

    if phase == "pre-match":
        return {
            "bowling_strategy": "NEW-BALL PRESSURE PLAN",
            "bowling_risk_level": "Medium",
            "bowling_focus": "Use the first over to assess moisture, attack the stumps, and keep a slip in place if there is movement.",
        }

    if phase == "powerplay":
        if wickets_in_hand >= 8:
            return {
                "bowling_strategy": "ATTACK STUMPS EARLY",
                "bowling_risk_level": "Medium-High",
                "bowling_focus": "Use wicket-taking lengths and catching positions before the batters settle.",
            }
        return {
            "bowling_strategy": "KEEP THE SQUEEZE ON",
            "bowling_risk_level": "Medium",
            "bowling_focus": "Mix tight hard lengths with swing and deny easy release shots.",
        }

    if phase == "middle":
        if required_rr > 9:
            return {
                "bowling_strategy": "BOUNDARY DENIAL WITH WICKET THREAT",
                "bowling_risk_level": "Medium",
                "bowling_focus": "Protect straight boundaries, vary pace, and keep one wicket-taking option in play.",
            }
        return {
            "bowling_strategy": "CHOKE THE SINGLES",
            "bowling_risk_level": "Low-Medium",
            "bowling_focus": "Force the batters to manufacture risk by drying up singles and twos.",
        }

    if required_rr > 10:
        return {
            "bowling_strategy": "FULL PRESSURE FINISH",
            "bowling_risk_level": "Medium-High",
            "bowling_focus": "Attack yorkers and wide lines to protect boundaries while hunting miscued big shots.",
        }
    return {
        "bowling_strategy": "DISCIPLINED CLOSE-OUT",
        "bowling_risk_level": "Medium",
        "bowling_focus": "Keep boundary riders alert and force the chase into low-percentage shots.",
    }


def decide_strategy(state: Dict[str, Any]) -> Dict[str, str]:
    phase = state["phase"]
    wickets_down = state["wickets"]
    rrr = state.get("required_run_rate") or 0

    if phase == "pre-match":
        batting_plan = {
            "strategy": "ASSESS CONDITIONS EARLY",
            "target_runs": "8-10",
            "risk_level": "Medium",
            "focus": "Use the first over to read swing and pace before expanding strokeplay.",
        }
    elif state.get("target") is None:
        batting_plan = _first_innings_strategy(phase, total_overs=state.get("total_overs") or 20)
    elif phase == "powerplay":
        batting_plan = _powerplay_strategy(wickets_down, rrr)
    elif phase == "middle":
        batting_plan = _middle_strategy(wickets_down, rrr)
    else:
        batting_plan = _death_strategy(rrr)

    bowling_plan = _bowling_counter_strategy(state)
    matchup = _build_matchup_advice(state)

    if matchup["batting_note"]:
        batting_plan["focus"] = f"{batting_plan['focus']} {matchup['batting_note']}".strip()
    if matchup["bowling_note"]:
        bowling_plan["bowling_focus"] = f"{bowling_plan['bowling_focus']} {matchup['bowling_note']}".strip()

    return {
        **batting_plan,
        **bowling_plan,
        "awareness_notes": matchup["awareness_notes"],
    }


def generate_report(state: Dict[str, Any], plan: Dict[str, str]) -> str:
    probability = state.get("estimated_win_probability")
    bowling_probability = state.get("estimated_bowling_win_probability")
    batting_team = state.get("batting_team", "Team A")
    bowling_team = state.get("bowling_team", "Team B")
    required_rr = state.get("required_run_rate")
    runs_needed = state.get("runs_needed")
    total_overs = int(state.get("total_overs") or 20)
    venue_line = f"\n- Venue: {state['venue']}" if state.get("venue") else ""
    status_line = f"\n- Status: {state['status']}" if state.get("status") else ""
    context_line = f"\n- Match Context: {state.get('match_context')}" if state.get("match_context") else ""
    players_line = ""
    if state.get("striker") or state.get("bowler"):
        players_line = (
            f"\n- Live Matchup: {state.get('striker', 'N/A')} {state.get('striker_score', '')} | "
            f"{state.get('non_striker', 'N/A')} {state.get('non_striker_score', '')} | "
            f"bowler {state.get('bowler', 'N/A')} {state.get('bowler_score', '')}"
        )
    score_line = (
        f"- Score: {state['runs']}/{state['wickets']} in {state['overs']} overs"
        if not state.get("is_pre_match")
        else "- Score: Not started / unavailable yet"
    )
    projected_line = ""
    if state.get("target") is None and state.get("projected_total") is not None:
        projected_line = f"\n- Projected Total: {state.get('projected_total')} (par {state.get('par_score')})"
    batting_win_line = f"- {batting_team} Win Probability: {probability}%"
    bowling_win_line = f"- {bowling_team} Win Probability: {bowling_probability}%"
    awareness_lines = ""
    if plan.get("awareness_notes"):
        awareness_lines = "\n\nKey Awareness\n" + "\n".join(f"- {note}" for note in plan["awareness_notes"])

    return f"""
Match Snapshot
- Batting Team: {state.get('batting_team', 'Unknown')}
- Bowling Team: {state.get('bowling_team', 'Unknown')}{venue_line}{status_line}{context_line}
- Match Length: {total_overs} overs per side{players_line}
{score_line}
- Current Run Rate: {state['current_run_rate']}
- Required Run Rate: {required_rr if required_rr is not None else 'N/A'}
- Runs Needed: {runs_needed if runs_needed is not None else 'N/A'}{projected_line}
- Balls Left: {state['balls_left']}
- Phase: {state['phase']}
{batting_win_line}
{bowling_win_line}

Batting Plan
- Strategy: {plan['strategy']}
- Next Over Target: {plan['target_runs']}
- Risk Level: {plan['risk_level']}
- Focus: {plan['focus']}

Bowling Counter-Plan
- Strategy: {plan.get('bowling_strategy', 'N/A')}
- Risk Level: {plan.get('bowling_risk_level', 'N/A')}
- Focus: {plan.get('bowling_focus', 'N/A')}{awareness_lines}
""".strip()
