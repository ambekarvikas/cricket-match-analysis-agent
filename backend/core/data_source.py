from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


CRICBUZZ_BASE_URL = "https://www.cricbuzz.com"
CRICBUZZ_LIVE_URL = f"{CRICBUZZ_BASE_URL}/live-cricket-scores"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
    )
}
TEAM_NAME_BY_SHORT = {
    "CSK": "Chennai Super Kings",
    "DC": "Delhi Capitals",
    "GT": "Gujarat Titans",
    "KKR": "Kolkata Knight Riders",
    "LSG": "Lucknow Super Giants",
    "MI": "Mumbai Indians",
    "PBKS": "Punjab Kings",
    "RCB": "Royal Challengers Bengaluru",
    "RR": "Rajasthan Royals",
    "SRH": "Sunrisers Hyderabad",
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

SAMPLE_MATCHES = {
    "chase_pressure": {
        "batting_team": "India",
        "bowling_team": "Australia",
        "innings": 2,
        "runs": 140,
        "wickets": 4,
        "overs": 15.0,
        "target": 180,
        "striker": "Set Batter",
        "non_striker": "Support Batter",
        "bowler": "Fast Bowler",
    },
    "powerplay_trouble": {
        "batting_team": "South Africa",
        "bowling_team": "England",
        "innings": 2,
        "runs": 25,
        "wickets": 2,
        "overs": 3.4,
        "target": 180,
        "striker": "Aggressive Opener",
        "non_striker": "Stabilizer",
        "bowler": "Swing Bowler",
    },
    "death_chase": {
        "batting_team": "New Zealand",
        "bowling_team": "Pakistan",
        "innings": 2,
        "runs": 168,
        "wickets": 5,
        "overs": 18.2,
        "target": 191,
        "striker": "Finisher 1",
        "non_striker": "Finisher 2",
        "bowler": "Death Specialist",
    },
}


TEAM_SCORE_PATTERN = re.compile(
    r"(?P<team>[A-Za-z][A-Za-z\s\-'&]+?)\s+"
    r"(?P<short>[A-Z]{2,5})\s+"
    r"(?P<score>\d{1,3}-\d{1,2}\s*\(\d+(?:\.\d+)?\))"
)
TEAM_SHORT_PATTERN = re.compile(r"(?P<team>[A-Za-z][A-Za-z\s\-'&]+?)\s+(?P<short>[A-Z]{2,5})\b")


def get_hardcoded_match_state(scenario: str = "chase_pressure") -> Dict[str, Any]:
    if scenario not in SAMPLE_MATCHES:
        available = ", ".join(SAMPLE_MATCHES.keys())
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from: {available}")
    return dict(SAMPLE_MATCHES[scenario])


_ALLOWED_PREFIX = "https://www.cricbuzz.com/"


def _fetch_html(url: str) -> str:
    if not url.startswith(_ALLOWED_PREFIX):
        raise ValueError(f"Blocked request to disallowed URL: {url!r}")
    safe_url = url
    request = Request(safe_url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "ignore")


def _clean_text(raw: str) -> str:
    from html.parser import HTMLParser

    class _StripScripts(HTMLParser):
        """Remove <script> and <style> blocks; collect other text."""

        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self._skip = False
            self._parts: List[str] = []

        def handle_starttag(self, tag: str, attrs: Any) -> None:
            if tag in ("script", "style"):
                self._skip = True

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style"):
                self._skip = False

        def handle_data(self, data: str) -> None:
            if not self._skip:
                self._parts.append(data)

        def get_text(self) -> str:
            return " ".join(self._parts)

    parser = _StripScripts()
    parser.feed(raw)
    return re.sub(r"\s+", " ", parser.get_text()).strip()


def _extract_match_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    url_match = re.search(r"/live-cricket-scores/(\d+)/", value)
    if url_match:
        return url_match.group(1)

    id_match = re.search(r"\b(\d{5,})\b", value)
    if id_match:
        return id_match.group(1)

    return None


def _extract_match_url(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    url_match = re.search(r"https?://www\.cricbuzz\.com/live-cricket-scores/\d+/[\w\-]+", value)
    if url_match:
        return url_match.group(0)

    match_id = _extract_match_id(value)
    if match_id:
        return f"{CRICBUZZ_BASE_URL}/live-cricket-scores/{match_id}"

    return None


def _extract_fixture_teams_from_url(match_url: str) -> List[str]:
    match = re.search(r"/live-cricket-scores/\d+/([a-z0-9]+)-vs-([a-z0-9]+)-", match_url)
    if not match:
        return []

    team_a, team_b = match.groups()
    return [
        TEAM_NAME_BY_SLUG.get(team_a, team_a.upper()),
        TEAM_NAME_BY_SLUG.get(team_b, team_b.upper()),
    ]


def _normalize_team_name(name: str) -> str:
    normalized = _clean_text(name.replace("-", " "))
    return " ".join(part if part.isupper() else part.capitalize() for part in normalized.split())


def _build_pre_match_state(match_url: str, venue: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    fixture_teams = _extract_fixture_teams_from_url(match_url)
    first_team = fixture_teams[0] if len(fixture_teams) >= 1 else "Team A"
    second_team = fixture_teams[1] if len(fixture_teams) >= 2 else "Team B"

    return {
        "match_id": _extract_match_id(match_url),
        "match_description": None,
        "venue": venue,
        "batting_team": first_team,
        "bowling_team": second_team,
        "innings": 0,
        "runs": 0,
        "wickets": 0,
        "overs": 0.0,
        "target": None,
        "status": status or "Pre-match / score unavailable",
        "source": "cricbuzz",
        "source_url": match_url,
        "is_pre_match": True,
    }


def _extract_rain_overs_context(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    total_overs = None
    note = None
    for pattern in (
        r"(\d+)\s+overs?\s+game\s+due\s+to\s+rain",
        r"(\d+)\s+overs?\s+game",
        r"reduced\s+to\s+(\d+)\s+overs?",
        r"(\d+)\s+overs?\s+per\s+side",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            total_overs = int(match.group(1))
            note = match.group(0).strip()
            break

    wet_outfield_match = re.search(r"(wet outfield|rain delay|delayed due to rain|toss delayed due to wet outfield)", text, re.IGNORECASE)
    if wet_outfield_match:
        note = f"{note}. {wet_outfield_match.group(1).strip()}" if note else wet_outfield_match.group(1).strip()

    context: Dict[str, Any] = {}
    if total_overs:
        context["total_overs"] = total_overs
    if note:
        context["conditions_note"] = note
    return context


def _extract_live_player_context(html_text: str) -> Dict[str, Any]:
    context: Dict[str, Any] = {}
    patterns = {
        "striker": r'batStrikerObj.*?playerName\\?":\\?"([^"\\]+).*?playerScore\\?":\\?"([^"\\]+)',
        "non_striker": r'batNonStrikerObj.*?playerName\\?":\\?"([^"\\]+).*?playerScore\\?":\\?"([^"\\]+)',
        "bowler": r'bowlerObj.*?playerName\\?":\\?"([^"\\]+).*?playerScore\\?":\\?"([^"\\]+)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        context[key] = match.group(1).strip()
        context[f"{key}_score"] = match.group(2).strip()

    return context


def _parse_score_fragment(score_fragment: str) -> Dict[str, Any]:
    match = re.search(r"(\d{1,3})-(\d{1,2})\s*\((\d+(?:\.\d+)?)\)", score_fragment)
    if not match:
        raise ValueError(f"Could not parse score fragment: {score_fragment}")

    runs, wickets, overs = match.groups()
    return {
        "runs": int(runs),
        "wickets": int(wickets),
        "overs": float(overs),
    }


def _extract_series_section(page_text: str, series_hint: Optional[str]) -> str:
    if not series_hint:
        return ""

    section_match = re.search(
        rf"{re.escape(series_hint)}\s+\d{{4}}(?P<section>.*?)(?=(?:[A-Z][A-Za-z'\-\s]+\d{{4}})|Home|Menu)",
        page_text,
        re.IGNORECASE,
    )
    if not section_match:
        return ""
    return section_match.group("section")


def _extract_match_cards(html_text: str, series_hint: Optional[str]) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    seen_urls = set()
    page_text = _clean_text(html_text)
    series_section = _extract_series_section(page_text, series_hint)
    anchor_pattern = re.compile(
        r'<a[^>]+href="(?P<url>/live-cricket-scores/\d+/[^"]+)"[^>]*>(?P<label>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    for match in anchor_pattern.finditer(html_text):
        url = urljoin(CRICBUZZ_BASE_URL, match.group("url"))
        if url in seen_urls:
            continue

        label = _clean_text(match.group("label"))
        if "match" not in label.lower():
            continue
        if series_section and label not in series_section:
            continue

        cards.append({"url": url, "label": label})
        seen_urls.add(url)

    return cards


def _parse_match_card(card: Dict[str, str]) -> Dict[str, Any]:
    label = card["label"]
    url = card["url"]

    match_description = None
    venue = None
    header_match = re.search(r"(?P<desc>.+?Match)\s+•\s+(?P<tail>.+)", label)
    if header_match:
        match_description = header_match.group("desc").strip()
        tail = header_match.group("tail")
        score_or_status_match = re.search(r"([A-Za-z][A-Za-z\s\-'&]+\s+[A-Z]{2,5}\s+\d{1,3}-\d{1,2}\s*\(|Delay|Preview|No result|Abandoned|Interrupted)", tail)
        if score_or_status_match:
            venue = tail[:score_or_status_match.start()].strip()

    score_entries = []
    for match in TEAM_SCORE_PATTERN.finditer(label):
        parsed_score = _parse_score_fragment(match.group("score"))
        short_code = match.group("short")
        team_name = TEAM_NAME_BY_SHORT.get(short_code, _normalize_team_name(match.group("team")))
        score_entries.append(
            {
                "team": team_name,
                "short": short_code,
                "span": match.span(),
                **parsed_score,
            }
        )

    rain_context = _extract_rain_overs_context(label)

    if not score_entries:
        prematch_state = _build_pre_match_state(url, venue=venue, status=label)
        prematch_state["match_description"] = match_description
        prematch_state.update(rain_context)
        return prematch_state

    current = score_entries[-1]
    bowling_team = "Unknown"

    if len(score_entries) >= 2:
        bowling_team = score_entries[0]["team"]
    else:
        trailing_text = label[current["span"][1]:]
        other_team_match = TEAM_SHORT_PATTERN.search(trailing_text)
        if other_team_match:
            short_code = other_team_match.group("short")
            bowling_team = TEAM_NAME_BY_SHORT.get(short_code, _normalize_team_name(other_team_match.group("team")))

    target = None
    innings = 1

    if len(score_entries) >= 2:
        target = score_entries[0]["runs"] + 1
        innings = 2
    else:
        need_match = re.search(r"need\s+(\d+)\s+runs?", label, re.IGNORECASE)
        if need_match:
            target = current["runs"] + int(need_match.group(1))
            innings = 2

    if header_match:
        tail = header_match.group("tail")
        first_team_name = score_entries[0]["team"]
        first_short = score_entries[0]["short"]
        split_token = f"{first_team_name} {first_short}"
        if split_token in tail:
            venue = tail.split(split_token, 1)[0].strip()

    parsed = {
        "match_id": _extract_match_id(url),
        "match_description": match_description,
        "venue": venue,
        "batting_team": current["team"],
        "bowling_team": bowling_team,
        "innings": innings,
        "runs": current["runs"],
        "wickets": current["wickets"],
        "overs": current["overs"],
        "target": target,
        "status": label,
        "source": "cricbuzz",
        "source_url": url,
    }
    parsed.update(rain_context)
    return parsed


def list_live_matches_from_cricbuzz(series_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        html_text = _fetch_html(CRICBUZZ_LIVE_URL)
        cards = _extract_match_cards(html_text, series_hint)
    except (URLError, TimeoutError) as exc:
        raise ConnectionError(f"Could not fetch Cricbuzz live scores: {exc}") from exc

    live_matches: List[Dict[str, Any]] = []
    for card in cards:
        try:
            live_matches.append(_parse_match_card(card))
        except ValueError:
            continue

    return live_matches


def _parse_direct_match_page(match_url: str) -> Dict[str, Any]:
    html_text = _fetch_html(match_url)
    page_text = _clean_text(html_text)
    fixture_teams = _extract_fixture_teams_from_url(match_url)
    rain_context = _extract_rain_overs_context(page_text) | _extract_rain_overs_context(html_text)
    player_context = _extract_live_player_context(html_text)

    score_match = re.search(
        r"Follow [^\"]*?\b([A-Z]{2,5})\s+(\d{1,3})[/-](\d{1,2})\s*\((\d+(?:\.\d+)?)\)",
        html_text,
        re.IGNORECASE,
    )
    if not score_match:
        score_match = re.search(
            r"\b([A-Z]{2,5})\s+(\d{1,3})[/-](\d{1,2})\s*\((\d+(?:\.\d+)?)\)",
            html_text,
            re.IGNORECASE,
        )

    venue_match = re.search(r"Venue:\s*(.*?)\s*Date\s*&\s*Time:", page_text, re.IGNORECASE)
    rich_status_match = re.search(
        r"(\d+\s+overs?\s+game\s+due\s+to\s+rain|toss\s+delayed\s+due\s+to\s+wet\s+outfield|Delay|Preview|No result \(due to rain\)|Interrupted|Match abandoned|Abandoned|Delayed)",
        page_text,
        re.IGNORECASE,
    )
    status_text = rich_status_match.group(1).strip() if rich_status_match else page_text[:180]

    if not score_match:
        first_team = fixture_teams[0] if len(fixture_teams) >= 1 else "Team A"
        second_team = fixture_teams[1] if len(fixture_teams) >= 2 else "Team B"
        prematch_state = {
            "match_id": _extract_match_id(match_url),
            "match_description": None,
            "venue": venue_match.group(1).strip() if venue_match else None,
            "batting_team": first_team,
            "bowling_team": second_team,
            "innings": 0,
            "runs": 0,
            "wickets": 0,
            "overs": 0.0,
            "target": None,
            "status": status_text,
            "source": "cricbuzz",
            "source_url": match_url,
            "is_pre_match": True,
        }
        prematch_state.update(rain_context)
        prematch_state.update(player_context)
        return prematch_state

    batting_short, runs, wickets, overs = score_match.groups()
    if status_text.lower() == "preview":
        status_text = rain_context.get("conditions_note") or f"Live: {runs}/{wickets} after {overs} overs"
    batting_team = TEAM_NAME_BY_SHORT.get(batting_short, batting_short)

    if len(fixture_teams) == 2 and batting_team == fixture_teams[0]:
        bowling_team = fixture_teams[1]
    elif len(fixture_teams) == 2 and batting_team == fixture_teams[1]:
        bowling_team = fixture_teams[0]
    else:
        bowling_team = fixture_teams[1] if len(fixture_teams) == 2 else "Unknown"

    need_match = re.search(r"need\s+(\d+)\s+runs?\s+in\s+(\d+)\s+balls", page_text, re.IGNORECASE)

    target = None
    innings = 1
    if need_match:
        target = int(runs) + int(need_match.group(1))
        innings = 2

    parsed = {
        "match_id": _extract_match_id(match_url),
        "match_description": None,
        "venue": venue_match.group(1).strip() if venue_match else None,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "innings": innings,
        "runs": int(runs),
        "wickets": int(wickets),
        "overs": float(overs),
        "target": target,
        "status": status_text,
        "source": "cricbuzz",
        "source_url": match_url,
        "is_pre_match": False,
    }
    parsed.update(rain_context)
    parsed.update(player_context)
    return parsed


def get_live_match_state_from_cricbuzz(match_reference: Optional[str] = None) -> Dict[str, Any]:
    direct_url = _extract_match_url(match_reference)
    if direct_url:
        try:
            return _parse_direct_match_page(direct_url)
        except Exception:
            pass

    live_matches = list_live_matches_from_cricbuzz()

    if not live_matches and direct_url:
        return _parse_direct_match_page(direct_url)
    if not live_matches:
        raise ValueError("No live cricket matches could be detected from Cricbuzz right now.")

    selected_match = None
    match_id = _extract_match_id(match_reference)

    if match_id:
        selected_match = next((match for match in live_matches if match.get("match_id") == match_id), None)

    if selected_match is None and match_reference:
        needle = match_reference.lower()
        selected_match = next(
            (
                match
                for match in live_matches
                if needle in match.get("batting_team", "").lower()
                or needle in match.get("bowling_team", "").lower()
                or needle in match.get("status", "").lower()
            ),
            None,
        )

    if selected_match is None and direct_url:
        return _parse_direct_match_page(direct_url)
    if selected_match is None:
        selected_match = live_matches[0]

    selected_url = selected_match.get("source_url")
    if selected_url:
        try:
            direct_state = _parse_direct_match_page(selected_url)
            merged_state = dict(selected_match)
            merged_state.update({key: value for key, value in direct_state.items() if value not in (None, "", [])})
            return merged_state
        except Exception:
            pass

    return dict(selected_match)
