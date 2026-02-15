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
- Genres are limited to: House, Tech House, Melodic/Progressive House, Pop EDM, Techno, Hardstyle, Dubstep, Drums & Bass, Trap, Hard Techno, Melodic Dubstep, Riddim, Afro House, Psytrance, Fonk.
- Unknown artists are grouped under `Unknown`.
- Seed data is in `artist-db.js`.
