"""Spotify search normalization and CSV export."""

from __future__ import annotations

import csv
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from Helper_file import DatabaseWriter, SpotifyClient, join_artist_names


HEADERS = {
    "album": ["term", "ranks", "name", "upc", "id", "artist", "Total_Tracks"],
    "artist": ["term", "ranks", "name", "id", "genres", "followers", "popularity"],
    "track": [
        "term",
        "ranks",
        "name",
        "isrc",
        "id",
        "artist",
        "album",
        "release_date",
        "popularity",
    ],
    "similar": ["artist", "artist_id", "ranks", "similar_a", "sim_ID"],
}

_FORMULA_PREFIX = re.compile(r"^\s*[=+\-@]")


def spreadsheet_safe(value: Any) -> Any:
    """Neutralize formula-like strings before writing untrusted API data to CSV."""

    if isinstance(value, str) and _FORMULA_PREFIX.match(value):
        return "'" + value
    return value


def append_csv(
    output_dir: Path, resource_type: str, rows: Sequence[Sequence[Any]]
) -> Path:
    header = HEADERS.get(resource_type)
    if header is None:
        raise ValueError(f"Unsupported CSV resource type: {resource_type}")

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{resource_type}_data.csv"
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if write_header:
            writer.writerow(header)
        writer.writerows(
            [[spreadsheet_safe(value) for value in row] for row in rows]
        )
    return path


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def normalize_search_rows(
    client: SpotifyClient,
    term: str,
    resource_type: str,
    items: Sequence[Mapping[str, Any]],
) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    for rank, item in enumerate(items, start=1):
        if resource_type == "track":
            album = _mapping(item.get("album"))
            external_ids = _mapping(item.get("external_ids"))
            rows.append(
                (
                    term,
                    rank,
                    item.get("name", ""),
                    external_ids.get("isrc"),
                    item.get("id", ""),
                    join_artist_names(item.get("artists", [])),
                    album.get("name", ""),
                    album.get("release_date", ""),
                    item.get("popularity"),
                )
            )
        elif resource_type == "artist":
            followers = _mapping(item.get("followers"))
            genres = item.get("genres", [])
            rows.append(
                (
                    term,
                    rank,
                    item.get("name", ""),
                    item.get("id", ""),
                    ", ".join(str(value) for value in genres)
                    if isinstance(genres, list)
                    else "",
                    followers.get("total"),
                    item.get("popularity"),
                )
            )
        elif resource_type == "album":
            album_id = str(item.get("id", ""))
            upc = client.album_upc(album_id) if album_id else None
            rows.append(
                (
                    term,
                    rank,
                    item.get("name", ""),
                    upc,
                    album_id,
                    join_artist_names(item.get("artists", [])),
                    item.get("total_tracks"),
                )
            )
        else:
            raise ValueError(f"Unsupported Spotify resource type: {resource_type}")
    return rows


def run_searches(
    client: SpotifyClient,
    terms: Sequence[str],
    output_dir: Path,
    *,
    database: DatabaseWriter | None = None,
    limit: int = 5,
) -> dict[str, int]:
    totals = {"track": 0, "artist": 0, "album": 0}
    for term in terms:
        for resource_type in totals:
            items = client.search(term, resource_type, limit=limit)
            rows = normalize_search_rows(client, term, resource_type, items)
            append_csv(output_dir, resource_type, rows)
            if database is not None:
                database.write(resource_type, rows)
            totals[resource_type] += len(rows)
    return totals
