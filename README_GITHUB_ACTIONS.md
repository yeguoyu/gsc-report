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

Optional repository variables:

- `SITE_URL`, default `https://thermalmaster.com/`
- `DATA_DELAY_DAYS`, default `3`
- `GSC_SEARCH_TYPE`, default `web`
- `GSC_API_PAGE_SIZE`, default `25000`
- `QUERY_PAGE_LIMIT`, default `2000`
- `COUNTRY_DEVICE_LIMIT`, default `1000`
- `SEARCH_APPEARANCE_LIMIT`, default `1000`
- `BITABLE_TOP_QUERIES`, default `100`
- `BITABLE_TOP_PAGES`, default `100`
- `SEO_OPPORTUNITY_LIMIT`, default `12`
- `BRAND_TERMS`, comma-separated brand query rules
- `BRAND_PRODUCT_TERMS`, comma-separated product/model words inside brand queries
- `CORE_COUNTRIES`, comma-separated ISO country codes for priority markets

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

## SEO operations dashboard

Weekly and monthly HTML reports now include:

- Brand / brand-product / non-brand query split.
- Shopify URL page-type split: product, collection, blog, page, policy, cart, search, account, home, and other.
- Core-country performance using the default priority markets: United States, Germany, Japan, Norway, United Kingdom, France, Italy, Spain, Netherlands, Sweden, Finland, Denmark, Switzerland, Austria, Belgium, Poland, Portugal, Ireland, Czechia, and Hungary.
- SEO opportunity pool for low CTR, ranking push, product CTR, and blog internal-link opportunities.
