"""CLI entry point for the Elevate Spotify catalog prototype."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

from Helper_file import (
    ConfigurationError,
    DatabaseWriter,
    SpotifyClient,
    SpotifyError,
    env_flag,
    read_terms,
)
from search import run_searches
from similars import run_similar_artists


REPOSITORY_DIR = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect bounded Spotify catalog results into CSV files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=REPOSITORY_DIR / "input.txt",
        help="Search-term file (default: input.txt).",
    )
    parser.add_argument(
        "--artists-input",
        type=Path,
        default=REPOSITORY_DIR / "artists_input.txt",
        help="Related-artist term file (default: artists_input.txt).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_DIR / "output",
        help="Directory for generated CSV files.",
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Also write to MySQL using DB_* environment variables.",
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, int]:
    load_dotenv(REPOSITORY_DIR / ".env")
    client = SpotifyClient.from_environment()
    database = (
        DatabaseWriter.from_environment()
        if args.db or env_flag("DB_ENABLED")
        else None
    )

    terms = read_terms(args.input.resolve())
    artist_terms = read_terms(args.artists_input.resolve())
    totals = run_searches(
        client, terms, args.output_dir.resolve(), database=database, limit=5
    )
    totals["similar"] = run_similar_artists(
        client,
        artist_terms,
        args.output_dir.resolve(),
        database=database,
        limit=5,
    )
    return totals


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        totals = run(args)
    except (ConfigurationError, SpotifyError, RuntimeError, OSError) as exc:
        print(f"Elevate stopped safely: {exc}", file=sys.stderr)
        return 1

    summary = ", ".join(f"{name}={count}" for name, count in totals.items())
    print(f"Completed: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
