"""SEO operations analysis helpers for GSC reports."""

import re
from urllib.parse import urlparse

import config


DEFAULT_BRAND_TERMS = [
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
]

DEFAULT_PRODUCT_TERMS = [
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
]

DEFAULT_CORE_COUNTRIES = [
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
]

DEFAULT_TARGET_KEYWORD_TERMS = [
    "thermal camera",
    "thermal camera for android",
    "thermal camera for iphone",
    "android thermal camera",
    "iphone thermal camera",
    "phone thermal camera",
    "smartphone thermal camera",
    "thermal imaging camera",
    "thermal imager",
    "thermal monocular",
    "thermal monoculars",
    "thermal scope",
    "thermal telescope",
    "thermal binocular",
    "thermal binoculars",
    "birdwatching binoculars",
    "bird watching binoculars",
    "birding binoculars",
    "binoculars for bird watching",
    "best binoculars for bird watching",
    "birdwatching monocular",
    "bird watching monocular",
    "birding monocular",
]

DEFAULT_EXCLUDED_TARGET_KEYWORD_TERMS = [
    "night vision camera for car",
    "infrared camera for car",
    "infrared car",
    "car",
    "automotive",
    "vehicle",
    "dashcam",
    "dashboard camera",
    "cctv",
    "security camera",
    "surveillance",
    "backup camera",
    "rear view camera",
]

DEFAULT_EXCLUDED_EXACT_KEYWORDS = [
    "thermal",
    "car",
    "infrared",
    "camera",
]

THERMAL_CAMERA_GROUP_TERMS = [
    "thermal camera",
    "thermal camera for android",
    "thermal camera for iphone",
    "android thermal camera",
    "iphone thermal camera",
    "phone thermal camera",
    "smartphone thermal camera",
    "thermal imaging camera",
    "thermal imager",
    "infrared thermal camera",
]

THERMAL_MONOCULAR_GROUP_TERMS = [
    "thermal monocular",
    "thermal monoculars",
    "thermal scope",
    "thermal telescope",
]

BIRDWATCHING_GROUP_TERMS = [
    "birdwatching binoculars",
    "bird watching binoculars",
    "birding binoculars",
    "binoculars for bird watching",
    "best binoculars for bird watching",
    "birdwatching monocular",
    "bird watching monocular",
    "birding monocular",
]

LONG_TAIL_MARKERS = [
    "how to",
    "best",
    "for",
    "vs",
    "versus",
    "does",
    "can",
    "what",
    "which",
    "android",
    "iphone",
]

TARGET_KEYWORD_GROUP_ORDER = [
    "Thermal Camera",
    "Thermal Monocular",
    "Birdwatching",
    "Long-tail Intent",
]

LOCALE_PREFIXES = {
    "ar", "bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr", "he",
    "hr", "hu", "id", "it", "ja", "ko", "lt", "lv", "ms", "nl", "no", "pl",
    "pt", "ro", "ru", "sk", "sl", "sv", "th", "tr", "uk", "vi", "zh",
    "zh-cn", "zh-tw",
}

FOCUS_PRODUCT_GROUPS = [
    {
        "topic": "thermal camera",
        "products": [
            {"name": "Thor", "terms": ["thor"], "priority": True},
            {"name": "P1", "terms": ["p1"], "priority": True},
            {"name": "P3", "terms": ["p3"], "priority": True},
            {"name": "P4", "terms": ["p4"], "priority": False},
        ],
    },
    {
        "topic": "thermal monocular",
        "products": [
            {"name": "DV2", "terms": ["dv2"], "priority": False},
            {"name": "T2 Max", "terms": ["t2-max", "t2 max", "t2max"], "priority": False},
        ],
    },
    {
        "topic": "night vision camera for car",
        "products": [
            {"name": "NV300 Max", "terms": ["nv300-max", "nv300 max", "nv300max"], "priority": False},
            {"name": "NV300", "terms": ["nv300"], "exclude_terms": ["max"], "priority": False},
        ],
    },
]

PAGE_TYPE_RULES = [
    ("/products/", "Product"),
    ("/collections/", "Collection"),
    ("/blogs/", "Blog"),
    ("/pages/", "Page"),
    ("/policies/", "Policy"),
    ("/cart", "Cart"),
    ("/search", "Search"),
    ("/account", "Account"),
]


def _keys(row):
    return row.get("keys", [])


