import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import streamlit as st

GENRE_PRIORITY = [
    "House",
    "Tech House",
    "Melodic/Progressive House",
    "Pop EDM",
    "Techno",
    "Hardstyle",
    "Dubstep",
    "Drums & Bass",
    "Trap",
    "Hard Techno",
    "Melodic Dubstep",
    "Riddim",
    "Afro House",
    "Psytrance",
    "Fonk",
    "Unknown",
]


def load_seed_artists() -> list[dict]:
    data_path = Path(__file__).parent / "seed_artists.json"
    return json.loads(data_path.read_text(encoding="utf-8"))


def normalize_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    stripped = (
        stripped.replace("Ø", "O")
        .replace("ø", "o")
        .replace("Æ", "AE")
        .replace("æ", "ae")
        .replace("Œ", "OE")
        .replace("œ", "oe")
    )
    stripped = re.sub(r"[^A-Za-z0-9&+/\-'.:\s]", "", stripped.upper())
    return re.sub(r"\s+", " ", stripped).strip()


def strip_set_meta(value: str) -> str:
    value = re.sub(r"\(.*?\)", "", value)
    value = re.sub(r"\s+WITH\s+MC\s+.+$", "", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def parse_lineup_text(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    cleaned = []
    for line in lines:
        line = re.sub(r"^[•\-*]\s*", "", line).strip()
        line = re.sub(r"^[0-9]+\.\s*", "", line).strip()
        if line:
            cleaned.append(line)

    unique_entries = []
    seen = set()
    for line in cleaned:
        key = normalize_key(line)
        if key and key not in seen:
            seen.add(key)
            unique_entries.append(line)
    return unique_entries


def build_artist_db(seed_artists: list[dict]) -> dict[str, dict]:
    db: dict[str, dict] = {}
    for artist in seed_artists:
        key = normalize_key(artist["name"])
        if not key:
            continue
        db[key] = {
            "name": artist["name"],
            "primary_genre": artist["primary_genre"],
            "secondary_genre": artist.get("secondary_genre"),
        }
    return db


def lookup_artist(name: str, artist_db: dict[str, dict]) -> dict | None:
    direct = artist_db.get(normalize_key(name))
    if direct:
        return direct

    without_the = re.sub(r"^THE\s+", "", name, flags=re.IGNORECASE)
    if without_the != name:
        return artist_db.get(normalize_key(without_the))
    return None


def lookup_from_collab(value: str, artist_db: dict[str, dict]) -> dict | None:
    parts = re.split(r"\s+B2B\s+|\s+X\s+|,\s*|/|\s+VS\.?\s+|\s+AND\s+", value, flags=re.IGNORECASE)
    for part in (p.strip() for p in parts if p.strip()):
        found = lookup_artist(part, artist_db)
        if found:
            return found
    return None


def to_genre_record(entry: str, artist_db: dict[str, dict]) -> dict:
    base_name = strip_set_meta(entry)
    match = lookup_artist(base_name, artist_db) or lookup_from_collab(base_name, artist_db)

    if not match:
        match = {
            "name": base_name,
            "primary_genre": "Unknown",
            "secondary_genre": None,
        }

    return {
        "lineup_entry": entry,
        "matched_artist": match["name"],
        "primary_genre": match["primary_genre"],
        "secondary_genre": match.get("secondary_genre"),
    }


def group_by_primary_genre(records: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record.get("primary_genre") or "Unknown"].append(record)

    for genre in grouped:
        grouped[genre].sort(key=lambda r: r["lineup_entry"])
    return dict(grouped)


def genre_sort_key(genre: str) -> tuple[int, str]:
    if genre in GENRE_PRIORITY:
        return (GENRE_PRIORITY.index(genre), genre)
    return (999, genre)


def render_grouped_results(grouped: dict[str, list[dict]]) -> None:
    if not grouped:
        st.info("No artists found.")
        return

    for genre in sorted(grouped.keys(), key=genre_sort_key):
        records = grouped[genre]
        with st.expander(f"{genre} ({len(records)})", expanded=True):
            for row in records:
                st.markdown(f"- {row['lineup_entry']}")


def main() -> None:
    st.set_page_config(page_title="Festival Lineup Genre Sorter", layout="wide")
    st.title("Festival Lineup Genre Sorter")
    st.caption("Paste lineup text and group artists by primary genre.")

    artist_db = build_artist_db(load_seed_artists())

    lineup_text = st.text_area("Lineup Text", height=340, placeholder="Paste lineup text here...")
    run = st.button("Group by Genre", type="primary")

    if run:
        entries = parse_lineup_text(lineup_text)
        records = [to_genre_record(entry, artist_db) for entry in entries]
        grouped = group_by_primary_genre(records)
        unknown_count = sum(1 for r in records if r["primary_genre"] == "Unknown")
        st.write(f"{len(records)} unique lineup entries parsed. {unknown_count} unmatched (Unknown).")
        render_grouped_results(grouped)


if __name__ == "__main__":
    main()
