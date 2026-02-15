# Festival Lineup Genre Sorter

Simple local web app that:

- accepts pasted festival lineup text
- parses artist entries from bullet/plain text
- matches artists to a seeded local genre database
- groups lineup entries by **primary genre**

## Run

From the project folder:

```bash
cd /Users/khushipatel/edc-lineup
python3 -m http.server 8080
```

Then open:

`http://localhost:8080`

## Notes

- Input is paste-only (no file upload).
- Genres include required categories: Dubstep, Tech House, Techno, Bass House, Melodic/Progressive House, Hardstyle, DnB, Riddim.
- Unknown artists are grouped under `Unknown`.
- Seed data is in `artist-db.js`.