def _key(row, index=0):
    keys = _keys(row)
    return keys[index] if len(keys) > index else ""


def _norm(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def _tokens(text):
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _contains_query_term(text, term):
    clean_term = str(term or "").strip().lower()
    if not clean_term:
        return False
    if len(clean_term) <= 3 and clean_term.isalnum():
        return clean_term in _tokens(text)
    return _norm(clean_term) in _norm(text)


def _terms_from_config(name, defaults):
    value = getattr(config, name, defaults)
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return list(value or defaults)


def get_brand_terms():
    return _terms_from_config("BRAND_TERMS", DEFAULT_BRAND_TERMS)


def get_product_terms():
    return _terms_from_config("BRAND_PRODUCT_TERMS", DEFAULT_PRODUCT_TERMS)


def get_core_countries():
    return {code.lower() for code in _terms_from_config("CORE_COUNTRIES", DEFAULT_CORE_COUNTRIES)}


def get_target_keyword_terms():
    return _terms_from_config("TARGET_KEYWORD_TERMS", DEFAULT_TARGET_KEYWORD_TERMS)


def get_excluded_target_keyword_terms():
    return _terms_from_config("EXCLUDED_TARGET_KEYWORDS", DEFAULT_EXCLUDED_TARGET_KEYWORD_TERMS)


def get_excluded_exact_keywords():
    return {term.lower() for term in _terms_from_config("EXCLUDED_EXACT_KEYWORDS", DEFAULT_EXCLUDED_EXACT_KEYWORDS)}


def is_brand_query(query):
    q = _norm(query)
    return any(_norm(term) in q for term in get_brand_terms())


def is_brand_product_query(query):
    if not is_brand_query(query):
        return False
    q = _norm(query)
    return any(_norm(term) in q for term in get_product_terms())


def classify_keyword(query):
    if is_brand_product_query(query):
        return "Brand Product"
    if is_brand_query(query):
        return "Brand"
    return "Non-brand"


def is_target_keyword(query):
    text = str(query or "").strip().lower()
    if not _norm(text) or text in get_excluded_exact_keywords():
        return False
    if any(_contains_query_term(text, term) for term in get_excluded_target_keyword_terms()):
        return False
    return any(_contains_query_term(text, term) for term in get_target_keyword_terms())


def _is_long_tail_query(query):
    text = str(query or "").strip().lower()
    words = _tokens(text)
    if len(words) >= 5:
        return True
    return any(_contains_query_term(text, marker) for marker in LONG_TAIL_MARKERS)


def classify_target_keyword_group(query):
    text = str(query or "").strip().lower()
    if not is_target_keyword(text):
        return None
    if _is_long_tail_query(text):
        return "Long-tail Intent"
    if any(_contains_query_term(text, term) for term in THERMAL_CAMERA_GROUP_TERMS):
        return "Thermal Camera"
    if any(_contains_query_term(text, term) for term in THERMAL_MONOCULAR_GROUP_TERMS):
        return "Thermal Monocular"
    if any(_contains_query_term(text, term) for term in BIRDWATCHING_GROUP_TERMS):
        return "Birdwatching"
    return "Long-tail Intent"


def is_main_domain_page(url):
    parsed = urlparse(str(url))
    path = parsed.path or "/"
    parts = [part.lower() for part in path.split("/") if part]
    if not parts:
        return True
    return parts[0] not in LOCALE_PREFIXES


def classify_page_type(url):
    parsed = urlparse(str(url))
    path = parsed.path or "/"
    if path == "/":
        return "Home"
    for prefix, label in PAGE_TYPE_RULES:
        if path.startswith(prefix):
            return label
    return "Other"


def _aggregate(rows, key_fn):
    buckets = {}
    for row in rows:
        key = key_fn(row)
        bucket = buckets.setdefault(key, {
            "clicks": 0,
            "impressions": 0,
            "position_weight": 0.0,
            "rows": 0,
        })
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        bucket["clicks"] += clicks
        bucket["impressions"] += impressions
        bucket["position_weight"] += row.get("position", 0) * impressions
        bucket["rows"] += 1

    result = {}
    for key, bucket in buckets.items():
        impressions = bucket["impressions"]
        result[key] = {
            "clicks": bucket["clicks"],
            "impressions": impressions,
            "ctr": bucket["clicks"] / impressions if impressions else 0,
            "position": bucket["position_weight"] / impressions if impressions else 0,
            "rows": bucket["rows"],
        }
    return result


def _target_ctr(position):
    try:
        position = float(position)
    except (TypeError, ValueError):
        position = 99
    if position <= 3:
        return 0.18
    if position <= 10:
        return 0.08
    if position <= 20:
        return 0.04
    return 0.02


def target_ctr_for_position(position):
    return _target_ctr(position)


def _short_url(url):
    return str(url).replace(config.SITE_URL, "/")


def _opportunity_score(row, target_ctr=None):
    impressions = row.get("impressions", 0)
    clicks = row.get("clicks", 0)
    target = target_ctr if target_ctr is not None else _target_ctr(row.get("position", 99))
    return max(0, int(impressions * target) - int(clicks))


def _make_opportunity(kind, row, query="", url="", reason="", action="", page_type=None):
    position = row.get("position", 99)
    target = _target_ctr(position)
    score = _opportunity_score(row, target)
    return {
        "type": kind,
        "query": query,
        "url": url,
        "short_url": _short_url(url) if url else "",
        "page_type": page_type or (classify_page_type(url) if url else ""),
        "keyword_segment": classify_keyword(query) if query else "",
        "clicks": int(row.get("clicks", 0)),
        "impressions": int(row.get("impressions", 0)),
        "ctr": float(row.get("ctr", 0)),
        "position": float(position),
        "target_ctr": target,
        "opportunity_clicks": score,
        "priority": "High" if score >= 20 else ("Medium" if score >= 8 else "Low"),
        "reason": reason,
        "action": action,
    }


def build_brand_summary(queries):
    return _aggregate(queries, lambda row: classify_keyword(_key(row, 0)))


def build_page_type_summary(pages):
    return _aggregate(pages, lambda row: classify_page_type(_key(row, 0)))


def build_core_country_summary(countries):
    core = get_core_countries()
    result = _aggregate(countries, lambda row: "Core" if _key(row, 0).lower() in core else "Other")
    result["top_core"] = [
        row for row in sorted(
            countries,
            key=lambda r: r.get("clicks", 0),
            reverse=True,
        )
        if _key(row, 0).lower() in core
    ][:8]
    return result


def build_target_keyword_summary(queries, limit=20):
    rows = [row for row in queries if is_target_keyword(_key(row, 0))]
    return sorted(rows, key=lambda row: row.get("impressions", 0), reverse=True)[:limit]


def best_landing_page_for_query(query_pages, query):
    target = str(query or "").strip().lower()
    matches = [
        row for row in query_pages
        if str(_key(row, 0)).strip().lower() == target and _key(row, 1)
    ]
    main_matches = [row for row in matches if is_main_domain_page(_key(row, 1))]
    pool = main_matches or matches
    if not pool:
        return None
    return sorted(
        pool,
        key=lambda row: (row.get("clicks", 0), row.get("impressions", 0)),
        reverse=True,
    )[0]


def build_target_keyword_groups(data, limit=10):
    buckets = {group: [] for group in TARGET_KEYWORD_GROUP_ORDER}
    query_pages = data.get("query_pages", [])

    for row in data.get("queries", []):
        query = _key(row, 0)
        group = classify_target_keyword_group(query)
        if not group:
            continue

        page_row = best_landing_page_for_query(query_pages, query)
        url = _key(page_row, 1) if page_row else ""
        try:
            position = float(row.get("position", 99) or 99)
        except (TypeError, ValueError):
            position = 99
        target_ctr = target_ctr_for_position(position)
        buckets.setdefault(group, []).append({
            "group": group,
            "query": query,
            "url": url,
            "short_url": _short_url(url) if url else "",
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0)),
            "position": position,
            "target_ctr": target_ctr,
            "opportunity_clicks": _opportunity_score(row, target_ctr),
            "page_clicks": int(page_row.get("clicks", 0)) if page_row else 0,
            "page_impressions": int(page_row.get("impressions", 0)) if page_row else 0,
        })

    grouped = []
    for group in TARGET_KEYWORD_GROUP_ORDER:
        rows = sorted(
            buckets.get(group, []),
            key=lambda item: (item["impressions"], item["opportunity_clicks"]),
            reverse=True,
        )[:limit]
        if rows:
            grouped.append({"group": group, "rows": rows})
    return grouped


