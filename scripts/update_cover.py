"""Build the cover story (cover.json) from prices.json and news.json.

Runs in GitHub Actions after update_news.py and update_prices.py.
Standard library only, no API keys. The text is assembled from rules and
templates, so it states facts from the data and avoids buy/sell advice.
If the data is missing, the existing cover.json is left untouched.
"""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parent.parent
PRICES = ROOT / "prices.json"
NEWS = ROOT / "news.json"
OUT = ROOT / "cover.json"
FIRST_ISSUE = date(2026, 11, 8)
ETFS = {"NIFTYBEES", "BANKBEES", "GOLDBEES", "SILVERBEES", "JUNIORBEES"}
WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def inr_group(v, dec=0):
    """Indian digit grouping: 1,02,345."""
    neg = v < 0
    s = f"{abs(v):.{dec}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + whole + ("." + frac if frac else "")


def pct(v):
    return f"{'▲' if v > 0 else '▼' if v < 0 else ''} {abs(v):.2f}%".strip()


def change(spark, n):
    """% change over the last n sessions, from daily closes."""
    if not spark or len(spark) <= n or not spark[-1 - n]:
        return None
    return (spark[-1] / spark[-1 - n] - 1) * 100


def streak(spark):
    """Signed run of up (+) or down (-) closes ending today, and the run before it."""
    diffs = [b - a for a, b in zip(spark, spark[1:]) if b != a]
    if not diffs:
        return 0, 0
    sign = 1 if diffs[-1] > 0 else -1
    k = 0
    for d in reversed(diffs):
        if (d > 0) == (sign > 0):
            k += 1
        else:
            break
    rest = diffs[: len(diffs) - k]
    prev = 0
    if rest:
        ps = 1 if rest[-1] > 0 else -1
        for d in reversed(rest):
            if (d > 0) == (ps > 0):
                prev += 1
            else:
                break
        prev *= ps
    return sign * k, prev


def headline(day, k, prev, week):
    if k == -1 and prev >= 3:
        return "Streak", "snapped."
    if k == 1 and prev <= -3:
        return "The slide", "pauses."
    if k >= 3:
        return f"{WORDS[k] if k < len(WORDS) else k} up days in a", "row."
    if k <= -3:
        return f"{WORDS[-k] if -k < len(WORDS) else -k} down days in a", "row."
    if day >= 1.5:
        return "Bulls take", "charge."
    if day <= -1.5:
        return "A rough day for", "Dalal Street."
    if week is not None and abs(week) >= 4:
        return f"Nifty {'up' if week > 0 else 'down'} {abs(week):.1f}% in a", "week."
    if day >= 0.5:
        return "A good day for", "Dalal Street."
    if day <= -0.5:
        return "Sellers in", "control."
    return "A quiet", "session."


def oil_text(wk):
    if wk is None:
        return "India imports most of its crude, so oil prices feed into inflation, the rupee and company margins."
    if wk >= 2:
        return f"Brent is up {wk:.1f}% in a week. India imports most of its crude, so costlier oil can push up inflation, weigh on the rupee and squeeze margins for oil users."
    if wk <= -2:
        return f"Brent is down {abs(wk):.1f}% in a week. India imports most of its crude, so cheaper oil eases inflation, supports the rupee and helps oil users."
    return f"Brent moved {wk:+.1f}% over the week, fairly steady. Oil remains a key swing factor for inflation and the rupee."


def rupee_text(rate, wk):
    if wk is None:
        return f"The rupee is at {rate:.2f} per dollar."
    # INR=X rising means more rupees per dollar, i.e. a weaker rupee
    if wk >= 0.3:
        return f"The rupee is at {rate:.2f} per dollar, weaker than a week ago. A weak rupee helps exporters like IT but raises import costs."
    if wk <= -0.3:
        return f"The rupee is at {rate:.2f} per dollar, stronger than a week ago. A firmer rupee eases import costs and tends to steady foreign investors."
    return f"The rupee is at {rate:.2f} per dollar, little changed on the week."


