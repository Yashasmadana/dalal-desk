"""Fetch commodity, index and stock prices and write prices.json.

Runs in GitHub Actions with update_news.py. Standard library only.
Prices come from Yahoo Finance's public chart endpoint and may be delayed.
Stock symbols to track are listed in symbols.txt (one NSE symbol per line).
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "prices.json"
SYMBOLS_FILE = ROOT / "symbols.txt"

MARKETS = {
    "^NSEI": "Nifty 50",
    "^BSESN": "Sensex",
    "^NSEBANK": "Bank Nifty",
    "INR=X": "USD/INR",
}
COMMODITIES = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "BZ=F": "Brent crude",
    "CL=F": "WTI crude",
    "NG=F": "Natural gas",
    "HG=F": "Copper",
}
UNITS = {"GC=F": "$/oz", "SI=F": "$/oz", "BZ=F": "$/bbl", "CL=F": "$/bbl", "NG=F": "$/MMBtu", "HG=F": "$/lb"}


def chart(symbol, rng="1mo"):
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range={rng}&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (dalal-desk price bot)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.load(r)["chart"]["result"][0]
            closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
            meta = res["meta"]
            price = meta.get("regularMarketPrice") or (closes[-1] if closes else None)
            if price is None:
                return None
            # previous close = last daily close before the latest one
            prev = closes[-2] if len(closes) >= 2 else meta.get("chartPreviousClose")
            if closes and abs(closes[-1] - price) / price > 0.002 and len(closes) >= 1:
                prev = closes[-1]  # today's bar not in closes yet
            chg = price - prev if prev else 0.0
            return {
                "p": round(price, 4),
                "chg": round(chg, 4),
                "pct": round(chg / prev * 100, 2) if prev else 0.0,
                "cur": meta.get("currency", ""),
                "t": datetime.fromtimestamp(meta.get("regularMarketTime", 0), IST).isoformat(timespec="minutes"),
                "spark": [round(c, 4) for c in closes[-22:]],
            }
        except Exception as e:
            last = e
    print(f"warn: {symbol}: {last}")
    return None


def main():
    data = {"updated": datetime.now(IST).isoformat(timespec="minutes"), "markets": {}, "commodities": {}, "stocks": {}}

    for sym, name in MARKETS.items():
        q = chart(sym)
        if q:
            data["markets"][sym] = {"name": name, **q}
    for sym, name in COMMODITIES.items():
        q = chart(sym)
        if q:
            data["commodities"][sym] = {"name": name, "unit": UNITS[sym], **q}

    symbols = []
    if SYMBOLS_FILE.exists():
        for line in SYMBOLS_FILE.read_text(encoding="utf-8").splitlines():
            s = line.split("#")[0].strip().upper()
            if s and s not in symbols:
                symbols.append(s)
    for s in symbols:
        q = chart(s + ".NS", rng="5d")
        if q:
            q.pop("spark", None)
            data["stocks"][s] = q
        time.sleep(0.15)

    if len(data["commodities"]) < 3:
        raise SystemExit("Too few prices fetched; keeping the previous prices.json")
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(data['markets'])} markets, {len(data['commodities'])} commodities, {len(data['stocks'])} stocks")


if __name__ == "__main__":
    main()
