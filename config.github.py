"""
GitHub Actions configuration.

The workflow copies this file to config.py before running the report. Keep
secrets in GitHub Actions secrets, not in this file.
"""

import os


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


SITE_URL = os.getenv("SITE_URL", "https://thermalmaster.com/")

FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")

REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports")
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "./client_secret.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "./token.json")

DATA_DELAY_DAYS = _env_int("DATA_DELAY_DAYS", 3)

TOP_QUERIES = _env_int("TOP_QUERIES", 20)
TOP_PAGES = _env_int("TOP_PAGES", 15)
TOP_COUNTRIES = _env_int("TOP_COUNTRIES", 10)
MAX_URLS_PER_REASON = _env_int("MAX_URLS_PER_REASON", 10)

ALL_QUERIES_LIMIT = _env_int("ALL_QUERIES_LIMIT", 5000)
ALL_PAGES_LIMIT = _env_int("ALL_PAGES_LIMIT", 2000)

NEW_KW_MIN_CLICKS = _env_int("NEW_KW_MIN_CLICKS", 3)
LOST_KW_MIN_CLICKS = _env_int("LOST_KW_MIN_CLICKS", 3)

COUNTRY_NAMES = {
    "chn": "China",
    "usa": "United States",
    "jpn": "Japan",
    "kor": "South Korea",
    "gbr": "United Kingdom",
    "deu": "Germany",
    "fra": "France",
    "ind": "India",
    "bra": "Brazil",
    "can": "Canada",
    "aus": "Australia",
    "twn": "Taiwan",
    "hkg": "Hong Kong",
    "sgp": "Singapore",
    "mys": "Malaysia",
    "tha": "Thailand",
    "idn": "Indonesia",
    "vnm": "Vietnam",
    "phl": "Philippines",
    "rus": "Russia",
    "ita": "Italy",
    "esp": "Spain",
    "mex": "Mexico",
    "nld": "Netherlands",
    "tur": "Turkey",
    "sau": "Saudi Arabia",
    "are": "United Arab Emirates",
    "zaf": "South Africa",
    "pol": "Poland",
    "swe": "Sweden",
    "che": "Switzerland",
    "aut": "Austria",
    "bel": "Belgium",
    "nor": "Norway",
    "dnk": "Denmark",
    "fin": "Finland",
    "irl": "Ireland",
    "prt": "Portugal",
    "nzl": "New Zealand",
    "arg": "Argentina",
    "col": "Colombia",
    "chl": "Chile",
    "per": "Peru",
    "egy": "Egypt",
    "pak": "Pakistan",
    "bgd": "Bangladesh",
    "ukr": "Ukraine",
    "rom": "Romania",
    "isr": "Israel",
    "cze": "Czechia",
    "hun": "Hungary",
    "grc": "Greece",
}

FEISHU_PUSH_ENABLED = _env_bool("FEISHU_PUSH_ENABLED", True)
HTML_REPORT_ENABLED = _env_bool("HTML_REPORT_ENABLED", True)

FEISHU_CHAT_ID = os.getenv("FEISHU_CHAT_ID", "")

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN", "")

GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")
GA4_ENABLED = _env_bool("GA4_ENABLED", bool(GA4_PROPERTY_ID))

AI_REFERRERS = {
    "chat.openai.com": "ChatGPT",
    "chatgpt.com": "ChatGPT",
    "perplexity.ai": "Perplexity",
    "gemini.google.com": "Gemini",
    "bard.google.com": "Gemini",
    "copilot.microsoft.com": "Copilot",
    "bing.com/chat": "Copilot",
    "claude.ai": "Claude",
    "poe.com": "Poe",
    "you.com": "You.com",
    "phind.com": "Phind",
    "meta.ai": "Meta AI",
}
