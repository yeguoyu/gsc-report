"""
飞书多维表格数据持久化模块 v6
- 同日期旧数据先删除，再重新写入，避免重复跑导致重复记录
- 关键词历史表现：按点击量取 Top 200，并过滤低展示词
- 页面历史表现：按点击量取 Top 200，并过滤低展示页面
"""

import requests
from datetime import datetime
import config


BITABLE_TOP_QUERIES = getattr(config, "BITABLE_TOP_QUERIES", 100)
BITABLE_TOP_PAGES = getattr(config, "BITABLE_TOP_PAGES", 100)
BITABLE_MIN_IMPRESSIONS = 10
BITABLE_PAGE_SIZE = 500


def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": config.FEISHU_APP_ID,
        "app_secret": config.FEISHU_APP_SECRET
    }

    try:
        resp = requests.post(url, json=payload, timeout=20).json()
    except Exception as e:
        print(f"[ERROR] 获取飞书 Token 请求失败: {e}")
        return None

    if resp.get("code") not in (0, None):
        print(f"[ERROR] 获取飞书 Token 失败: {resp}")
        return None

    return resp.get("tenant_access_token")


def get_table_ids(token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=20).json()
    except Exception as e:
        print(f"[ERROR] 获取多维表格 Table 列表失败: {e}")
        return {}

    table_map = {}
    if resp.get("code") == 0:
        for item in resp.get("data", {}).get("items", []):
            table_map[item["name"]] = item["table_id"]
    else:
        print(f"[ERROR] 获取多维表格 Table 列表失败: {resp}")

    return table_map


def batch_create_records(token, table_id, records):
    if not records:
        print("[INFO] 无记录需要写入")
        return True

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    ok = True
    for i in range(0, len(records), BITABLE_PAGE_SIZE):
        chunk = records[i:i + BITABLE_PAGE_SIZE]
        payload = {"records": chunk}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30).json()
        except Exception as e:
            print(f"[ERROR] 写入多维表格请求失败: {e}")
            ok = False
            continue

        if resp.get("code") != 0:
            print(f"[WARN] 写入多维表格失败: {resp.get('msg')} - 详情: {resp}")
            ok = False
        else:
            print(f"[INFO] 成功写入 {len(chunk)} 条数据至多维表格！")

    return ok


def _date_value_matches(value, feishu_date, date_str):
    target_date_1 = str(date_str)
    target_date_2 = target_date_1.replace("-", "/")

    try:
        target_ms = int(feishu_date)
    except Exception:
        target_ms = None

    if value is None:
        return False

    if isinstance(value, (int, float)):
        value_int = int(value)

        if target_ms is not None and value_int == target_ms:
            return True

        try:
            return datetime.fromtimestamp(value_int / 1000).strftime("%Y-%m-%d") == target_date_1
        except Exception:
            return False

    if isinstance(value, str):
        text = value.strip()

        if text in {target_date_1, target_date_2, str(feishu_date)}:
            return True

        if text.isdigit():
            try:
                return _date_value_matches(int(text), feishu_date, date_str)
            except Exception:
                return False

        normalized = text.replace("/", "-")
        if len(normalized) >= 10 and normalized[:10] == target_date_1:
            return True

        return False

    if isinstance(value, list):
        return any(_date_value_matches(item, feishu_date, date_str) for item in value)

    if isinstance(value, dict):
        for key in ("value", "text", "timestamp"):
            if key in value and _date_value_matches(value.get(key), feishu_date, date_str):
                return True

        return any(_date_value_matches(v, feishu_date, date_str) for v in value.values())

    return False


def _fetch_records_page(token, table_id, page_token=None, payload=None):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables/{table_id}/records/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    params = {"page_size": BITABLE_PAGE_SIZE}
    if page_token:
        params["page_token"] = page_token

    try:
        resp = requests.post(
            url,
            headers=headers,
            params=params,
            json=payload or {},
            timeout=30
        ).json()
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": {}}

    return resp


def search_records_by_date(token, table_id, feishu_date, date_str):
    record_ids = []
    page_token = None

    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "日期",
                    "operator": "is",
                    "value": [str(feishu_date)]
                }
            ]
        }
    }

    while True:
        resp = _fetch_records_page(token, table_id, page_token=page_token, payload=payload)

        if resp.get("code") != 0:
            print(f"[WARN] 按日期筛选记录失败，准备使用全量扫描兜底: {resp.get('msg')} - {resp}")
            return scan_record_ids_by_date(token, table_id, feishu_date, date_str)

        data = resp.get("data", {})
        for item in data.get("items", []):
            record_id = item.get("record_id")
            if record_id:
                record_ids.append(record_id)

        if not data.get("has_more"):
            break

        page_token = data.get("page_token")
        if not page_token:
            break

    if record_ids:
        return record_ids

    return scan_record_ids_by_date(token, table_id, feishu_date, date_str)


def scan_record_ids_by_date(token, table_id, feishu_date, date_str):
    record_ids = []
    page_token = None

    while True:
        resp = _fetch_records_page(token, table_id, page_token=page_token, payload={})

        if resp.get("code") != 0:
            print(f"[WARN] 全量扫描同日期记录失败: {resp.get('msg')} - {resp}")
            return None

        data = resp.get("data", {})
        for item in data.get("items", []):
            fields = item.get("fields", {})
            if _date_value_matches(fields.get("日期"), feishu_date, date_str):
                record_id = item.get("record_id")
                if record_id:
                    record_ids.append(record_id)

        if not data.get("has_more"):
            break

        page_token = data.get("page_token")
        if not page_token:
            break

    return record_ids


