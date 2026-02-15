const REQUIRED_GENRES = [
  "Dubstep",
  "Tech House",
  "Techno",
  "Bass House",
  "Melodic/Progressive House",
  "Hardstyle",
  "DnB",
  "Riddim"
];

const GENRE_PRIORITY = [
  ...REQUIRED_GENRES,
  "Trance",
  "Psytrance",
  "Melodic Bass",
  "Bass Music",
  "UK Garage/Bassline",
  "House",
  "Afro House",
  "Pop EDM",
  "Unknown"
];

const inputEl = document.getElementById("lineup-input");
const parseBtn = document.getElementById("parse-btn");
const clearBtn = document.getElementById("clear-btn");
const statsEl = document.getElementById("stats");
const resultsEl = document.getElementById("results");

const artistDb = buildArtistDb(window.SEED_ARTISTS || []);

parseBtn.addEventListener("click", () => {
  const raw = inputEl.value;
  const entries = parseLineupText(raw);
  const enriched = entries.map(toGenreRecord);
  const grouped = groupByPrimaryGenre(enriched);
  renderStats(enriched);
  renderResults(grouped);
});

clearBtn.addEventListener("click", () => {
  inputEl.value = "";
  statsEl.innerHTML = "";
  resultsEl.innerHTML = "";
});

function normalizeKey(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\u00d8/g, "O")
    .replace(/\u00f8/g, "o")
    .replace(/\u00c6/g, "AE")
    .replace(/\u00e6/g, "ae")
    .replace(/\u0152/g, "OE")
    .replace(/\u0153/g, "oe")
    .toUpperCase()
    .replace(/[^A-Z0-9&+/\-'.:\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function stripSetMeta(value) {
  return value
    .replace(/\(.*?\)/g, "")
    .replace(/\s+WITH\s+MC\s+.+$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function parseLineupText(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const cleaned = lines
    .map((line) => line.replace(/^[\u2022\-*]\s*/, "").trim())
    .map((line) => line.replace(/^[0-9]+\.\s*/, "").trim())
    .filter(Boolean);

  const unique = new Set();
  return cleaned.filter((line) => {
    const key = normalizeKey(line);
    if (!key || unique.has(key)) {
      return false;
    }
    unique.add(key);
    return true;
  });
}

function buildArtistDb(seedArtists) {
  const map = new Map();
  for (const artist of seedArtists) {
    const key = normalizeKey(artist.name);
    if (!key) continue;
    map.set(key, {
      name: artist.name,
      primary_genre: artist.primary_genre,
      secondary_genre: artist.secondary_genre || null
    });
  }
  return map;
}

function toGenreRecord(entry) {
  const baseName = stripSetMeta(entry);
  const match =
    lookupArtist(baseName) ||
    lookupFromCollab(baseName) || {
      name: baseName,
      primary_genre: "Unknown",
      secondary_genre: null
    };

  return {
    lineup_entry: entry,
    matched_artist: match.name,
    primary_genre: match.primary_genre,
    secondary_genre: match.secondary_genre
  };
}

function lookupArtist(name) {
  const direct = artistDb.get(normalizeKey(name));
  if (direct) return direct;

  const withoutThe = name.replace(/^THE\s+/i, "");
  if (withoutThe !== name) {
    const fromWithoutThe = artistDb.get(normalizeKey(withoutThe));
    if (fromWithoutThe) return fromWithoutThe;
  }

  return null;
}

function lookupFromCollab(value) {
  const pieces = value
    .split(/\s+B2B\s+|\s+X\s+|,\s*|\/|\s+VS\.?\s+|\s+AND\s+/i)
    .map((part) => part.trim())
    .filter(Boolean);

  for (const piece of pieces) {
    const found = lookupArtist(piece);
    if (found) return found;
  }

  return null;
}

function groupByPrimaryGenre(records) {
  const grouped = {};
  for (const record of records) {
    const key = record.primary_genre || "Unknown";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(record);
  }

  for (const genre of Object.keys(grouped)) {
    grouped[genre].sort((a, b) => a.lineup_entry.localeCompare(b.lineup_entry));
  }

  return grouped;
}

function genreSort(a, b) {
  const aIndex = GENRE_PRIORITY.indexOf(a);
  const bIndex = GENRE_PRIORITY.indexOf(b);

  if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
  if (aIndex === -1) return 1;
  if (bIndex === -1) return -1;
  return aIndex - bIndex;
}

function renderStats(records) {
  const unknownCount = records.filter((r) => r.primary_genre === "Unknown").length;
  statsEl.textContent = `${records.length} unique lineup entries parsed. ${unknownCount} unmatched (Unknown).`;
}

function renderResults(grouped) {
  resultsEl.innerHTML = "";
  const genres = Object.keys(grouped).sort(genreSort);

  if (!genres.length) {
    resultsEl.innerHTML = "<p>No artists found.</p>";
    return;
  }

  for (const genre of genres) {
    const records = grouped[genre];
    const card = document.createElement("article");
    card.className = "genre-card";

    const title = document.createElement("h3");
    title.className = "genre-title";
    title.innerHTML = `${genre} <span class="count">${records.length}</span>`;
    card.appendChild(title);

    const list = document.createElement("ul");
    list.className = "artist-list";

    for (const item of records) {
      const row = document.createElement("li");
      row.className = "artist-item";
      row.textContent = item.lineup_entry;
      list.appendChild(row);
    }

    card.appendChild(list);
    resultsEl.appendChild(card);
  }
}
