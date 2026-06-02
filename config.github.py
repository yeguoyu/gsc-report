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


def _env_list(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return list(default)
    return [part.strip() for part in value.split(",") if part.strip()]


SITE_URL = os.getenv("SITE_URL", "https://thermalmaster.com/")

FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")

REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports")
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "./client_secret.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "./token.json")

DATA_DELAY_DAYS = _env_int("DATA_DELAY_DAYS", 3)
GSC_SEARCH_TYPE = os.getenv("GSC_SEARCH_TYPE", "web")
GSC_API_PAGE_SIZE = _env_int("GSC_API_PAGE_SIZE", 25000)

TOP_QUERIES = _env_int("TOP_QUERIES", 20)
TOP_PAGES = _env_int("TOP_PAGES", 15)
TOP_COUNTRIES = _env_int("TOP_COUNTRIES", 10)
MAX_URLS_PER_REASON = _env_int("MAX_URLS_PER_REASON", 10)

ALL_QUERIES_LIMIT = _env_int("ALL_QUERIES_LIMIT", 5000)
ALL_PAGES_LIMIT = _env_int("ALL_PAGES_LIMIT", 2000)
QUERY_PAGE_LIMIT = _env_int("QUERY_PAGE_LIMIT", 2000)
COUNTRY_DEVICE_LIMIT = _env_int("COUNTRY_DEVICE_LIMIT", 1000)
SEARCH_APPEARANCE_LIMIT = _env_int("SEARCH_APPEARANCE_LIMIT", 1000)

BITABLE_TOP_QUERIES = _env_int("BITABLE_TOP_QUERIES", 100)
BITABLE_TOP_PAGES = _env_int("BITABLE_TOP_PAGES", 100)

BRAND_TERMS = _env_list("BRAND_TERMS", [
    "thermal master",
    "thermalmaster",
    "thermal master p1",
    "thermal master p2",
    "thermal master p2 pro",
    "thermal master p2 app",
    "thermal master p3",
    "thermal master nv300",
    "thermal master nv300 max",
    "thermal master camera",
    "thermal master thermal camera",
    "thermal master t2 max",
    "thermal master thor",
    "thermal master thor 001",
    "thermal master thor 002",
    "thermal master thor002",
    "thermal master x3",
    "thermal master iphone",
    "thermal master app",
])
BRAND_PRODUCT_TERMS = _env_list("BRAND_PRODUCT_TERMS", [
    "p1",
    "p2",
    "p2 pro",
    "p3",
    "nv300",
    "nv300 max",
    "t2 max",
    "thor",
    "thor 001",
    "thor 002",
    "thor002",
    "x3",
    "camera",
    "thermal camera",
    "iphone",
    "app",
])
CORE_COUNTRIES = _env_list("CORE_COUNTRIES", [
    "usa",
    "deu",
    "jpn",
    "nor",
    "gbr",
    "fra",
    "ita",
    "esp",
    "nld",
    "swe",
    "fin",
    "dnk",
    "che",
    "aut",
    "bel",
    "pol",
    "prt",
    "irl",
    "cze",
    "hun",
])
SEO_OPPORTUNITY_LIMIT = _env_int("SEO_OPPORTUNITY_LIMIT", 12)

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
FEISHU_TECH_AT_ID = os.getenv("FEISHU_TECH_AT_ID", "")
FEISHU_TECH_AT_NAME = os.getenv("FEISHU_TECH_AT_NAME", "叶国钰")
FEISHU_OPS_AT_ID = os.getenv("FEISHU_OPS_AT_ID", "")
FEISHU_OPS_AT_NAME = os.getenv("FEISHU_OPS_AT_NAME", "谢佳丽")

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
