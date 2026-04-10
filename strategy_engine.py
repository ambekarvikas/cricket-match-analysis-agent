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


def _status_has_result(status_text: str) -> bool:
    return any(token in status_text for token in ("won by", "beat ", "beats ", "match tied", "tied match", "no result", "abandoned"))


def _status_has_innings_break(status_text: str) -> bool:
    return any(token in status_text for token in ("innings break", "end of innings", "after 20 overs"))


def _build_upcoming_phase_note(state: Dict[str, Any]) -> str:
    phase = state.get("phase")
    total_overs = float(state.get("total_overs") or 20)
    balls_bowled = int(state.get("balls_bowled") or 0)
    powerplay_limit = max(2.0, round(total_overs * 0.30, 1))
    death_start = max(powerplay_limit + 2.0, round(total_overs * 0.75, 1))

    if phase == "completed":
        return state.get("result_summary") or "Match complete — no further live tactical action remains."
    if phase == "innings-break":
        return "Innings break: the fielding side should plan its first two overs of the chase and protect the straight boundary early."
    if phase == "powerplay":
        powerplay_balls_left = max(int(powerplay_limit * 6) - balls_bowled, 0)
        return f"Powerplay pressure window is still open for {powerplay_balls_left} more balls, so early momentum swings are high-value."
    if phase == "middle":
        death_balls_away = max(int(death_start * 6) - balls_bowled, 0)
        return f"The middle overs are about squeezing or building before the death phase begins in roughly {death_balls_away} balls."
    return "The death phase is live, so every ball should be treated as a boundary or wicket event."


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
    balls_bowled = overs_to_balls(enriched["overs"])
    if total_overs * 6 < balls_bowled:
        total_overs = max(20.0, float(int(enriched.get("overs") or 0) + 1))
    total_balls = int(total_overs * 6)
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
    enriched["current_run_rate"] = calculate_current_rr(enriched["runs"], enriched["overs"])
    enriched["wickets_in_hand"] = max(10 - enriched["wickets"], 0)

    target = enriched.get("target")
    if target is not None:
        runs_needed = max(target - enriched["runs"], 0)
        enriched["runs_needed"] = runs_needed
        enriched["required_run_rate"] = calculate_required_rr(runs_needed, balls_left)
    else:
        enriched["runs_needed"] = None
        enriched["required_run_rate"] = None

    innings_complete = balls_bowled >= total_balls or enriched.get("wickets", 0) >= 10 or _status_has_innings_break(status_text)
    match_complete = _status_has_result(status_text)
    if target is not None and enriched.get("runs_needed") is not None:
        if enriched["runs_needed"] <= 0 or balls_left <= 0:
            innings_complete = True
            match_complete = True

    if innings_complete or match_complete:
        balls_left = 0

    enriched["balls_left"] = balls_left
    enriched["overs_left"] = balls_to_overs(balls_left)
    enriched["is_innings_complete"] = bool(innings_complete)
    enriched["is_match_complete"] = bool(match_complete)
    enriched["result_summary"] = (
        enriched.get("status") if match_complete else "Innings complete — the chase setup is now clear." if innings_complete and target is None else None
    )

    if is_pre_match:
        enriched["phase"] = "pre-match"
    elif match_complete:
        enriched["phase"] = "completed"
    elif innings_complete and target is None:
        enriched["phase"] = "innings-break"
    else:
        enriched["phase"] = get_phase(enriched["overs"], total_overs=total_overs)

    base_context = (
        f"Rain-shortened to {int(total_overs)} overs per side. {conditions_note}".strip()
        if total_overs != 20
        else (conditions_note.strip() or "Standard 20-over match")
    )
    if match_complete and enriched.get("result_summary"):
        enriched["match_context"] = f"{base_context} Result: {enriched['result_summary']}"
    elif innings_complete and target is None:
        enriched["match_context"] = f"{base_context} First innings complete — chase preparation phase."
    else:
        enriched["match_context"] = base_context
    enriched["upcoming_phase_note"] = _build_upcoming_phase_note(enriched)

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
    """Heuristic win probability for pre-match, first-innings, chase, and completed states."""
    if state.get("is_pre_match"):
        return 50

    if state.get("is_match_complete"):
        status_text = str(state.get("status", "")).lower()
        batting_team = str(state.get("batting_team", "")).lower()
        bowling_team = str(state.get("bowling_team", "")).lower()
        if state.get("target") is not None:
            return 99 if (state.get("runs_needed") or 0) <= 0 else 1
        if batting_team and batting_team in status_text and "won by" in status_text:
            return 99
        if bowling_team and bowling_team in status_text and "won by" in status_text:
            return 1
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


