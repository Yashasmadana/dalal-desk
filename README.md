# Dalal Desk

An Indian markets desk: headlines and prices refreshed every 12 hours, how war and diplomacy reach Nifty sectors, commodities, a private portfolio tracker, a SIP goal planner, a market calendar and a beginner's corner.

Live at https://yashasmadana.github.io/dalal-desk/

## Files

| File | What it does |
|---|---|
| `index.html` | The website |
| `news.json` | Latest headlines (rewritten automatically) |
| `prices.json` | Indices, commodities and stock prices (rewritten automatically) |
| `symbols.txt` | NSE stocks/ETFs whose prices are fetched for the portfolio tracker |
| `scripts/update_news.py` | Fetches headlines from Google News |
| `scripts/update_prices.py` | Fetches prices from Yahoo Finance |
| `.github/workflows/update-news.yml` | Runs both scripts at 6:50 AM and 6:50 PM IST |

## Everyday edits

- **Track a new stock's price:** add its NSE symbol on a new line in `symbols.txt`.
- **Add a calendar event:** add a line to the `EVENTS` list in `index.html`.
- **Update the analysis:** the cover story, war cards (`BOARD`) and oil table are in `index.html`.
- Always run `git pull` before editing locally; the bot commits new data twice a day.

## Notes

- The portfolio is stored only in each visitor's browser (localStorage). Use "Copy backup" / "Restore" to move it between devices.
- Prices come from Yahoo Finance's public chart data and may be delayed. Commodity ₹ figures exclude import duty and GST.
- GitHub pauses scheduled workflows after 60 days with no repository activity. Re-enable from the Actions tab if that happens.
- Google News RSS is offered for personal, non-commercial use. Keep the site personal; don't monetise it.
- For learning only, not investment advice.
