# Elevate (Python)

Elevate is a two-person internship prototype created at Anghami in 2024. It
collects bounded Spotify catalog search results for tracks, artists, albums, and
related artists, then writes them to CSV files. Optional MySQL output preserves
the original table contracts.

This repository is a learning and data-collection prototype, not an Anghami
production service. It does not contain Anghami source code, infrastructure, or
customer data.

## Safety changes

- Spotify and MySQL credentials are read only from environment variables.
- Tokens stay in memory and are never written to the repository.
- HTTP requests use connection and response timeouts and validate status/JSON.
- Input size, term count, result count, and related-artist work are bounded.
- CSV cells from external data are neutralized against spreadsheet formulas.
- MySQL is opt-in and uses parameterized batch inserts.

Credentials that were previously committed must still be revoked in their
provider dashboards. Removing them from Git does not make old credentials safe.

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in the local `.env` file.
The file is ignored by Git.

Run the collector:

```powershell
.venv\Scripts\python main.py
```

The default inputs remain `input.txt` and `artists_input.txt`. Generated CSV
files are placed in `output/`. Every search is capped at five results per
term. Use `python main.py --help` for other paths.

## Optional MySQL output

Set `DB_ENABLED=true` and configure the `DB_*` values shown in
`.env.example`, or pass `--db`. The original tables must already exist:
`track`, `artist`, `album`, and `similar_artist`.

## Tests

Tests are offline and do not use real credentials or Spotify:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```
