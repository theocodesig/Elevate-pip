"""Shared, side-effect-free helpers for the Elevate data collector."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import threading
import time
from typing import Any, Iterable, Mapping, Sequence

import requests


SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"
HTTP_TIMEOUT = (5, 20)
MAX_INPUT_BYTES = 64 * 1024
MAX_INPUT_TERMS = 250
MAX_TERM_LENGTH = 200


class ConfigurationError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


class SpotifyError(RuntimeError):
    """Raised when Spotify returns an unusable response."""


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        required = {
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError(
                "Database output is enabled, but these variables are missing: "
                + ", ".join(missing)
            )
        try:
            port = int(os.getenv("DB_PORT", "3306"))
        except ValueError as exc:
            raise ConfigurationError("DB_PORT must be an integer.") from exc
        return cls(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=port,
            database=required["DB_NAME"] or "",
            user=required["DB_USER"] or "",
            password=required["DB_PASSWORD"] or "",
        )


class TokenCache:
    """Thread-safe, in-memory Spotify client-credentials token cache."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        session: requests.Session | None = None,
        timeout: tuple[int, int] = HTTP_TIMEOUT,
        now=time.monotonic,
    ) -> None:
        if not client_id or not client_secret:
            raise ConfigurationError(
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in the environment."
            )
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session or requests.Session()
        self._timeout = timeout
        self._now = now
        self._token: str | None = None
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        with self._lock:
            if self._token is None or self._now() >= self._expires_at:
                self._refresh()
            return self._token or ""

    def _refresh(self) -> None:
        try:
            response = self._session.post(
                SPOTIFY_ACCOUNTS_URL,
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "client_credentials"},
                timeout=self._timeout,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise SpotifyError("Could not contact Spotify's token service.") from exc

        if response.status_code != 200:
            raise SpotifyError(
                f"Spotify token request failed with HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise SpotifyError("Spotify token response was not valid JSON.") from exc

        token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)
        if not isinstance(token, str) or not token:
            raise SpotifyError("Spotify token response did not contain an access token.")
        try:
            lifetime = max(1, int(expires_in))
        except (TypeError, ValueError) as exc:
            raise SpotifyError("Spotify token expiry was invalid.") from exc

        self._token = token
        self._expires_at = self._now() + max(1, lifetime - 60)


