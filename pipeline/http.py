"""Shared HTTP session with a polite UA, timeouts and retries."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter, Retry

UA = "fuyumi-digest-bot (fan site; contact on site)"
BROWSER_UA = "Mozilla/5.0 (compatible; fuyumi-digest-bot)"

_session = requests.Session()
_session.mount("https://", HTTPAdapter(max_retries=Retry(total=2, backoff_factor=2, status_forcelist=[500, 502, 503, 504])))
_session.headers["User-Agent"] = UA


def get(url: str, **kw) -> requests.Response:
    kw.setdefault("timeout", 20)
    return _session.get(url, **kw)