def _summarize_current_batter(state: Dict[str, Any]) -> str:
    striker = state.get("striker")
    striker_score = state.get("striker_score")
    if not striker or not striker_score:
        return ""

    runs, balls, strike_rate = _parse_batter_score(striker_score)
    if balls <= 0:
        return ""
    if balls <= 6:
        return f"{striker} is still new at {runs}({balls}), so the next few balls should test his early scoring options and temperament."
    if strike_rate >= 170:
        return f"{striker} is dominating at {runs}({balls}) with a strike rate of {strike_rate:.0f}, so the batting side should maximize his exposure against the weaker matchup."
    if strike_rate <= 110:
        return f"{striker} is below tempo at {runs}({balls}), so strike rotation or a change in matchup is needed quickly."
    return f"{striker} is reasonably set at {runs}({balls}), which gives the batting side a stable anchor for the next phase."


def _summarize_current_bowler(state: Dict[str, Any]) -> str:
    bowler = state.get("bowler")
    bowler_score = state.get("bowler_score")
    if not bowler or not bowler_score:
        return ""

    overs_bowled, _, wickets, economy = _parse_bowler_figures(bowler_score)
    if overs_bowled <= 0:
        return ""
    if wickets >= 1 and economy <= 8:
        return f"{bowler} is controlling the contest at {bowler_score}, so the field should stay attacking around his wicket-taking length."
    if economy >= 10:
        return f"{bowler} is leaking {economy:.1f} an over at {bowler_score}, so the captain should change pace profile, line, or boundary-side protection immediately."
    return f"{bowler} has mixed returns at {bowler_score}, so his next plan should be guided by the current batter matchup rather than a fixed template."


def _build_detailed_tactics(state: Dict[str, Any]) -> Dict[str, Any]:
    batting_tactics: list[str] = []
    bowling_tactics: list[str] = []
    phase_watchouts: list[str] = []
    matchup_insights: list[str] = []

    phase = state.get("phase")
    runs_needed = state.get("runs_needed")
    rrr = state.get("required_run_rate") or 0
    wickets_in_hand = state.get("wickets_in_hand") or 0

    if phase == "completed":
        phase_watchouts.append(state.get("result_summary") or "Match complete.")
        batting_tactics.append("No further live batting action remains; review which over or partnership decided the result.")
        bowling_tactics.append("No further live bowling action remains; review which spell created or lost scoreboard pressure.")
    elif phase == "innings-break":
        batting_tactics.append("The batting side should review which scoring zones produced the boundary overs and which risks cost wickets.")
        bowling_tactics.append("The fielding side should plan the first two overs of the chase and hold back its best death bowler for the finish.")
        phase_watchouts.append(f"The first innings has ended at {state.get('runs')}; par for this match length is around {state.get('par_score')}.")
    elif phase == "powerplay":
        batting_tactics.extend([
            "Keep one attacking batter on strike for at least four of the next six balls.",
            "Target width and overpitched pace, but avoid gifting a wicket to the best new-ball bowler.",
        ])
        bowling_tactics.extend([
            "Attack the top of off stump and keep at least one catching option in front of the wicket while the ball is hard.",
            "If swing disappears, switch to wobble-seam or hard lengths rather than feeding slot balls.",
        ])
        phase_watchouts.append("Field restrictions are still active, so one loose over can shift the game quickly.")
    elif phase == "middle":
        batting_tactics.extend([
            "Treat the next over as a platform over: one safe boundary option plus hard-run twos is enough.",
            "Avoid back-to-back dot balls that push the chase into a boundary-only equation.",
        ])
        bowling_tactics.extend([
            "Dry up the easy single to force a riskier release shot against the longer side of the ground.",
            "Use spin or cutters into the pitch if the set batter is lining up pace-on deliveries.",
        ])
        phase_watchouts.append("The middle overs decide whether the death overs begin with control or panic.")
    else:
        batting_tactics.extend([
            "Make sure the best finisher faces as many of the next six balls as possible.",
            "Target one side of the ground and commit to the boundary options there rather than swinging at everything.",
        ])
        bowling_tactics.extend([
            "Miss full and wide rather than length in the slot, and force the batter to hit square of the wicket.",
            "Protect the shorter side and keep one yorker or slower-ball option ready every over.",
        ])
        phase_watchouts.append("In the death overs, every ball should be treated as either a boundary chance or a wicket chance.")

    if runs_needed is not None and phase not in {"completed", "innings-break"}:
        if rrr >= 12:
            batting_tactics.append("The asking rate is now extreme, so the batting side must pre-identify the bowler and ball to attack rather than waiting passively.")
            bowling_tactics.append("The chase is under severe pressure, so protect the obvious boundary zones and force low-percentage power shots.")
        elif rrr <= 7 and wickets_in_hand >= 5:
            batting_tactics.append("The chase is under control if wickets are preserved; there is no need for a reckless over.")
            bowling_tactics.append("Even with a moderate asking rate, one wicket can reopen the match immediately.")

    batter_insight = _summarize_current_batter(state)
    bowler_insight = _summarize_current_bowler(state)
    if batter_insight:
        matchup_insights.append(batter_insight)
    if bowler_insight:
        matchup_insights.append(bowler_insight)

    return {
        "batting_tactics": batting_tactics,
        "bowling_tactics": bowling_tactics,
        "phase_watchouts": phase_watchouts,
        "matchup_insights": matchup_insights,
        "current_batter_insight": batter_insight,
        "current_bowler_insight": bowler_insight,
    }


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