def build_focus_product_pages(pages):
    result = []
    product_pages = [
        row for row in pages
        if is_main_domain_page(_key(row, 0)) and classify_page_type(_key(row, 0)) == "Product"
    ]
    for group in FOCUS_PRODUCT_GROUPS:
        for product in group["products"]:
            terms = [_norm(term) for term in product["terms"]]
            exclude_terms = [_norm(term) for term in product.get("exclude_terms", [])]
            matches = [
                row for row in product_pages
                if any(term in _norm(_key(row, 0)) for term in terms)
                and not any(term in _norm(_key(row, 0)) for term in exclude_terms)
            ]
            best = sorted(
                matches,
                key=lambda row: (row.get("clicks", 0), row.get("impressions", 0)),
                reverse=True,
            )[0] if matches else None
            result.append({
                "topic": group["topic"],
                "product": product["name"],
                "priority": product.get("priority", False),
                "url": _key(best, 0) if best else "",
                "short_url": _short_url(_key(best, 0)) if best else "",
                "clicks": int(best.get("clicks", 0)) if best else 0,
                "impressions": int(best.get("impressions", 0)) if best else 0,
                "ctr": float(best.get("ctr", 0)) if best else 0,
                "position": float(best.get("position", 0)) if best else 0,
                "found": bool(best),
            })
    return result


