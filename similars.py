"""Finite related-artist collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from Helper_file import DatabaseWriter, SpotifyClient
from search import append_csv


def related_rows(
    client: SpotifyClient, artist_name: str, *, limit: int = 5
) -> list[tuple[Any, ...]]:
    artist_id = client.artist_id(artist_name)
    if not artist_id:
        return []
    related = client.related_artists(artist_id, limit=limit)
    return [
        (
            artist_name,
            artist_id,
            rank,
            item.get("name", ""),
            item.get("id", ""),
        )
        for rank, item in enumerate(related, start=1)
    ]


def run_similar_artists(
    client: SpotifyClient,
    artists: Sequence[str],
    output_dir: Path,
    *,
    database: DatabaseWriter | None = None,
    limit: int = 5,
) -> int:
    total = 0
    for artist_name in artists:
        rows = related_rows(client, artist_name, limit=limit)
        append_csv(output_dir, "similar", rows)
        if database is not None:
            database.write("similar", rows)
        total += len(rows)
    return total