def batch_delete_records(token, table_id, record_ids):
    if not record_ids:
        return True

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables/{table_id}/records/batch_delete"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    ok = True
    for i in range(0, len(record_ids), BITABLE_PAGE_SIZE):
        chunk = record_ids[i:i + BITABLE_PAGE_SIZE]
        payload = {"records": chunk}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30).json()
        except Exception as e:
            print(f"[ERROR] 删除旧记录请求失败: {e}")
            ok = False
            continue

        if resp.get("code") != 0:
            print(f"[WARN] 删除旧记录失败: {resp.get('msg')} - {resp}")
            ok = False
        else:
            print(f"[INFO] 已删除 {len(chunk)} 条同日期旧记录")

    return ok


def clear_same_date_records(token, table_id, feishu_date, date_str, table_name):
    print(f"[INFO] 检查 {table_name} 是否存在同日期旧数据...")
    record_ids = search_records_by_date(token, table_id, feishu_date, date_str)

    if record_ids is None:
        print(f"[ERROR] {table_name} 同日期旧数据查询失败，为避免重复写入，本表跳过写入")
        return False

    if record_ids:
        print(f"[INFO] {table_name} 找到 {len(record_ids)} 条同日期旧数据，开始删除...")
        return batch_delete_records(token, table_id, record_ids)

    print(f"[INFO] {table_name} 无同日期旧数据")
    return True


def _get_key(row):
    keys = row.get("keys", [])
    return keys[0] if keys else ""


def _filter_top_rows(rows, top_n):
    filtered = [
        row for row in rows
        if row.get("impressions", 0) >= BITABLE_MIN_IMPRESSIONS
    ]

    return sorted(
        filtered,
        key=lambda x: x.get("clicks", 0),
        reverse=True
    )[:top_n]


def _build_prev_map(rows):
    result = {}
    for row in rows:
        key = _get_key(row)
        if key:
            result[key] = row
    return result


def push_to_bitable(data):
    if not hasattr(config, "FEISHU_APP_ID") or not config.FEISHU_APP_ID:
        print("[INFO] 未配置多维表格 API 凭证，跳过大报写入")
        return

    print("[INFO] 开始将筛选后的数据写入飞书多维表格...")
    token = get_tenant_access_token()
    if not token:
        print("[ERROR] 获取飞书 Token 失败，请检查 App ID 和 Secret")
        return

    table_map = get_table_ids(token)
    if not table_map:
        print("[ERROR] 未获取到多维表格 Table 列表，跳过写入")
        return

    date_str = str(data["end_date"])

    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        feishu_date = int(dt_obj.timestamp() * 1000)
    except Exception as e:
        print(f"[WARN] 日期转换失败，降级使用字符串: {e}")
        feishu_date = date_str

    kw_table_id = table_map.get("关键词历史表现")
    if kw_table_id and "queries" in data:
        if clear_same_date_records(token, kw_table_id, feishu_date, date_str, "关键词历史表现"):
            print("[INFO] 正在组装关键词明细...")
            prev_q_map = _build_prev_map(data.get("queries_prev", []))
            filtered_queries = _filter_top_rows(data.get("queries", []), BITABLE_TOP_QUERIES)

            print(
                f"[INFO] 关键词明细过滤后写入 {len(filtered_queries)} 条 "
                f"(Top {BITABLE_TOP_QUERIES}, impressions >= {BITABLE_MIN_IMPRESSIONS})"
            )

            kw_records = []
            for q in filtered_queries:
                kw = _get_key(q)
                if not kw:
                    continue

                pq = prev_q_map.get(kw, {})
                diff = q.get("clicks", 0) - pq.get("clicks", 0)

                kw_records.append({
                    "fields": {
                        "日期": feishu_date,
                        "关键词": str(kw),
                        "点击量": int(q.get("clicks", 0)),
                        "展示量": int(q.get("impressions", 0)),
                        "CTR": float(round(q.get("ctr", 0), 4)),
                        "平均排名": float(round(q.get("position", 0), 1)),
                        "环比变化": str(diff)
                    }
                })

            batch_create_records(token, kw_table_id, kw_records)
    else:
        print("[WARN] 未找到「关键词历史表现」表，跳过关键词写入")

    pg_table_id = table_map.get("页面历史表现")
    if pg_table_id and "pages" in data:
        if clear_same_date_records(token, pg_table_id, feishu_date, date_str, "页面历史表现"):
            print("[INFO] 正在组装页面明细...")
            prev_p_map = _build_prev_map(data.get("pages_prev", []))
            filtered_pages = _filter_top_rows(data.get("pages", []), BITABLE_TOP_PAGES)

            print(
                f"[INFO] 页面明细过滤后写入 {len(filtered_pages)} 条 "
                f"(Top {BITABLE_TOP_PAGES}, impressions >= {BITABLE_MIN_IMPRESSIONS})"
            )

            pg_records = []
            for p in filtered_pages:
                url = _get_key(p)
                if not url:
                    continue

                pp = prev_p_map.get(url, {})
                diff = p.get("clicks", 0) - pp.get("clicks", 0)
                short_url = str(url).replace(config.SITE_URL, "/")

                pg_records.append({
                    "fields": {
                        "日期": feishu_date,
                        "URL": short_url,
                        "点击量": int(p.get("clicks", 0)),
                        "展示量": int(p.get("impressions", 0)),
                        "CTR": float(round(p.get("ctr", 0), 4)),
                        "平均排名": float(round(p.get("position", 0), 1)),
                        "环比变化": str(diff)
                    }
                })

            batch_create_records(token, pg_table_id, pg_records)
    else:
        print("[WARN] 未找到「页面历史表现」表，跳过页面写入")
