# Dalal Desk

An Indian markets desk: headlines refreshed every 12 hours, how war and diplomacy reach Nifty sectors, and a SIP goal planner.

## Files

| File | What it does |
|---|---|
| `index.html` | The website |
| `news.json` | Latest headlines (rewritten automatically) |
| `scripts/update_news.py` | Fetches headlines from Google News |
| `.github/workflows/update-news.yml` | Runs the script at 6:50 AM and 6:50 PM IST |

## Put it online (GitHub Pages)

1. On github.com, click **New repository**, name it `dalal-desk`, choose **Public**, and create it.
2. Click **uploading an existing file** and drag in everything from this folder, including the hidden `.github` folder. (On Windows, if `.github` doesn't drag in, use GitHub Desktop or `git push` instead.) Commit.
3. **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, folder `/ (root)`. Save.
4. **Settings → Actions → General → Workflow permissions**: choose *Read and write permissions*. Save.
5. **Actions** tab → *Update headlines* → **Run workflow** to fetch fresh headlines now.

Your site will be at `https://<your-username>.github.io/dalal-desk/` after a minute or two. It works on phones too.

## Updating the analysis

Headlines update by themselves. The lead story, the four war & diplomacy cards and the oil table are in `index.html` (search for `BOARD` and `class="lead"`). Edit them on GitHub whenever the situation changes.

## Notes

- GitHub pauses scheduled workflows in repositories with no activity for 60 days. Re-enable it from the Actions tab if that happens.
- Google News RSS is offered for personal, non-commercial use. Keep the site personal; don't monetise it.
- For learning only, not investment advice.
