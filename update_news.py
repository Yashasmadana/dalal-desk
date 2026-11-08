"""Fetch Indian market headlines from Google News RSS and write news.json.

Runs in GitHub Actions every 12 hours. Uses only the Python standard library.
"""
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
OUT = Path(__file__).resolve().parent.parent / "news.json"
PER_CATEGORY = 6

# category -> search queries
QUERIES = {
    "Markets": ["Sensex Nifty when:2d", "Sensex closes Nifty settles when:2d"],
    "War": ["war stock market India crude when:3d", "Iran war Hormuz oil when:3d"],
    "Diplomacy": ["India trade deal tariff diplomacy when:3d", "Russia Ukraine talks India oil sanctions when:3d"],
    "Rupee & RBI": ["RBI rupee FII when:3d"],
}
PULSE_QUERY = "Sensex closes Nifty when:1d"


def fetch(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "dalal-desk-news-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(xml_bytes):
    items = []
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = it.findtext("pubDate")
        try:
            dt = parsedate_to_datetime(pub).astimezone(IST)
        except Exception:
            continue
        # Google appends " - Source" to titles; strip it
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        if title:
            items.append({"t": title, "s": source, "link": link, "ts": dt.isoformat()})
    return items


def norm(title):
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()[:60]


def main():
    seen, news = set(), []
    for cat, queries in QUERIES.items():
        pool = []
        for q in queries:
            try:
                pool += parse(fetch(q))
            except Exception as e:
                print(f"warn: {q!r}: {e}")
        pool.sort(key=lambda x: x["ts"], reverse=True)
        picked = 0
        for item in pool:
            key = norm(item["t"])
            if key in seen:
                continue
            seen.add(key)
            news.append({"c": cat, **item})
            picked += 1
            if picked >= PER_CATEGORY:
                break

    if len(news) < 6:
        raise SystemExit("Too few headlines fetched; keeping the previous news.json")

    pulse = None
    try:
        p = parse(fetch(PULSE_QUERY))
        p.sort(key=lambda x: x["ts"], reverse=True)
        pulse = p[0] if p else None
    except Exception as e:
        print(f"warn: pulse: {e}")

    data = {
        "updated": datetime.now(IST).isoformat(timespec="minutes"),
        "pulse": pulse,
        "news": news,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(news)} headlines to {OUT}")


if __name__ == "__main__":
    main()