def main():
    prices, news = load(PRICES), load(NEWS)
    m = (prices or {}).get("markets", {})
    nifty, sensex = m.get("^NSEI"), m.get("^BSESN")
    if not nifty or not sensex:
        print("no index data; cover.json left unchanged")
        return

    sess = datetime.fromisoformat(nifty["t"]).astimezone(IST)
    sess_label = sess.strftime("%a %-d %b %Y")
    issue = max(1, (sess.date() - FIRST_ISSUE).days + 1)

    n_spark = nifty.get("spark") or []
    day = nifty.get("pct", 0.0)
    week = change(n_spark, 5)
    k, prev = streak(n_spark)
    h_a, h_b = headline(day, k, prev, week)

    brent = (prices.get("commodities") or {}).get("BZ=F")
    gold = (prices.get("commodities") or {}).get("GC=F")
    usd = m.get("INR=X")
    bank = m.get("^NSEBANK")
    b_wk = change(brent.get("spark"), 5) if brent else None
    r_wk = change(usd.get("spark"), 5) if usd else None

    deck = f"Nifty closed at {inr_group(nifty['p'])} ({pct(day)}) and Sensex at {inr_group(sensex['p'])} ({pct(sensex.get('pct', 0))})."
    if week is not None:
        deck += f" Over the last five sessions Nifty is {'up' if week >= 0 else 'down'} {abs(week):.1f}%."
    if brent and usd:
        deck += f" Brent crude is near ${brent['p']:.0f} a barrel and the rupee at {usd['p']:.2f} to the dollar."

    stats = [
        {"v": inr_group(sensex["p"]), "l": f"Sensex {pct(sensex.get('pct', 0))}, {sess.strftime('%a %-d %b')}"},
        {"v": inr_group(nifty["p"]), "l": f"Nifty 50 {pct(day)}"},
    ]
    if week is not None:
        stats.append({"v": f"{week:+.1f}%", "l": "Nifty over the last 5 sessions"})
    elif brent:
        stats.append({"v": f"${brent['p']:.0f}", "l": "Brent crude a barrel"})

    # paragraph 1: breadth and leaders
    st = {s: q for s, q in (prices.get("stocks") or {}).items() if s not in ETFS and q.get("pct") is not None}
    story = []
    if st:
        adv = sum(1 for q in st.values() if q["pct"] > 0)
        dec = sum(1 for q in st.values() if q["pct"] < 0)
        top = max(st.items(), key=lambda x: x[1]["pct"])
        bot = min(st.items(), key=lambda x: x[1]["pct"])
        p1 = f"Of the {len(st)} large stocks this page tracks, {adv} rose and {dec} fell. {top[0]} led the gainers ({top[1]['pct']:+.2f}%), while {bot[0]} fell the most ({bot[1]['pct']:+.2f}%)."
        if bank:
            p1 += f" Bank Nifty ended {pct(bank.get('pct', 0))}."
        story.append(p1)
    p2 = []
    if brent:
        p2.append(f"Brent crude near ${brent['p']:.0f} a barrel" + (f" ({b_wk:+.1f}% on the week)" if b_wk is not None else ""))
    if usd:
        p2.append(f"the rupee at {usd['p']:.2f} per dollar" + (f" ({'weaker' if r_wk >= 0.3 else 'stronger' if r_wk <= -0.3 else 'little changed'} on the week)" if r_wk is not None else ""))
    if gold:
        p2.append(f"gold near ${gold['p']:,.0f} an ounce")
    if p2:
        story.append("Across markets: " + ", ".join(p2) + ".")

    items = (news or {}).get("news") or []
    first = {}
    for it in items:
        first.setdefault(it.get("c"), it)
    focus = [x for x in ((news or {}).get("pulse"), first.get("War"), first.get("Diplomacy")) if x]
    if focus:
        story.append("In the headlines: " + " ".join(f"“{x['t']}” ({x.get('s', '')})." for x in focus[:2]))
    story.append("One session says little about the long run. Oil, the Iran war and foreign flows remain the big swing factors.")

    drivers = []
    if brent:
        arrow = "▲" if (b_wk or 0) > 0 else "▼" if (b_wk or 0) < 0 else ""
        drivers.append({"h": f"Oil {arrow}{abs(b_wk):.0f}%" if b_wk is not None else f"Oil ${brent['p']:.0f}", "p": oil_text(b_wk)})
    if usd:
        drivers.append({"h": f"Rupee {usd['p']:.2f}", "p": rupee_text(usd["p"], r_wk)})
    world = first.get("War") or first.get("Diplomacy")
    if world:
        drivers.append({"h": "World", "p": f"{world['t']} ({world.get('s', '')})", "link": world.get("link")})

    cover = {
        "updated": datetime.now(IST).isoformat(timespec="minutes"),
        "issue": [f"Issue {issue:02d}", f"Market close · {sess_label}"],
        "h1": [h_a, h_b],
        "deck": deck,
        "stats": stats,
        "story": story,
        "drivers": drivers,
    }
    OUT.write_text(json.dumps(cover, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote cover: {h_a} {h_b}")


if __name__ == "__main__":
    main()