def _build_decision_recommendation(state: Dict[str, Any]) -> Dict[str, Any]:
    phase = state.get("phase")
    rrr = state.get("required_run_rate") or 0
    wickets_in_hand = state.get("wickets_in_hand") or 0

    if phase == "completed":
        return {
            "recommended_action": "Review the decisive over, spell, and partnership rather than forcing a live recommendation.",
            "bowling_recommended_action": "Review where scoreboard pressure was created or released.",
            "decision_window": "post-match review",
            "priority": "closed",
            "decision_rationale": [state.get("result_summary") or "The result is already decided."],
            "avoid_now": ["No live tactical intervention remains."],
        }

    if phase == "innings-break":
        return {
            "recommended_action": "Use the break to map the first two overs of the chase and decide which matchup to target first.",
            "bowling_recommended_action": "Start with your highest-control bowler and save one premium death over for the finish.",
            "decision_window": "first 2 overs after restart",
            "priority": "high",
            "decision_rationale": [
                f"The innings has ended at {state.get('runs')}, so the next phase is about chase setup rather than live repair.",
                f"Par for this match length is around {state.get('par_score')}.",
            ],
            "avoid_now": ["Do not enter the chase without a clear first-over plan.", "Do not burn all death resources too early."],
        }

    if state.get("target") is not None:
        if rrr >= 12:
            return {
                "recommended_action": "Attack one pre-identified over immediately and keep the set batter on strike for most of the next six balls.",
                "bowling_recommended_action": "Use your best boundary-denial bowler now and crowd the strongest hitting arc.",
                "decision_window": "next 6 balls",
                "priority": "urgent",
                "decision_rationale": [
                    f"The asking rate is {rrr}, so the chase cannot drift for even one quiet over.",
                    "The batting side must choose where to attack rather than waiting for a release ball.",
                ],
                "avoid_now": ["Do not allow two low-scoring overs in a row.", "Do not expose a new batter unnecessarily."],
            }
        if wickets_in_hand <= 3:
            return {
                "recommended_action": "Prioritize strike rotation and one boundary option, because another wicket would end the chase.",
                "bowling_recommended_action": "Keep the stumps in play and force the tail to hit against the larger boundary.",
                "decision_window": "next over",
                "priority": "high",
                "decision_rationale": [
                    f"Only {wickets_in_hand} wickets remain, so survival and tempo must be balanced carefully.",
                ],
                "avoid_now": ["Do not turn every ball into a boundary attempt."],
            }
        if phase == "powerplay":
            return {
                "recommended_action": "Use the field restrictions now, but keep one stable batter in reserve for the middle overs.",
                "bowling_recommended_action": "Attack the top of off and keep one catching option active while the ball is hard.",
                "decision_window": "powerplay",
                "priority": "high",
                "decision_rationale": ["Field restrictions make this the easiest scoring window of the chase."],
                "avoid_now": ["Do not waste the powerplay with only singles."],
            }
        if phase == "death":
            return {
                "recommended_action": "Let the best finisher face the majority of the next over and commit to one side of the ground.",
                "bowling_recommended_action": "Miss wide and full, not in the slot, and protect the shorter boundary first.",
                "decision_window": "next 6-12 balls",
                "priority": "urgent",
                "decision_rationale": ["The death overs reward clarity and punish hesitation."],
                "avoid_now": ["Do not spread the strike randomly if a set finisher is in."],
            }
        return {
            "recommended_action": "Use the next over as a platform over: rotate hard and target one calculated boundary option.",
            "bowling_recommended_action": "Dry up the easy single and force the release shot to the longer side.",
            "decision_window": "next over",
            "priority": "balanced",
            "decision_rationale": ["The chase is still live, but momentum can flip with one smart over."],
            "avoid_now": ["Do not let dot-ball pressure stack up."],
        }

    if phase == "powerplay":
        return {
            "recommended_action": "Press the powerplay advantage with controlled intent and keep one aggressive batter exposed.",
            "bowling_recommended_action": "Hunt a wicket before the platform settles by attacking the corridor around off stump.",
            "decision_window": "next 2 overs",
            "priority": "high",
            "decision_rationale": ["Powerplay overs set the ceiling for the rest of the innings."],
            "avoid_now": ["Do not burn wickets chasing low-value shots."],
        }
    if phase == "death":
        return {
            "recommended_action": "Maximize boundary matchups and make sure the best finisher gets most of the strike.",
            "bowling_recommended_action": "Protect yorker execution and slower-ball variation over pure pace-on length.",
            "decision_window": "final overs",
            "priority": "urgent",
            "decision_rationale": ["This is the highest-value scoring window of the innings."],
            "avoid_now": ["Do not leave your best hitter stranded off strike."],
        }

    return {
        "recommended_action": "Build through the next over without letting dot-ball pressure slow the innings down.",
        "bowling_recommended_action": "Control the middle overs by denying easy singles and changing pace profile when needed.",
        "decision_window": "next over",
        "priority": "balanced",
        "decision_rationale": ["The middle phase decides whether the finish begins with control or panic."],
        "avoid_now": ["Do not allow the game to drift into a passive pattern."],
    }