def build_opportunities(data, limit=12):
    opportunities = []
    query_pages = data.get("query_pages", [])
    pages = data.get("pages", [])

    seen = set()
    for row in query_pages:
        query = _key(row, 0)
        url = _key(row, 1)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0)
        position = row.get("position", 99)
        page_type = classify_page_type(url)

        if is_target_keyword(query) and impressions >= 50 and ctr < 0.02 and position <= 20:
            op = _make_opportunity(
                "Low CTR",
                row,
                query=query,
                url=url,
                reason="High impressions but CTR below 2%",
                action="Rewrite title/meta around search intent and put the strongest selling point early.",
                page_type=page_type,
            )
            opportunities.append(op)
            seen.add(("low_ctr", query, url))

        if page_type == "Product" and impressions >= 50 and ctr < 0.03 and position <= 15:
            op = _make_opportunity(
                "Product CTR",
                row,
                query=query,
                url=url,
                reason="Product page has search visibility but weak click-through",
                action="Improve product title, price/value proposition, reviews, schema, and above-the-fold copy.",
                page_type=page_type,
            )
            opportunities.append(op)

    for row in pages:
        url = _key(row, 0)
        page_type = classify_page_type(url)
        if page_type == "Blog" and row.get("impressions", 0) >= 80 and row.get("clicks", 0) >= 3:
            op = _make_opportunity(
                "Blog Internal Links",
                row,
                query="",
                url=url,
                reason="Blog page earns organic demand and can pass intent to product pages",
                action="Add 3-5 contextual links to relevant product or collection pages.",
                page_type=page_type,
            )
            opportunities.append(op)

    deduped = {}
    for op in opportunities:
        key = (op["type"], op["query"], op["url"])
        existing = deduped.get(key)
        if existing is None or op["opportunity_clicks"] > existing["opportunity_clicks"]:
            deduped[key] = op

    return sorted(
        deduped.values(),
        key=lambda item: (item["opportunity_clicks"], item["impressions"]),
        reverse=True,
    )[:limit]


def build_seo_ops_summary(data):
    queries = data.get("queries", [])
    pages = data.get("pages", [])
    countries = data.get("countries", [])
    opportunities = build_opportunities(data, limit=getattr(config, "SEO_OPPORTUNITY_LIMIT", 12))
    target_keyword_limit = getattr(config, "TARGET_KEYWORD_LIMIT", 20)
    target_group_limit = getattr(config, "TARGET_KEYWORD_GROUP_LIMIT", 10)

    return {
        "brand": build_brand_summary(queries),
        "page_types": build_page_type_summary(pages),
        "core_countries": build_core_country_summary(countries),
        "opportunities": opportunities,
        "target_keywords": build_target_keyword_summary(queries, limit=target_keyword_limit),
        "target_keyword_groups": build_target_keyword_groups(data, limit=target_group_limit),
        "focus_products": build_focus_product_pages(pages),
        "brand_terms": get_brand_terms(),
        "target_keyword_terms": get_target_keyword_terms(),
        "core_country_codes": sorted(get_core_countries()),
    }
