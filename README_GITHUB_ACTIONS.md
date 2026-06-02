# Run GSC reports on GitHub Actions

This project currently relies on Windows Task Scheduler, so it cannot run when
the local computer is off. The GitHub Actions workflow in
`.github/workflows/gsc-report.yml` runs it in GitHub instead.

## Schedule

- Weekly report: Sunday 12:00 Asia/Shanghai.
- Monthly report: last day of the month at 09:00 Asia/Shanghai.
- Manual run: Actions -> GSC report -> Run workflow.

## Required GitHub secrets

Add these in GitHub repo -> Settings -> Secrets and variables -> Actions:

- `FEISHU_WEBHOOK`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_CHAT_ID`
- `BITABLE_APP_TOKEN`
- `GSC_CLIENT_SECRET_JSON`
- `GSC_TOKEN_JSON`

Optional:

- `GA4_PROPERTY_ID`
- `GA4_TOKEN_JSON`

If GitHub has trouble accepting raw JSON, use base64 secrets instead:

- `GSC_CLIENT_SECRET_JSON_B64`
- `GSC_TOKEN_JSON_B64`
- `GA4_TOKEN_JSON_B64`

PowerShell examples:

```powershell
Get-Content .\client_secret.json -Raw
Get-Content .\token.json -Raw

[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content .\client_secret.json -Raw)))
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content .\token.json -Raw)))
```

## Push to GitHub

This folder is not a Git repository yet. After creating an empty GitHub repo,
run these from this folder:

```powershell
git init
git add .
git commit -m "Add GitHub Actions GSC scheduler"
git branch -M main
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

Do not commit `config.py`, `token.json`, `token_ga4.json`, or
`client_secret.json`. They are intentionally ignored.
