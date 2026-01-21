# FirstShowing RSS Feed Generator

Automatically generates an RSS feed every Monday at 9am with detailed movie information for the upcoming Friday's releases.

## Features

- Scrapes FirstShowing schedule for upcoming Friday releases
- Fetches movie details from TMDB API:
  - Movie posters
  - Synopsis
  - Runtime
  - MPAA rating (PG-13, R, etc.)
  - User scores
  - Genres
- Runs automatically in the cloud via GitHub Actions
- Publishes to GitHub Pages for easy RSS reader access

## Quick Start (Hosted on GitHub)

**See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for detailed GitHub setup.**

1. Create a public GitHub repository
2. Push this code
3. Enable GitHub Pages
4. Your feed URL: `https://YOUR_USERNAME.github.io/REPO_NAME/feed.xml`
5. Add to Feedly or any RSS reader

The feed updates automatically every Monday at 9 AM UTC.

## Local Testing

```bash
pip install -r requirements.txt
python generate_rss.py
```

## Manual Hosting (Windows Task Scheduler)

If you prefer to run locally instead of GitHub:

1. Install dependencies: `pip install -r requirements.txt`
2. Open Task Scheduler
3. Create Basic Task: "FirstShowing RSS Generator"
4. Trigger: Weekly, Monday at 9:00 AM
5. Action: Start `run_rss_generator.bat`
6. Host `feed.xml` on a web server
