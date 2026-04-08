from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
    )
}
TEAM_NAME_BY_SLUG = {
    "csk": "Chennai Super Kings",
    "dc": "Delhi Capitals",
    "gt": "Gujarat Titans",
    "kkr": "Kolkata Knight Riders",
    "lsg": "Lucknow Super Giants",
    "mi": "Mumbai Indians",
    "pbks": "Punjab Kings",
    "rcb": "Royal Challengers Bengaluru",
    "rr": "Rajasthan Royals",
    "srh": "Sunrisers Hyderabad",
}
PLAYER_ROLE_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z .'-]*?(?:\s+\((?:C|WK)\))?)\s+"
    r"(WK-Batter|Batter|Bowler|Batting Allrounder|Bowling Allrounder|Allrounder)"
)
SPINNER_NAMES = {
    "sunil narine",
    "varun chakaravarthy",
    "ravi bishnoi",
    "yuzvendra chahal",
    "mitchell santner",
    "mayank markande",
    "kuldeep yadav",
    "axar patel",
    "ravindra jadeja",
    "anukul roy",
}
TEAM_SELECTION_PRIORITIES = {
    "Kolkata Knight Riders": [
        "Finn Allen", "Sunil Narine", "Ajinkya Rahane (C)", "Angkrish Raghuvanshi (WK)", "Rinku Singh",
        "Rovman Powell", "Cameron Green", "Ramandeep Singh", "Varun Chakaravarthy", "Vaibhav Arora",
        "Kartik Tyagi", "Navdeep Saini", "Anukul Roy", "Tim Seifert", "Rachin Ravindra",
    ],
    "Punjab Kings": [
        "Prabhsimran Singh (WK)", "Shreyas Iyer (C)", "Nehal Wadhera", "Shashank Singh", "Marcus Stoinis",
        "Marco Jansen", "Cooper Connolly", "Arshdeep Singh", "Xavier Bartlett", "Yuzvendra Chahal",
        "Vijaykumar Vyshak", "Priyansh Arya",
    ],
    "Rajasthan Royals": [
        "Yashasvi Jaiswal", "Dhruv Jurel (WK)", "Riyan Parag (C)", "Shimron Hetmyer", "Donovan Ferreira",
        "Ravindra Jadeja", "Jofra Archer", "Nandre Burger", "Sandeep Sharma", "Ravi Bishnoi",
        "Tushar Deshpande", "Dasun Shanaka", "Shubham Dubey", "Adam Milne",
    ],
    "Mumbai Indians": [
        "Ryan Rickelton (WK)", "Rohit Sharma", "Suryakumar Yadav (C)", "Tilak Varma", "Hardik Pandya",
        "Will Jacks", "Naman Dhir", "Mitchell Santner", "Deepak Chahar", "Jasprit Bumrah", "Trent Boult",
        "Shardul Thakur", "Sherfane Rutherford", "Corbin Bosch",
    ],
    "Delhi Capitals": [
        "KL Rahul", "Abishek Porel", "Faf du Plessis", "Tristan Stubbs", "Axar Patel", "Ashutosh Sharma",
        "Kuldeep Yadav", "Mitchell Starc", "Mukesh Kumar", "T Natarajan", "Vipraj Nigam",
    ],
    "Lucknow Super Giants": [
        "Aiden Markram", "Mitchell Marsh", "Nicholas Pooran", "Rishabh Pant", "Ayush Badoni", "David Miller",
        "Abdul Samad", "Shardul Thakur", "Avesh Khan", "Prince Yadav", "Digvesh Rathi",
    ],
}


def _fetch_html(url: str) -> str:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "ignore")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _build_squads_url(state: Dict[str, Any]) -> Optional[str]:
    source_url = state.get("source_url")
    if not source_url:
        return None
    return source_url.replace("/live-cricket-scores/", "/cricket-match-squads/")


def _extract_fixture_teams(source_url: Optional[str]) -> List[str]:
    if not source_url:
        return []

    match = re.search(r"/(?:live-cricket-scores|cricket-match-squads)/\d+/([a-z0-9]+)-vs-([a-z0-9]+)-", source_url)
    if not match:
        return []

    team_a, team_b = match.groups()
    return [TEAM_NAME_BY_SLUG.get(team_a, team_a.upper()), TEAM_NAME_BY_SLUG.get(team_b, team_b.upper())]


