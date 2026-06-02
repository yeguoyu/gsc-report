"""
GSC API 数据拉取模块 v4
- 统一使用 searchconsole v1
- 方法名小写 searchanalytics()
- 服务实例缓存避免重复构建
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import config

SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/webmasters'
]

_service_cache = None
SEARCH_ANALYTICS_MAX_PAGE_SIZE = 25000


def get_credentials():
    """获取或刷新 OAuth 凭据"""
    creds = None
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def get_service():
    """创建 GSC API 服务实例（带缓存，避免重复 build）"""
    global _service_cache
    if _service_cache is None:
        creds = get_credentials()
        # ⚠️ 必须用 searchconsole v1，不能用 webmasters v3
        _service_cache = build('searchconsole', 'v1', credentials=creds)
    return _service_cache


def fetch_search_analytics(service, start_date, end_date, dimensions, row_limit=1000, search_type=None):
    """
    拉取搜索分析数据
    ⚠️ 必须用小写 searchanalytics()，不能用驼峰 searchAnalytics()
    """
    rows = []
    start_row = 0
    target_limit = max(0, int(row_limit or 0))
    page_size_config = getattr(config, 'GSC_API_PAGE_SIZE', SEARCH_ANALYTICS_MAX_PAGE_SIZE)
    page_size = max(1, min(int(page_size_config), SEARCH_ANALYTICS_MAX_PAGE_SIZE))

    if target_limit == 0:
        return rows
    try:
        while len(rows) < target_limit:
            current_limit = min(page_size, target_limit - len(rows))
            body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': current_limit,
                'startRow': start_row
            }

            if search_type:
                body['searchType'] = search_type

            response = service.searchanalytics().query(
                siteUrl=config.SITE_URL, body=body
            ).execute()
            page_rows = response.get('rows', [])

            if not page_rows:
                break

            rows.extend(page_rows)

            if len(page_rows) < current_limit:
                break

            start_row += len(page_rows)

        print(f"[INFO] dims={dimensions} fetched {len(rows)} rows")
        return rows
    except Exception as e:
        print(f"[ERROR] 拉取搜索数据失败 (dims={dimensions}): {e}")
        return []


def fetch_index_coverage(service):
    """拉取站点地图数据"""
    try:
        sitemaps = service.sitemaps().list(siteUrl=config.SITE_URL).execute()
        return sitemaps.get('sitemap', [])
    except Exception as e:
        print(f"[ERROR] 拉取站点地图数据失败: {e}")
        return []


def inspect_url(service, url):
    """使用 URL Inspection API 检查单个 URL 索引状态"""
    body = {
        'inspectionUrl': url,
        'siteUrl': config.SITE_URL
    }
    try:
        response = service.urlInspection().index().inspect(body=body).execute()
        return response.get('inspectionResult', {})
    except Exception as e:
        print(f"[ERROR] 检查 URL 失败 ({url}): {e}")
        return {}


def get_date_range(report_type):
    """根据报告类型计算日期范围"""
    today = datetime.now()
    delay = config.DATA_DELAY_DAYS

    if report_type == 'daily':
        end = today - timedelta(days=delay)
        start = end
    elif report_type == 'weekly':
        end = today - timedelta(days=delay)
        start = end - timedelta(days=6)
    elif report_type == 'monthly':
        end = today - timedelta(days=delay)
        start = end - timedelta(days=29)
    else:
        raise ValueError(f"未知报告类型: {report_type}")

    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


def get_comparison_range(report_type, start_date, end_date):
    """获取对比时间段（环比）"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    delta = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta - 1)
    return prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d')


