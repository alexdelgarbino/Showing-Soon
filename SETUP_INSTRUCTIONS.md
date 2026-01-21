# GitHub Setup Instructions

Follow these steps to host your RSS feed automatically on GitHub:

## 1. Create GitHub Repository

1. Go to https://github.com/new
2. Name it something like `movie-rss-feed`
3. Make it **Public** (required for GitHub Pages)
4. Don't initialize with README (we already have files)
5. Click "Create repository"

## 2. Push Your Code

In this folder, run these commands:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/movie-rss-feed.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## 3. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Pages" in the left sidebar
4. Under "Source", select "Deploy from a branch"
5. Select branch: `main` and folder: `/ (root)`
6. Click "Save"

## 4. Enable GitHub Actions

1. Go to "Actions" tab in your repository
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow will run automatically every Monday at 9 AM UTC
4. You can also click "Run workflow" to test it immediately

## 5. Get Your Feed URL

Your RSS feed will be available at:
```
https://YOUR_USERNAME.github.io/movie-rss-feed/feed.xml
```

## 6. Add to Feedly

1. Open Feedly
2. Click "Add Content" or the "+" button
3. Paste your feed URL
4. Click "Follow"

## Timezone Adjustment

The workflow runs at 9 AM UTC by default. To change the timezone:

Edit `.github/workflows/update-feed.yml` and change the cron schedule:
- `0 9 * * 1` = 9 AM UTC Monday
- `0 14 * * 1` = 9 AM EST Monday (UTC-5)
- `0 13 * * 1` = 9 AM EDT Monday (UTC-4)
- `0 16 * * 1` = 9 AM PST Monday (UTC-8)
- `0 17 * * 1` = 9 AM PDT Monday (UTC-7)

## Testing

To test immediately without waiting for Monday:
1. Go to "Actions" tab
2. Click "Update RSS Feed" workflow
3. Click "Run workflow" dropdown
4. Click green "Run workflow" button

## Troubleshooting

If the feed doesn't update:
1. Check "Actions" tab for error messages
2. Make sure repository is Public
3. Verify GitHub Pages is enabled
4. Wait a few minutes for GitHub Pages to deploy

That's it! Your feed will update automatically every Monday at 9 AM.