def _extract_playing_xi_from_squads_page(squads_url: str, team_names: List[str]) -> Dict[str, Any]:
    try:
        raw_html = _fetch_html(squads_url)
    except (URLError, TimeoutError):
        return {"lineup_type": "Unavailable", "teams": {}}

    cleaned_page = _clean_text(re.sub(r"<[^>]+>", " ", raw_html))
    section_match = re.search(r"Playing XI (?P<section>.*?)(?:Substitutes|Bench)", cleaned_page, re.IGNORECASE)
    if not section_match:
        return {"lineup_type": "Unavailable", "teams": {}}

    cleaned_names = [_clean_text(name) for name in PLAYER_ROLE_PATTERN.findall(section_match.group("section")) if _clean_text(name)]

    if len(cleaned_names) < 22:
        return {"lineup_type": "Unavailable", "teams": {}}

    first_team = team_names[0] if len(team_names) >= 1 else "Team 1"
    second_team = team_names[1] if len(team_names) >= 2 else "Team 2"

    return {
        "lineup_type": "Confirmed Playing XI",
        "teams": {
            first_team: cleaned_names[:11],
            second_team: cleaned_names[11:22],
        },
        "source_url": squads_url,
    }


def recommend_toss_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    status_text = (state.get("status") or "").lower()
    venue_text = (state.get("venue") or "").lower()
    reasons: List[str] = []

    rain_risk = any(token in status_text for token in ("rain", "drizzle", "interrupted", "wet", "delayed", "abandoned"))
    dew_factor = any(token in venue_text for token in ("eden gardens", "wankhede", "chinnaswamy"))

    if rain_risk:
        reasons.append("rain threat and a shortened game usually make chasing safer under DLS pressure")
    if dew_factor:
        reasons.append("the venue can get wetter later, which often helps the chasing side and makes gripping the ball harder")

    if rain_risk or dew_factor:
        decision = "BOWL FIRST"
        confidence = "High" if rain_risk else "Medium-High"
    else:
        decision = "BOWL FIRST"
        confidence = "Medium"
        reasons.append("T20 captains generally prefer having scoreboard clarity in a chase")

    summary = f"If the toss happens under these conditions, the captain should usually {decision.lower()}"
    return {
        "decision": decision,
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
    }


def _extract_relevant_squad_text(cleaned_page: str) -> str:
    candidates = [idx for idx in (cleaned_page.find("Playing XI"), cleaned_page.find(" Squad ")) if idx != -1]
    start = min(candidates) if candidates else 0

    end_candidates = [idx for idx in (cleaned_page.find("Support Staff", start), cleaned_page.find("Menu", start)) if idx != -1]
    end = min(end_candidates) if end_candidates else len(cleaned_page)
    return cleaned_page[start:end]


def _split_players_by_team(flat_players: List[Dict[str, str]], team_names: List[str]) -> Dict[str, List[Dict[str, str]]]:
    if len(team_names) < 2:
        return {team_names[0] if team_names else "Team": flat_players}

    first_team, second_team = team_names[0], team_names[1]
    second_team_hints = set(TEAM_SELECTION_PRIORITIES.get(second_team, []))

    split_index = None
    for idx, player in enumerate(flat_players):
        if idx >= 8 and player["name"] in second_team_hints:
            split_index = idx
            break

    if split_index is None:
        split_index = len(flat_players) // 2

    return {
        first_team: flat_players[:split_index],
        second_team: flat_players[split_index:],
    }


