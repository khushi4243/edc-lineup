import json
import csv
import io
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


def apply_dark_theme() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background: #0b1020;
            color: #e6ecff;
          }
          [data-testid="stHeader"] {
            background: rgba(11, 16, 32, 0.85);
          }
          [data-testid="stToolbar"] {
            right: 1rem;
          }
          h1, h2, h3, p, label, span, div {
            color: #e6ecff;
          }
          .stCaption {
            color: #a4b1d3;
          }
          [data-testid="stTextArea"] textarea {
            background: #0a1025;
            color: #e6ecff;
            border: 1px solid #2b3965;
            border-radius: 8px;
            caret-color: #8e9abb;
          }
          [data-testid="stTextArea"] textarea::placeholder {
            color: #8e9abb;
            opacity: 1;
          }
          [data-testid="stTextArea"] textarea:focus::placeholder {
            color: transparent;
          }
          .stButton > button {
            background: #4c67b2;
            color: white;
            border: 1px solid #4c67b2;
            border-radius: 8px;
            font-weight: 600;
          }
          .stButton > button:hover {
            border-color: #5f79c7;
            background: #5f79c7;
            color: white;
          }
          .stDownloadButton > button {
            color: #0f1730;
          }
          .stDownloadButton > button:hover {
            color: #0f1730;
          }
          [data-testid="stExpander"] {
            background: #0f1730;
            border: 1px solid #2a365e;
            border-radius: 10px;
          }
          [data-testid="stExpander"] details summary {
            background: #ffffff !important;
            border-radius: 8px;
          }
          [data-testid="stExpander"] details[open] summary {
            background: #ffffff !important;
          }
          [data-testid="stExpander"] details summary p {
            color: #0f1730 !important;
            font-weight: 600;
          }
          [data-testid="stExpander"] details summary svg {
            fill: #0f1730 !important;
            color: #0f1730 !important;
          }
          [data-testid="stMarkdownContainer"] ul {
            margin-top: 0.25rem;
          }
          .chip-row {
            margin: 0.5rem 0 0.25rem 0;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
          }
          .chip {
            background: #1f2a4d;
            border: 1px solid #35508f;
            color: #dbe6ff;
            border-radius: 999px;
            padding: 0.2rem 0.6rem;
            font-size: 0.8rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    cleaned = []
    for line in text.splitlines():
        for entry in line.split(","):
            entry = entry.strip()
            entry = re.sub(r"^[•\-*]\s*", "", entry).strip()
            entry = re.sub(r"^[0-9]+\.\s*", "", entry).strip()
            if entry:
                cleaned.append(entry)

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

    columns = st.columns(2)
    for index, genre in enumerate(sorted(grouped.keys(), key=genre_sort_key)):
        records = grouped[genre]
        with columns[index % 2]:
            with st.expander(f"{genre} ({len(records)})", expanded=True):
                for row in records:
                    st.markdown(f"- {row['lineup_entry']}")


def make_csv(records: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["lineup_entry", "matched_artist", "primary_genre", "secondary_genre"],
    )
    writer.writeheader()
    for row in records:
        writer.writerow(row)
    return buffer.getvalue()


def main() -> None:
    st.set_page_config(page_title="Festival Lineup Genre Sorter", layout="wide")
    apply_dark_theme()
    st.title("Festival Lineup Genre Sorter")
    st.caption("Paste lineup text and group artists by primary genre.")

    artist_db = build_artist_db(load_seed_artists())

    if "records" not in st.session_state:
        st.session_state.records = []
    if "grouped" not in st.session_state:
        st.session_state.grouped = {}

    lineup_text = st.text_area("Lineup Text", height=340, placeholder="Paste lineup text here...")
    run = st.button("Group by Genre", type="primary")

    if run:
        entries = parse_lineup_text(lineup_text)
        records = [to_genre_record(entry, artist_db) for entry in entries]
        grouped = group_by_primary_genre(records)
        st.session_state.records = records
        st.session_state.grouped = grouped

    if st.session_state.records:
        records = st.session_state.records
        grouped = st.session_state.grouped
        unknown_count = sum(1 for r in records if r["primary_genre"] == "Unknown")
        matched_count = len(records) - unknown_count
        match_rate = int((matched_count / len(records)) * 100) if records else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Parsed Artists", len(records))
        c2.metric("Matched", matched_count)
        c3.metric("Match Rate", f"{match_rate}%")
        st.progress(match_rate / 100 if records else 0)

        sorted_genres = sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
        top_genres = sorted_genres[:3]
        if top_genres:
            chips = "".join([f"<span class='chip'>{g} ({len(v)})</span>" for g, v in top_genres])
            st.markdown("Top Genres")
            st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)

        genre_options = sorted(grouped.keys(), key=genre_sort_key)
        selected_genres = st.multiselect(
            "Filter Genres",
            options=genre_options,
            default=genre_options,
            help="Show only selected genres in the grouped results.",
        )
        filtered_grouped = {g: grouped[g] for g in selected_genres}

        st.write(f"{len(records)} unique lineup entries parsed. {unknown_count} unmatched (Unknown).")

        st.download_button(
            "Download Results CSV",
            data=make_csv(records),
            file_name="lineup_genre_results.csv",
            mime="text/csv",
        )

        render_grouped_results(filtered_grouped)


if __name__ == "__main__":
    main()
