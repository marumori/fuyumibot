"""YouTube @fuyumibot: RSS for recent uploads, Data API for the one-time back-catalogue."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from .. import http
from . import RawUpload, SourceError

CHANNEL_ID = "UC6qAQ5HtWW6h-Wl0bmPabag"
UPLOADS_PLAYLIST = "UU" + CHANNEL_ID[2:]
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def _url(vid: str) -> str:
    return f"https://www.youtube.com/watch?v={vid}"


def parse_feed(xml: str) -> list[RawUpload]:
    root = ET.fromstring(xml)
    if not root.findall("a:entry", NS):
        raise SourceError("youtube feed has no entries")
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        out.append(RawUpload("youtube", vid, _url(vid), e.findtext("a:title", namespaces=NS),
                             e.findtext("a:published", namespaces=NS).replace("+00:00", "Z")))
    return out


def parse_playlist_items(js: dict) -> list[RawUpload]:
    out = []
    for it in js.get("items", []):
        sn = it["snippet"]
        vid = sn["resourceId"]["videoId"]
        out.append(RawUpload("youtube", vid, _url(vid), sn["title"], sn["publishedAt"]))
    return out


def fetch_recent() -> list[RawUpload]:
    r = http.get(FEED)
    if r.status_code != 200:
        raise SourceError(f"youtube feed {r.status_code}")
    return parse_feed(r.text)


def fetch_all(api_key: str) -> list[RawUpload]:
    out, token = [], None
    while True:
        params = {"part": "snippet", "playlistId": UPLOADS_PLAYLIST, "maxResults": 50, "key": api_key}
        if token:
            params["pageToken"] = token
        r = http.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
        if r.status_code != 200:
            raise SourceError(f"youtube api {r.status_code}")
        js = r.json()
        out += parse_playlist_items(js)
        token = js.get("nextPageToken")
        if not token:
            return out