def _extract_full_squad_pool(state: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    squads_url = _build_squads_url(state)
    team_names = _extract_fixture_teams(squads_url or state.get("source_url"))

    if not squads_url:
        return {}

    try:
        raw_html = _fetch_html(squads_url)
    except (URLError, TimeoutError):
        return {}

    cleaned_page = _clean_text(re.sub(r"<[^>]+>", " ", raw_html))
    relevant_text = _extract_relevant_squad_text(cleaned_page)
    flat_players = [
        {"name": _clean_text(name), "role": role}
        for name, role in PLAYER_ROLE_PATTERN.findall(relevant_text)
    ]

    if len(flat_players) < 10:
        return {}

    return _split_players_by_team(flat_players, team_names)


def _is_spinner(player_name: str) -> bool:
    return player_name.lower() in SPINNER_NAMES


def _player_rank_score(player: Dict[str, str], priority_map: Dict[str, int], rain_bias: bool) -> tuple:
    role = player["role"]
    name = player["name"]
    base = 100 - priority_map.get(name, 80)

    if "WK" in role:
        base += 12
    if "Allrounder" in role:
        base += 10
    if "Bowler" in role:
        base += 8
    if rain_bias and ("Bowler" in role or "Allrounder" in role):
        base += 8 if not _is_spinner(name) else -3

    return (base, -priority_map.get(name, 80), name)


def _rank_players(team_name: str, players: List[Dict[str, str]], rain_bias: bool) -> List[Dict[str, str]]:
    priority_map = {name: idx for idx, name in enumerate(TEAM_SELECTION_PRIORITIES.get(team_name, []))}

    unique_players = []
    seen = set()
    for player in players:
        if player["name"] not in seen:
            unique_players.append(player)
            seen.add(player["name"])

    return sorted(
        unique_players,
        key=lambda player: _player_rank_score(player, priority_map, rain_bias),
        reverse=True,
    )


def _pick_first(candidates: List[Dict[str, str]], selected_names: set) -> Optional[Dict[str, str]]:
    for player in candidates:
        if player["name"] not in selected_names:
            return player
    return None


def _build_agent_recommended_xi(team_name: str, players: List[Dict[str, str]], state: Dict[str, Any]) -> List[str]:
    rain_bias = any(token in str(state.get("status", "")).lower() for token in ("rain", "delay", "wet", "drizzle"))
    ranked = _rank_players(team_name, players, rain_bias)

    keepers = [player for player in ranked if "WK" in player["role"]]
    batters = [player for player in ranked if player["role"] in {"Batter", "WK-Batter"}]
    allrounders = [player for player in ranked if "Allrounder" in player["role"]]
    bowlers = [player for player in ranked if "Bowler" in player["role"] or "Allrounder" in player["role"]]
    seamers = [player for player in bowlers if not _is_spinner(player["name"])]
    spinners = [player for player in bowlers if _is_spinner(player["name"])]

    selected: List[str] = []
    selected_names = set()

    def add_player(player: Optional[Dict[str, str]]) -> None:
        if player and player["name"] not in selected_names and len(selected) < 11:
            selected.append(player["name"])
            selected_names.add(player["name"])

    add_player(_pick_first(keepers, selected_names))
    for player in batters[:4]:
        add_player(player)
    for player in allrounders[:2]:
        add_player(player)

    preferred_bowlers = seamers[:3] + spinners[:1] if rain_bias else seamers[:2] + spinners[:2]
    for player in preferred_bowlers:
        add_player(player)

    for player in ranked:
        add_player(player)
        if len(selected) == 11:
            break

    return selected[:11]


def _build_selection_reasoning(state: Dict[str, Any]) -> List[str]:
    reasons = ["the XI is chosen for role balance: keeper, top-order stability, all-round cover, and multiple bowling options"]
    status_text = str(state.get("status", "")).lower()
    if any(token in status_text for token in ("rain", "delay", "wet", "drizzle")):
        reasons.append("rain or delay risk pushes the agent toward extra seam and stronger chasing flexibility")
    if state.get("venue"):
        reasons.append(f"venue conditions at {state['venue']} are factored into the combination")
    return reasons


def _build_comparison_notes(recommended: Dict[str, List[str]], announced: Dict[str, List[str]]) -> Dict[str, List[str]]:
    notes: Dict[str, List[str]] = {}
    for team_name, recommended_xi in recommended.items():
        announced_xi = announced.get(team_name, [])
        if not announced_xi:
            continue

        to_add = [player for player in recommended_xi if player not in announced_xi]
        to_remove = [player for player in announced_xi if player not in recommended_xi]
        if to_add or to_remove:
            notes[team_name] = []
            if to_add:
                notes[team_name].append(f"Agent would bring in: {', '.join(to_add)}")
            if to_remove:
                notes[team_name].append(f"Agent would leave out: {', '.join(to_remove)}")
    return notes


def get_probable_playing_xi(state: Dict[str, Any]) -> Dict[str, Any]:
    squads_url = _build_squads_url(state)
    team_names = _extract_fixture_teams(squads_url or state.get("source_url"))

    if squads_url:
        xi_info = _extract_playing_xi_from_squads_page(squads_url, team_names)
        if xi_info.get("teams"):
            return xi_info

    batting_team = state.get("batting_team", "Batting Team")
    bowling_team = state.get("bowling_team", "Bowling Team")
    return {
        "lineup_type": "Announced XI unavailable from source",
        "teams": {
            batting_team: [],
            bowling_team: [],
        },
        "source_url": squads_url,
    }


def get_agent_recommended_xi(state: Dict[str, Any], announced_lineup: Dict[str, Any]) -> Dict[str, Any]:
    squad_pool = _extract_full_squad_pool(state)
    team_names = list((announced_lineup.get("teams") or {}).keys())

    if not team_names:
        team_names = [state.get("batting_team", "Batting Team"), state.get("bowling_team", "Bowling Team")]

    recommended_teams: Dict[str, List[str]] = {}
    for team_name in team_names:
        players = squad_pool.get(team_name, [])
        if not players:
            fallback_names = announced_lineup.get("teams", {}).get(team_name, [])
            players = [{"name": name, "role": "Batter"} for name in fallback_names]
        recommended_teams[team_name] = _build_agent_recommended_xi(team_name, players, state) if players else []

    return {
        "lineup_type": "Agent Recommended XI",
        "teams": recommended_teams,
        "reasoning": _build_selection_reasoning(state),
        "comparison_notes": _build_comparison_notes(recommended_teams, announced_lineup.get("teams", {})),
    }


def build_pre_match_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    toss = recommend_toss_decision(state)
    lineup = get_probable_playing_xi(state)
    recommended_xi = get_agent_recommended_xi(state, lineup)
    return {
        "toss": toss,
        "recommended_xi": recommended_xi,
        "lineup": lineup,
    }
