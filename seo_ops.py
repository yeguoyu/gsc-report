"""SEO operations analysis helpers for GSC reports."""

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
    if position <= 3:
        return 0.18
    if position <= 10:
        return 0.08
    if position <= 20:
        return 0.04
    return 0.02


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
        segment = classify_keyword(query)
        page_type = classify_page_type(url)

        if impressions >= 50 and ctr < 0.02 and position <= 20:
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

        if segment == "Non-brand" and 5 <= position <= 20 and impressions >= 30:
            op = _make_opportunity(
                "Ranking Push",
                row,
                query=query,
                url=url,
                reason="Non-brand query already ranks on page 1-2",
                action="Strengthen the target page with deeper content, internal links, and product proof.",
                page_type=page_type,
            )
            opportunities.append(op)

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

    return {
        "brand": build_brand_summary(queries),
        "page_types": build_page_type_summary(pages),
        "core_countries": build_core_country_summary(countries),
        "opportunities": opportunities,
        "brand_terms": get_brand_terms(),
        "core_country_codes": sorted(get_core_countries()),
    }