def collect_all_data(report_type):
    """收集报告所需的所有数据"""
    service = get_service()
    start_date, end_date = get_date_range(report_type)
    prev_start, prev_end = get_comparison_range(report_type, start_date, end_date)

    print(f"[INFO] 数据范围: {start_date} ~ {end_date}")
    print(f"[INFO] 对比范围: {prev_start} ~ {prev_end}")

    data = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'prev_start': prev_start,
        'prev_end': prev_end,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    search_type = getattr(config, 'GSC_SEARCH_TYPE', 'web')

    print("[INFO] 拉取按日期汇总数据...")
    data['daily_trend'] = fetch_search_analytics(service, start_date, end_date, ['date'], search_type=search_type)
    data['daily_trend_prev'] = fetch_search_analytics(service, prev_start, prev_end, ['date'], search_type=search_type)

    print("[INFO] 拉取关键词全量数据...")
    all_queries_limit = getattr(config, 'ALL_QUERIES_LIMIT', 5000)
    data['queries'] = fetch_search_analytics(service, start_date, end_date, ['query'], row_limit=all_queries_limit, search_type=search_type)
    data['queries_prev'] = fetch_search_analytics(service, prev_start, prev_end, ['query'], row_limit=all_queries_limit, search_type=search_type)

    print("[INFO] 拉取页面全量数据...")
    all_pages_limit = getattr(config, 'ALL_PAGES_LIMIT', 2000)
    data['pages'] = fetch_search_analytics(service, start_date, end_date, ['page'], row_limit=all_pages_limit, search_type=search_type)
    data['pages_prev'] = fetch_search_analytics(service, prev_start, prev_end, ['page'], row_limit=all_pages_limit, search_type=search_type)

    print("[INFO] 拉取设备数据...")
    data['devices'] = fetch_search_analytics(service, start_date, end_date, ['device'], search_type=search_type)

    print("[INFO] 拉取国家/地区数据...")
    data['countries'] = fetch_search_analytics(service, start_date, end_date, ['country'], row_limit=config.TOP_COUNTRIES, search_type=search_type)

    print("[INFO] Fetch query-page rows...")
    query_page_limit = getattr(config, 'QUERY_PAGE_LIMIT', 2000)
    data['query_pages'] = fetch_search_analytics(service, start_date, end_date, ['query', 'page'], row_limit=query_page_limit, search_type=search_type)
    data['query_pages_prev'] = fetch_search_analytics(service, prev_start, prev_end, ['query', 'page'], row_limit=query_page_limit, search_type=search_type)

    print("[INFO] Fetch country-device rows...")
    country_device_limit = getattr(config, 'COUNTRY_DEVICE_LIMIT', 1000)
    data['country_devices'] = fetch_search_analytics(service, start_date, end_date, ['country', 'device'], row_limit=country_device_limit, search_type=search_type)

    print("[INFO] Fetch search appearance rows...")
    search_appearance_limit = getattr(config, 'SEARCH_APPEARANCE_LIMIT', 1000)
    data['search_appearance'] = fetch_search_analytics(service, start_date, end_date, ['searchAppearance'], row_limit=search_appearance_limit, search_type=search_type)

    data['fetch_summary'] = {
        'search_type': search_type,
        'queries_rows': len(data.get('queries', [])),
        'pages_rows': len(data.get('pages', [])),
        'query_page_rows': len(data.get('query_pages', [])),
        'country_device_rows': len(data.get('country_devices', [])),
        'search_appearance_rows': len(data.get('search_appearance', [])),
        'query_limit': all_queries_limit,
        'page_limit': all_pages_limit,
        'query_page_limit': query_page_limit,
    }

    print("[INFO] 拉取索引覆盖数据...")
    data['sitemaps'] = fetch_index_coverage(service)

    if report_type in ('weekly', 'monthly'):
        print("[INFO] 检查未索引页面...")
        data['index_issues'] = check_index_issues(service, data['pages'])

    print("[INFO] 数据收集完成！")
    return data


def check_index_issues(service, pages_data):
    """检查低展示页面的索引状态"""
    issues = {
        'crawled_not_indexed': [],
        'duplicate_canonical_mismatch': [],
        'blocked_robots': [],
        'noindex': [],
        'not_found_404': [],
        'alternate_canonical': [],
        'other': []
    }

    urls_to_check = []
    if pages_data:
        sorted_pages = sorted(pages_data, key=lambda x: x.get('impressions', 0))
        urls_to_check = [p['keys'][0] for p in sorted_pages[:30]]

    for url in urls_to_check:
        result = inspect_url(service, url)
        if not result:
            continue

        index_status = result.get('indexStatusResult', {})
        verdict = index_status.get('verdict', 'UNKNOWN')
        coverage_state = index_status.get('coverageState', '')

        if verdict != 'PASS':
            issue_entry = {
                'url': url,
                'verdict': verdict,
                'coverage_state': coverage_state,
                'crawl_time': index_status.get('lastCrawlTime', ''),
                'page_fetch_state': index_status.get('pageFetchState', ''),
                'robots_txt_state': index_status.get('robotsTxtState', ''),
                'indexing_state': index_status.get('indexingState', ''),
            }

            state_lower = coverage_state.lower()
            if 'crawled' in state_lower and 'not indexed' in state_lower:
                issues['crawled_not_indexed'].append(issue_entry)
            elif 'duplicate' in state_lower or 'canonical' in state_lower:
                issues['duplicate_canonical_mismatch'].append(issue_entry)
            elif 'robots' in state_lower:
                issues['blocked_robots'].append(issue_entry)
            elif 'noindex' in state_lower:
                issues['noindex'].append(issue_entry)
            elif '404' in state_lower or 'not found' in state_lower:
                issues['not_found_404'].append(issue_entry)
            elif 'alternate' in state_lower:
                issues['alternate_canonical'].append(issue_entry)
            else:
                issues['other'].append(issue_entry)

    return issues


def calc_totals(rows):
    """计算汇总数据"""
    total_clicks = sum(r.get('clicks', 0) for r in rows)
    total_impressions = sum(r.get('impressions', 0) for r in rows)
    avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
    avg_position = (
        sum(r.get('position', 0) * r.get('impressions', 0) for r in rows) / total_impressions
        if total_impressions > 0 else 0
    )
    return {
        'clicks': total_clicks,
        'impressions': total_impressions,
        'ctr': avg_ctr,
        'position': round(avg_position, 1)
    }
