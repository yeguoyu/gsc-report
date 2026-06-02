"""
GA4 AI 可见度追踪模块
从 Google Analytics 4 拉取来自 AI 引擎的引荐流量，
按 日期 × AI来源 × 着陆页 × 国家 维度汇总，写入飞书多维表格。

依赖: google-analytics-data (pip install google-analytics-data)
复用项目已有的 OAuth 凭据（client_secret.json / token.json）
"""

import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import config

# GA4 Data API 需要额外的 scope
GA4_SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/webmasters',
]

# token 文件单独存，避免和 GSC 的 token 冲突（scope 不同）
GA4_TOKEN_FILE = './token_ga4.json'


def get_ga4_credentials():
    """获取 GA4 API 的 OAuth 凭据"""
    creds = None
    if os.path.exists(GA4_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GA4_TOKEN_FILE, GA4_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CLIENT_SECRET_FILE, GA4_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GA4_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return creds


def classify_ai_source(referrer):
    """
    根据 sessionSource / pageReferrer 判断 AI 来源
    返回来源标签（如 'ChatGPT'）或 None
    """
    if not referrer:
        return None
    referrer_lower = referrer.lower()
    for domain, label in config.AI_REFERRERS.items():
        if domain in referrer_lower:
            return label
    return None


def fetch_ai_traffic(start_date, end_date):
    """
    从 GA4 拉取所有引荐流量，筛选出 AI 引擎来源
    返回: [{date, ai_source, sessions, landing_page, country}, ...]
    """
    if not config.GA4_PROPERTY_ID:
        print("[WARN] GA4_PROPERTY_ID 未配置，跳过 AI 可见度追踪")
        return []

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, Dimension, Metric, DateRange, FilterExpression,
            Filter, OrderBy
        )
    except ImportError:
        print("[ERROR] 缺少依赖: pip install google-analytics-data --break-system-packages")
        return []

    print(f"[INFO] GA4 拉取 AI 引荐流量: {start_date} ~ {end_date}")

    creds = get_ga4_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)

    # 构建所有 AI referrer 域名的 OR 过滤条件
    ai_domains = list(config.AI_REFERRERS.keys())

    # 使用 sessionSource 维度来识别来源
    # 同时拉取 pageReferrer 做更精确的匹配
    request = RunReportRequest(
        property=f"properties/{config.GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="sessionSource"),
            Dimension(name="landingPage"),
            Dimension(name="country"),
            Dimension(name="pageReferrer"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=10000,
    )

    try:
        response = client.run_report(request)
    except Exception as e:
        print(f"[ERROR] GA4 API 调用失败: {e}")
        return []

    results = []
    for row in response.rows:
        date_val = row.dimension_values[0].value          # YYYYMMDD
        session_source = row.dimension_values[1].value    # e.g. 'chat.openai.com'
        landing_page = row.dimension_values[2].value      # e.g. '/products/xxx'
        country = row.dimension_values[3].value           # e.g. 'United States'
        page_referrer = row.dimension_values[4].value     # full referrer URL

        # 先用 sessionSource 匹配，再用 pageReferrer 兜底
        ai_source = classify_ai_source(session_source)
        if not ai_source:
            ai_source = classify_ai_source(page_referrer)
        if not ai_source:
            continue

        # 格式化日期 YYYYMMDD → YYYY-MM-DD
        try:
            formatted_date = datetime.strptime(date_val, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            formatted_date = date_val

        sessions = int(row.metric_values[0].value)
        active_users = int(row.metric_values[1].value)
        pageviews = int(row.metric_values[2].value)
        avg_duration = float(row.metric_values[3].value)

        if sessions > 0:
            results.append({
                'date': formatted_date,
                'ai_source': ai_source,
                'sessions': sessions,
                'active_users': active_users,
                'pageviews': pageviews,
                'avg_duration': round(avg_duration, 1),
                'landing_page': landing_page,
                'country': country,
            })

    print(f"[INFO] GA4 AI 引荐流量: 共 {len(results)} 条明细记录")
    return results


def build_geo_summary(records):
    """
    汇总 AI 流量概况，供飞书卡片推送用
    返回: {total_sessions, by_source: {source: sessions}, by_country: {country: sessions}}
    """
    summary = {
        'total_sessions': 0,
        'total_users': 0,
        'by_source': {},
        'by_country': {},
        'top_pages': {},
    }
    for r in records:
        summary['total_sessions'] += r['sessions']
        summary['total_users'] += r['active_users']

        src = r['ai_source']
        summary['by_source'][src] = summary['by_source'].get(src, 0) + r['sessions']

        ctry = r['country']
        summary['by_country'][ctry] = summary['by_country'].get(ctry, 0) + r['sessions']

        pg = r['landing_page']
        summary['top_pages'][pg] = summary['top_pages'].get(pg, 0) + r['sessions']

    return summary


def push_geo_to_bitable(records, token, table_id):
    """
    将 AI 流量明细写入飞书多维表格「GEO 品牌提及追踪」表
    字段: 日期, AI来源, 会话数, 着陆页, 国家
    """
    from feishu_bitable import batch_create_records

    if not records:
        print("[INFO] 无 AI 引荐流量数据，跳过 GEO 表写入")
        return

    geo_records = []
    for r in records:
        # 日期转飞书毫秒时间戳
        try:
            dt_obj = datetime.strptime(r['date'], '%Y-%m-%d')
            feishu_date = int(dt_obj.timestamp() * 1000)
        except Exception:
            feishu_date = r['date']

        geo_records.append({"fields": {
            "日期": feishu_date,
            "AI来源": str(r['ai_source']),
            "会话数": int(r['sessions']),
            "着陆页": str(r['landing_page']),
            "国家": str(r['country']),
        }})

    print(f"[INFO] 写入 GEO 品牌提及追踪: {len(geo_records)} 条")
    batch_create_records(token, table_id, geo_records)
