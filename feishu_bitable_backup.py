"""
飞书多维表格数据持久化模块 v5 (时间戳完美适配版)
"""
import requests
from datetime import datetime
import config

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": config.FEISHU_APP_ID,
        "app_secret": config.FEISHU_APP_SECRET
    }
    resp = requests.post(url, json=payload).json()
    return resp.get("tenant_access_token")

def get_table_ids(token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers).json()
    table_map = {}
    if resp.get("code") == 0:
        for item in resp["data"]["items"]:
            table_map[item["name"]] = item["table_id"]
    return table_map

def batch_create_records(token, table_id, records):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.BITABLE_APP_TOKEN}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    chunk_size = 500
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        payload = {"records": chunk}
        resp = requests.post(url, headers=headers, json=payload).json()
        if resp.get("code") != 0:
            print(f"[WARN] 写入多维表格失败: {resp.get('msg')} - 详情: {resp.get('error')}")
        else:
            print(f"[INFO] 成功写入 {len(chunk)} 条数据至多维表格！")

def push_to_bitable(data):
    if not hasattr(config, 'FEISHU_APP_ID') or not config.FEISHU_APP_ID:
        print("[INFO] 未配置多维表格 API 凭证，跳过大报写入")
        return

    print("[INFO] 开始将全量数据写入飞书多维表格...")
    token = get_tenant_access_token()
    if not token:
        print("[ERROR] 获取飞书 Token 失败，请检查 App ID 和 Secret")
        return

    table_map = get_table_ids(token)
    date_str = str(data['end_date'])
    
    # 核心修复：将文本日期自动转换为飞书要求的毫秒级时间戳
    try:
        dt_obj = datetime.strptime(date_str, '%Y-%m-%d')
        feishu_date = int(dt_obj.timestamp() * 1000)
    except Exception as e:
        print(f"[WARN] 日期转换失败，降级使用字符串: {e}")
        feishu_date = date_str

    # 1. 写入 [关键词历史表现] 表
    kw_table_id = table_map.get("关键词历史表现")
    if kw_table_id and 'queries' in data:
        print("[INFO] 正在组装关键词明细...")
        prev_q_map = {r['keys'][0]: r for r in data.get('queries_prev', [])}
        kw_records = []
        for q in data['queries']:
            kw = q['keys'][0]
            pq = prev_q_map.get(kw, {})
            diff = q.get('clicks', 0) - pq.get('clicks', 0)
            
            kw_records.append({"fields": {
                "日期": feishu_date,
                "关键词": str(kw),
                "点击量": int(q.get('clicks', 0)),
                "展示量": int(q.get('impressions', 0)),
                "CTR": float(round(q.get('ctr', 0), 4)),
                "平均排名": float(round(q.get('position', 0), 1)),
                "环比变化": str(diff)
            }})
        batch_create_records(token, kw_table_id, kw_records)

    # 2. 写入 [页面历史表现] 表
    pg_table_id = table_map.get("页面历史表现")
    if pg_table_id and 'pages' in data:
        print("[INFO] 正在组装页面明细...")
        prev_p_map = {r['keys'][0]: r for r in data.get('pages_prev', [])}
        pg_records = []
        for p in data['pages']:
            url = p['keys'][0]
            pp = prev_p_map.get(url, {})
            diff = p.get('clicks', 0) - pp.get('clicks', 0)
            
            pg_records.append({"fields": {
                "日期": feishu_date,
                "URL": str(url.replace(config.SITE_URL, '/')),
                "点击量": int(p.get('clicks', 0)),
                "展示量": int(p.get('impressions', 0)),
                "CTR": float(round(p.get('ctr', 0), 4)),
                "平均排名": float(round(p.get('position', 0), 1)),
                "环比变化": str(diff)
            }})
        batch_create_records(token, pg_table_id, pg_records)