def decide_strategy(state: Dict[str, Any]) -> Dict[str, Any]:
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
    elif phase == "completed":
        batting_plan = {
            "strategy": "MATCH COMPLETE",
            "target_runs": "N/A",
            "risk_level": "None",
            "focus": state.get("result_summary") or "The match has ended, so the focus shifts to what decided the result.",
        }
    elif phase == "innings-break":
        batting_plan = {
            "strategy": "INNINGS BREAK RESET",
            "target_runs": "N/A",
            "risk_level": "Low",
            "focus": "Use the break to map the chase or defence plan with clear matchup priorities for the first two overs.",
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
    detail_pack = _build_detailed_tactics(state)
    decision_pack = _build_decision_recommendation(state)

    if matchup["batting_note"]:
        batting_plan["focus"] = f"{batting_plan['focus']} {matchup['batting_note']}".strip()
    if matchup["bowling_note"]:
        bowling_plan["bowling_focus"] = f"{bowling_plan['bowling_focus']} {matchup['bowling_note']}".strip()

    return {
        **batting_plan,
        **bowling_plan,
        "awareness_notes": matchup["awareness_notes"],
        **detail_pack,
        **decision_pack,
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

    detail_lines = ""
    if plan.get("recommended_action"):
        detail_lines += f"\n\nDecision Recommendation\n- Batting: {plan['recommended_action']}"
    if plan.get("bowling_recommended_action"):
        detail_lines += f"\n- Bowling: {plan['bowling_recommended_action']}"
    if plan.get("decision_window"):
        detail_lines += f"\n- Window: {plan['decision_window']} | Priority: {plan.get('priority', 'balanced')}"
    if state.get("upcoming_phase_note"):
        detail_lines += f"\n\nUpcoming Phase\n- {state['upcoming_phase_note']}"
    if plan.get("current_batter_insight"):
        detail_lines += f"\n\nCurrent Batter Insight\n- {plan['current_batter_insight']}"
    if plan.get("current_bowler_insight"):
        detail_lines += f"\n\nCurrent Bowler Insight\n- {plan['current_bowler_insight']}"
    if plan.get("batting_tactics"):
        detail_lines += "\n\nBatting Tactics\n" + "\n".join(f"- {note}" for note in plan["batting_tactics"])
    if plan.get("bowling_tactics"):
        detail_lines += "\n\nBowling Tactics\n" + "\n".join(f"- {note}" for note in plan["bowling_tactics"])
    if plan.get("phase_watchouts"):
        detail_lines += "\n\nPhase Watchouts\n" + "\n".join(f"- {note}" for note in plan["phase_watchouts"])

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
- Focus: {plan.get('bowling_focus', 'N/A')}{awareness_lines}{detail_lines}
""".strip()
