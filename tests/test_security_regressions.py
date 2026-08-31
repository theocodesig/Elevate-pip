from __future__ import annotations

import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Helper_file import (
    ConfigurationError,
    SpotifyClient,
    TokenCache,
    read_terms,
)
from search import append_csv, spreadsheet_safe
from similars import run_similar_artists
from main import build_parser


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class TokenSession:
    def __init__(self):
        self.calls = 0

    def post(self, *_args, **kwargs):
        self.calls += 1
        self.last_timeout = kwargs.get("timeout")
        self.last_allow_redirects = kwargs.get("allow_redirects")
        return FakeResponse(
            {"access_token": f"token-{self.calls}", "expires_in": 120}
        )


class StaticTokenCache:
    def get_token(self):
        return "token"


class SearchSession:
    def get(self, *_args, **kwargs):
        self.allow_redirects = kwargs.get("allow_redirects")
        return FakeResponse(
            {
                "tracks": {
                    "items": [
                        {"id": str(index)} for index in range(10)
                    ]
                }
            }
        )


class FakeCatalog:
    def __init__(self):
        self.related_calls = 0

    def artist_id(self, artist_name):
        return f"id-{artist_name}"

    def related_artists(self, artist_id, limit=5):
        self.related_calls += 1
        return [
            {"name": f"related-{index}", "id": f"{artist_id}-{index}"}
            for index in range(limit)
        ]


class SecurityRegressionTests(unittest.TestCase):
    def test_token_is_cached_in_memory_until_refresh_deadline(self):
        now = [0.0]
        session = TokenSession()
        cache = TokenCache(
            "client",
            "secret",
            session=session,
            now=lambda: now[0],
        )
        self.assertEqual(cache.get_token(), "token-1")
        now[0] = 59.0
        self.assertEqual(cache.get_token(), "token-1")
        now[0] = 61.0
        self.assertEqual(cache.get_token(), "token-2")
        self.assertEqual(session.calls, 2)
        self.assertEqual(session.last_timeout, (5, 20))
        self.assertFalse(session.last_allow_redirects)

    def test_search_caps_oversized_responses_and_disables_redirects(self):
        session = SearchSession()
        client = SpotifyClient(StaticTokenCache(), session=session)
        rows = client.search("term", "track", limit=50)
        self.assertEqual(len(rows), 5)
        self.assertFalse(session.allow_redirects)

    def test_cli_does_not_expose_a_result_limit_override(self):
        destinations = {action.dest for action in build_parser()._actions}
        self.assertNotIn("limit", destinations)

    def test_missing_spotify_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                SpotifyClient.from_environment()

    def test_input_reader_enforces_term_and_size_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_text("one\ntwo\n", encoding="utf-8")
            self.assertEqual(read_terms(path, max_terms=2), ["one", "two"])
            with self.assertRaises(ConfigurationError):
                read_terms(path, max_terms=1)
            with self.assertRaises(ConfigurationError):
                read_terms(path, max_bytes=2)

    def test_formula_like_cells_are_neutralized(self):
        for value in ("=SUM(1,1)", "+cmd", "-1+2", "@lookup", " \t=hidden"):
            self.assertTrue(spreadsheet_safe(value).startswith("'"))

    def test_csv_neutralizes_every_string_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            path = append_csv(
                Path(directory),
                "similar",
                [("=artist", "id", 1, "@related", "+id")],
            )
            with path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.reader(csv_file))
            self.assertEqual(
                rows[1],
                ["'=artist", "id", "1", "'@related", "'+id"],
            )

    def test_related_artist_job_is_finite(self):
        fake = FakeCatalog()
        with tempfile.TemporaryDirectory() as directory:
            total = run_similar_artists(
                fake,
                ["one", "two"],
                Path(directory),
                limit=3,
            )
        self.assertEqual(total, 6)
        self.assertEqual(fake.related_calls, 2)


if __name__ == "__main__":
    unittest.main()
