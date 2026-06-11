#!/usr/bin/env python3
"""Download and normalize starter data for the FIFA World Cup 2026 predictor."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PyPDF2 import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

SOURCES = {
    "fifa_schedule_pdf": {
        "url": "https://digitalhub.fifa.com/m/1be9ce37eb98fcc5/original/FWC26-Match-Schedule_English.pdf",
        "path": RAW_DIR / "fifa" / "FWC26-Match-Schedule_English.pdf",
        "description": "Official FIFA World Cup 2026 match schedule PDF.",
    },
    "fifa_squad_pdf": {
        "url": "https://fdp.fifa.org/assetspublic/ce281/pdf/SquadLists-English.pdf",
        "path": RAW_DIR / "fifa" / "SquadLists-English.pdf",
        "description": "Official FIFA World Cup 2026 squad lists PDF.",
    },
    "openfootball_2026_json": {
        "url": "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
        "path": RAW_DIR / "openfootball" / "worldcup_2026.json",
        "description": "Public-domain structured 2026 World Cup schedule.",
    },
}

HISTORICAL_YEARS = [
    1930,
    1934,
    1938,
    1950,
    1954,
    1958,
    1962,
    1966,
    1970,
    1974,
    1978,
    1982,
    1986,
    1990,
    1994,
    1998,
    2002,
    2006,
    2010,
    2014,
    2018,
    2022,
]

TEAM_CODE_FIXES = {
    "AL G": "ALG",
    "CÔT": "CIV",
    "COT": "CIV",
    "CZE": "CZE",
}

COUNTRY_CODES = {
    "Algeria": "ALG",
    "Argentina": "ARG",
    "Australia": "AUS",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Bosnia & Herzegovina": "BIH",
    "Brazil": "BRA",
    "Canada": "CAN",
    "Cape Verde": "CPV",
    "Colombia": "COL",
    "Costa Rica": "CRC",
    "Croatia": "CRO",
    "Curaçao": "CUW",
    "Czech Republic": "CZE",
    "DR Congo": "COD",
    "Denmark": "DEN",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Ghana": "GHA",
    "Haiti": "HAI",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Ivory Coast": "CIV",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Norway": "NOR",
    "Panama": "PAN",
    "Paraguay": "PAR",
    "Portugal": "POR",
    "Qatar": "QAT",
    "Saudi Arabia": "KSA",
    "Scotland": "SCO",
    "Senegal": "SEN",
    "South Africa": "RSA",
    "South Korea": "KOR",
    "Spain": "ESP",
    "Sweden": "SWE",
    "Switzerland": "SUI",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Ukraine": "UKR",
    "United States": "USA",
    "Uruguay": "URU",
    "Uzbekistan": "UZB",
}

TEAM_NAME_FIXES = {
    "Côte D'Ivoire": "Ivory Coast",
    "Côte d’Ivoire": "Ivory Coast",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
    "USA": "United States",
    "Congo DR": "DR Congo",
}

NATIONALITY_SUFFIXES = sorted(
    {
        *COUNTRY_CODES,
        "Czech Republic",
        "Côte D'Ivoire",
        "Korea Republic",
        "Türkiye",
        "United States",
    },
    key=len,
    reverse=True,
)


@dataclass
class DownloadedSource:
    name: str
    url: str
    path: Path
    description: str
    sha256: str
    bytes: int


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "world-cup-predictor-data/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_kickoff_utc(date_text: str, time_text: str) -> str:
    match = re.fullmatch(r"(\d{2}):(\d{2}) UTC([+-]\d{1,2})", time_text)
    if not match:
        return ""
    hour, minute, offset_hours = match.groups()
    local_tz = timezone(timedelta(hours=int(offset_hours)))
    local_dt = datetime(
        int(date_text[:4]),
        int(date_text[5:7]),
        int(date_text[8:10]),
        int(hour),
        int(minute),
        tzinfo=local_tz,
    )
    return local_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_2026_schedule() -> list[dict]:
    data = json.loads(SOURCES["openfootball_2026_json"]["path"].read_text(encoding="utf-8"))
    rows = []
    for index, match in enumerate(data["matches"], start=1):
        row = {
            "match_id": match.get("num") or index,
            "round": match.get("round", ""),
            "date": match.get("date", ""),
            "time": match.get("time", ""),
            "kickoff_utc": parse_kickoff_utc(match.get("date", ""), match.get("time", "")),
            "group": match.get("group", ""),
            "team1": normalize_team_name(match.get("team1", "")),
            "team2": normalize_team_name(match.get("team2", "")),
            "team1_code": COUNTRY_CODES.get(normalize_team_name(match.get("team1", "")), ""),
            "team2_code": COUNTRY_CODES.get(normalize_team_name(match.get("team2", "")), ""),
            "ground": match.get("ground", ""),
            "source": "openfootball_2026_json",
        }
        rows.append(row)
    return rows


def normalize_team_name(name: str) -> str:
    return TEAM_NAME_FIXES.get(name, name)


def parse_team_header(text: str) -> tuple[str, str]:
    for line in text.splitlines():
        stripped = line.strip()
        match = re.fullmatch(r"(.+?) \(([A-Z ]{3,5})\)", stripped)
        if match:
            name = normalize_team_name(match.group(1).strip())
            code = match.group(2).strip()
            code = TEAM_CODE_FIXES.get(code, code.replace(" ", ""))
            return name, code
    raise ValueError("Could not find team header in squad page")


def clean_pdf_text(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())


def parse_squad_pdf() -> tuple[list[dict], list[dict]]:
    reader = PdfReader(str(SOURCES["fifa_squad_pdf"]["path"]))
    players: list[dict] = []
    coaches: list[dict] = []
    player_pattern = re.compile(
        r"^(GK|DF|MF|FW)(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d{2,3})\s+(\d+)\s+(\d+)$"
    )

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        team_name, team_code = parse_team_header(text)
        roster_index = 0
        for raw_line in text.splitlines():
            line = clean_pdf_text(raw_line)
            player_match = player_pattern.match(line)
            if player_match:
                roster_index += 1
                position, name_block, dob, club, height, caps, goals = player_match.groups()
                players.append(
                    {
                        "team": team_name,
                        "team_code": team_code,
                        "roster_index": roster_index,
                        "position": position,
                        "name_block": clean_pdf_text(name_block),
                        "dob": dob,
                        "club": clean_pdf_text(club),
                        "height_cm": int(height),
                        "caps": int(caps),
                        "goals": int(goals),
                        "source_page": page_number,
                        "source": "fifa_squad_pdf",
                    }
                )
                continue

            if line.startswith("Head coach "):
                coach_block, nationality = parse_coach_line(line)
                coaches.append(
                    {
                        "team": team_name,
                        "team_code": team_code,
                        "coach_block": clean_pdf_text(coach_block),
                        "coach_nationality": clean_pdf_text(nationality),
                        "source_page": page_number,
                        "source": "fifa_squad_pdf",
                    }
                )

    return players, coaches


def parse_coach_line(line: str) -> tuple[str, str]:
    details = line.removeprefix("Head coach ").strip()
    for suffix in NATIONALITY_SUFFIXES:
        if details.endswith(f" {suffix}"):
            return details[: -len(suffix)].strip(), normalize_team_name(suffix)
    parts = details.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return details, ""


def build_teams(schedule: list[dict], players: list[dict], coaches: list[dict]) -> list[dict]:
    groups_by_team: dict[str, str] = {}
    for match in schedule:
        if match["group"]:
            groups_by_team[match["team1"]] = match["group"].replace("Group ", "")
            groups_by_team[match["team2"]] = match["group"].replace("Group ", "")

    roster_sizes: dict[str, int] = {}
    for player in players:
        roster_sizes[player["team"]] = roster_sizes.get(player["team"], 0) + 1

    coaches_by_team = {coach["team"]: coach for coach in coaches}
    team_names = sorted(groups_by_team)
    rows = []
    for team_name in team_names:
        coach = coaches_by_team.get(team_name, {})
        rows.append(
            {
                "team": team_name,
                "team_code": COUNTRY_CODES.get(team_name, ""),
                "group": groups_by_team.get(team_name, ""),
                "roster_size": roster_sizes.get(team_name, 0),
                "coach_block": coach.get("coach_block", ""),
                "coach_nationality": coach.get("coach_nationality", ""),
            }
        )
    return rows


def build_ground_summary(schedule: list[dict]) -> list[dict]:
    summary: dict[str, dict] = {}
    for match in schedule:
        ground = match["ground"]
        current = summary.setdefault(
            ground,
            {"ground": ground, "match_count": 0, "group_stage_count": 0, "knockout_count": 0},
        )
        current["match_count"] += 1
        if match["group"]:
            current["group_stage_count"] += 1
        else:
            current["knockout_count"] += 1
    return sorted(summary.values(), key=lambda row: (-row["match_count"], row["ground"]))


def download_historical_worldcups(sources: list[DownloadedSource]) -> None:
    for year in HISTORICAL_YEARS:
        url = f"https://raw.githubusercontent.com/openfootball/worldcup.json/master/{year}/worldcup.json"
        path = RAW_DIR / "openfootball" / "history" / f"worldcup_{year}.json"
        try:
            download(url, path)
        except Exception as exc:
            print(f"warning: could not download historical World Cup {year}: {exc}", file=sys.stderr)
            continue
        sources.append(
            DownloadedSource(
                name=f"openfootball_worldcup_{year}_json",
                url=url,
                path=path,
                description=f"Public-domain structured FIFA World Cup {year} match data.",
                sha256=sha256(path),
                bytes=path.stat().st_size,
            )
        )


def main() -> int:
    downloaded_sources: list[DownloadedSource] = []
    for name, source in SOURCES.items():
        download(str(source["url"]), source["path"])
        downloaded_sources.append(
            DownloadedSource(
                name=name,
                url=str(source["url"]),
                path=source["path"],
                description=str(source["description"]),
                sha256=sha256(source["path"]),
                bytes=source["path"].stat().st_size,
            )
        )

    download_historical_worldcups(downloaded_sources)

    schedule = load_2026_schedule()
    players, coaches = parse_squad_pdf()
    teams = build_teams(schedule, players, coaches)
    grounds = build_ground_summary(schedule)

    write_csv(PROCESSED_DIR / "schedule_2026.csv", schedule)
    write_json(PROCESSED_DIR / "schedule_2026.json", schedule)
    write_csv(PROCESSED_DIR / "teams_2026.csv", teams)
    write_json(PROCESSED_DIR / "teams_2026.json", teams)
    write_csv(PROCESSED_DIR / "players_2026.csv", players)
    write_json(PROCESSED_DIR / "players_2026.json", players)
    write_csv(PROCESSED_DIR / "coaches_2026.csv", coaches)
    write_csv(PROCESSED_DIR / "grounds_2026.csv", grounds)

    source_rows = [
        {
            "name": source.name,
            "url": source.url,
            "local_path": str(source.path.relative_to(ROOT)),
            "description": source.description,
            "sha256": source.sha256,
            "bytes": source.bytes,
        }
        for source in downloaded_sources
    ]
    write_csv(PROCESSED_DIR / "sources.csv", source_rows)
    write_json(PROCESSED_DIR / "sources.json", source_rows)

    print(f"schedule rows: {len(schedule)}")
    print(f"team rows: {len(teams)}")
    print(f"player rows: {len(players)}")
    print(f"coach rows: {len(coaches)}")
    print(f"ground rows: {len(grounds)}")
    print(f"sources: {len(source_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