class SpotifyClient:
    """Small Spotify client with fixed origins and consistent error handling."""

    SEARCH_TYPES = {"track", "artist", "album"}

    def __init__(
        self,
        token_cache: TokenCache,
        *,
        session: requests.Session | None = None,
        timeout: tuple[int, int] = HTTP_TIMEOUT,
    ) -> None:
        self._token_cache = token_cache
        self._session = session or requests.Session()
        self._timeout = timeout

    @classmethod
    def from_environment(
        cls, *, session: requests.Session | None = None
    ) -> "SpotifyClient":
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        shared_session = session or requests.Session()
        return cls(
            TokenCache(client_id, client_secret, session=shared_session),
            session=shared_session,
        )

    def _get_json(
        self, path: str, *, params: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        if not path.startswith("/"):
            raise ValueError("Spotify API paths must start with '/'.")
        headers = {"Authorization": f"Bearer {self._token_cache.get_token()}"}
        try:
            response = self._session.get(
                SPOTIFY_API_URL + path,
                headers=headers,
                params=params,
                timeout=self._timeout,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise SpotifyError("Could not contact Spotify's API.") from exc

        if response.status_code != 200:
            raise SpotifyError(
                f"Spotify API request failed with HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise SpotifyError("Spotify API response was not valid JSON.") from exc
        if not isinstance(payload, Mapping):
            raise SpotifyError("Spotify API returned an unexpected response shape.")
        return payload

    def search(self, query: str, resource_type: str, limit: int = 5) -> list[Mapping[str, Any]]:
        if resource_type not in self.SEARCH_TYPES:
            raise ValueError(f"Unsupported Spotify resource type: {resource_type}")
        limit = max(1, min(int(limit), 5))
        payload = self._get_json(
            "/search", params={"q": query, "type": resource_type, "limit": limit}
        )
        group = payload.get(resource_type + "s", {})
        if not isinstance(group, Mapping):
            return []
        items = group.get("items", [])
        if not isinstance(items, list):
            return []
        return [
            item for item in items[:limit] if isinstance(item, Mapping)
        ]

    def album_upc(self, album_id: str) -> str | None:
        payload = self._get_json(f"/albums/{album_id}")
        external_ids = payload.get("external_ids", {})
        if isinstance(external_ids, Mapping):
            value = external_ids.get("upc")
            return str(value) if value else None
        return None

    def artist_id(self, artist_name: str) -> str | None:
        artists = self.search(artist_name, "artist", limit=1)
        value = artists[0].get("id") if artists else None
        return str(value) if value else None

    def related_artists(self, artist_id: str, limit: int = 5) -> list[Mapping[str, Any]]:
        payload = self._get_json(f"/artists/{artist_id}/related-artists")
        artists = payload.get("artists", [])
        if not isinstance(artists, list):
            return []
        safe_limit = max(0, min(int(limit), 5))
        return [item for item in artists[:safe_limit] if isinstance(item, Mapping)]


class DatabaseWriter:
    """Optional MySQL sink. CSV output remains the default and canonical output."""

    STATEMENTS = {
        "album": (
            "INSERT INTO album "
            "(term,ranks,name,upc,id,artist,Total_Tracks) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)"
        ),
        "artist": (
            "INSERT INTO artist "
            "(term,ranks,name,id,genres,followers,popularity) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)"
        ),
        "track": (
            "INSERT INTO track "
            "(term,ranks,name,isrc,id,artist,album,release_date,popularity) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        ),
        "similar": (
            "INSERT INTO similar_artist "
            "(artist,artist_id,ranks,similar_a,sim_ID) "
            "VALUES (%s,%s,%s,%s,%s)"
        ),
    }

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    @classmethod
    def from_environment(cls) -> "DatabaseWriter":
        return cls(DatabaseConfig.from_environment())

    def write(self, resource_type: str, rows: Sequence[Sequence[Any]]) -> None:
        if not rows:
            return
        statement = self.STATEMENTS.get(resource_type)
        if statement is None:
            raise ValueError(f"Unsupported database resource type: {resource_type}")

        try:
            import mysql.connector
            connection = mysql.connector.connect(
                host=self._config.host,
                port=self._config.port,
                database=self._config.database,
                user=self._config.user,
                password=self._config.password,
            )
            cursor = connection.cursor()
            cursor.executemany(statement, rows)
            connection.commit()
        except ImportError as exc:
            raise ConfigurationError(
                "Install the requirements before enabling database output."
            ) from exc
        except Exception as exc:
            if "connection" in locals():
                connection.rollback()
            raise RuntimeError("Database write failed.") from exc
        finally:
            if "cursor" in locals():
                cursor.close()
            if "connection" in locals():
                connection.close()


def read_terms(
    path: Path,
    *,
    max_bytes: int = MAX_INPUT_BYTES,
    max_terms: int = MAX_INPUT_TERMS,
    max_length: int = MAX_TERM_LENGTH,
) -> list[str]:
    """Read a bounded UTF-8 term list without creating intermediate files."""

    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Input file not found: {path}") from exc
    if size > max_bytes:
        raise ConfigurationError(f"Input file is larger than {max_bytes} bytes.")

    terms: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        term = raw_line.strip()
        if not term:
            continue
        if len(term) > max_length:
            raise ConfigurationError(
                f"An input term is longer than {max_length} characters."
            )
        terms.append(term)
        if len(terms) > max_terms:
            raise ConfigurationError(f"Input contains more than {max_terms} terms.")
    return terms


def join_artist_names(artists: Any) -> str:
    if not isinstance(artists, Iterable) or isinstance(artists, (str, bytes)):
        return ""
    names: list[str] = []
    for artist in artists:
        if isinstance(artist, Mapping) and artist.get("name"):
            names.append(str(artist["name"]))
    return ", ".join(names)
