"""
HTML 报告生成器 v3
全新设计的深色数据看板，带 SEO 诊断建议和图表
包含核心市场校验与 GEO(AI引擎优化) 数据模块预留
"""

import os
import json
import html
from datetime import datetime
import config
from seo_ops import build_seo_ops_summary


def generate_html_report(data):
    """生成完整的 HTML 报告"""
    if not config.HTML_REPORT_ENABLED:
        return None

    os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)

    report_type = data['report_type']
    date_str = data['end_date'].replace('-', '')
    filename = f"gsc_{report_type}_{date_str}.html"
    filepath = os.path.join(config.REPORT_OUTPUT_DIR, filename)

    html = _build_full_html(data)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[INFO] HTML 报告已生成: {filepath}")
    return filepath


def _calc_change(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return round((current - previous) / previous * 100, 1)


def _change_badge(val, reverse=False):
    """生成变化标签 HTML"""
    if val == 0:
        return '<span class="badge neutral">→ 持平</span>'
    if (val > 0 and not reverse) or (val < 0 and reverse):
        return f'<span class="badge up">↑ {abs(val)}%</span>'
    return f'<span class="badge down">↓ {abs(val)}%</span>'


def _change_badge_abs(val, reverse=False):
    if val == 0:
        return '<span class="badge neutral">→ 持平</span>'
    if (val > 0 and not reverse) or (val < 0 and reverse):
        return f'<span class="badge up">↑ {abs(val)}</span>'
    return f'<span class="badge down">↓ {abs(val)}</span>'


def _esc(value):
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _fmt_pct(value):
    return f"{float(value or 0) * 100:.2f}%"


def _summary_metric(summary, key, field):
    return summary.get(key, {}).get(field, 0) or 0


def _build_ops_html(data):
    summary = data.get('seo_ops') or build_seo_ops_summary(data)
    brand = summary.get('brand', {})
    page_types = summary.get('page_types', {})
    core = summary.get('core_countries', {})
    opportunities = summary.get('opportunities', [])

    brand_clicks = (
        _summary_metric(brand, 'Brand', 'clicks')
        + _summary_metric(brand, 'Brand Product', 'clicks')
    )
    nonbrand_clicks = _summary_metric(brand, 'Non-brand', 'clicks')
    total_keyword_clicks = brand_clicks + nonbrand_clicks
    nonbrand_share = nonbrand_clicks / total_keyword_clicks if total_keyword_clicks else 0
    brand_product_clicks = _summary_metric(brand, 'Brand Product', 'clicks')

    product_clicks = _summary_metric(page_types, 'Product', 'clicks')
    product_impressions = _summary_metric(page_types, 'Product', 'impressions')
    core_clicks = _summary_metric(core, 'Core', 'clicks')
    all_geo_clicks = core_clicks + _summary_metric(core, 'Other', 'clicks')
    core_share = core_clicks / all_geo_clicks if all_geo_clicks else 0

    segment_rows = ""
    for name in ['Non-brand', 'Brand Product', 'Brand']:
        item = brand.get(name, {})
        if not item:
            continue
        segment_rows += f'''<tr>
            <td class="kw">{_esc(name)}</td>
            <td class="val">{item.get('clicks', 0):,}</td>
            <td class="val">{item.get('impressions', 0):,}</td>
            <td class="val">{_fmt_pct(item.get('ctr', 0))}</td>
            <td class="val">{item.get('position', 0):.1f}</td>
            <td class="val">{item.get('rows', 0):,}</td>
        </tr>'''
    if not segment_rows:
        segment_rows = '<tr><td colspan="6" class="ops-empty">No keyword segment data.</td></tr>'

    page_type_rows = ""
    for name, item in sorted(page_types.items(), key=lambda kv: kv[1].get('clicks', 0), reverse=True):
        page_type_rows += f'''<tr>
            <td class="kw">{_esc(name)}</td>
            <td class="val">{item.get('clicks', 0):,}</td>
            <td class="val">{item.get('impressions', 0):,}</td>
            <td class="val">{_fmt_pct(item.get('ctr', 0))}</td>
            <td class="val">{item.get('position', 0):.1f}</td>
            <td class="val">{item.get('rows', 0):,}</td>
        </tr>'''
    if not page_type_rows:
        page_type_rows = '<tr><td colspan="6" class="ops-empty">No page type data.</td></tr>'

    core_rows = ""
    for row in core.get('top_core', []):
        keys = row.get('keys', [])
        code = keys[0].upper() if keys else ""
        core_rows += f'''<tr>
            <td class="kw">{_esc(code)}</td>
            <td class="val">{row.get('clicks', 0):,}</td>
            <td class="val">{row.get('impressions', 0):,}</td>
            <td class="val">{_fmt_pct(row.get('ctr', 0))}</td>
            <td class="val">{row.get('position', 0):.1f}</td>
        </tr>'''
    if not core_rows:
        core_rows = '<tr><td colspan="5" class="ops-empty">No core country data.</td></tr>'

    opportunity_rows = ""
    for i, op in enumerate(opportunities, 1):
        priority = op.get('priority', '')
        priority_cls = 'down' if priority == 'High' else ('up' if priority == 'Low' else '')
        query = op.get('query') or '-'
        page = op.get('short_url') or op.get('url') or '-'
        opportunity_rows += f'''<tr>
            <td class="num">{i}</td>
            <td><span class="badge neutral">{_esc(op.get('type', ''))}</span></td>
            <td class="chg {priority_cls}">{_esc(priority)}</td>
            <td class="kw">{_esc(query)}</td>
            <td class="pg" title="{_esc(op.get('url', ''))}">{_esc(page)}</td>
            <td class="val">{_esc(op.get('page_type', ''))}</td>
            <td class="val">{op.get('impressions', 0):,}</td>
            <td class="val">{_fmt_pct(op.get('ctr', 0))}</td>
            <td class="val">{op.get('position', 0):.1f}</td>
            <td class="val">{op.get('opportunity_clicks', 0):,}</td>
            <td class="pg">{_esc(op.get('action', ''))}</td>
        </tr>'''
    if not opportunity_rows:
        opportunity_rows = '<tr><td colspan="11" class="ops-empty">No SEO opportunities matched current thresholds.</td></tr>'

    return f'''
    <div class="card">
        <div class="card-title"><span class="icon">SEO</span> SEO Operations Snapshot</div>
        <div class="ops-grid">
            <div class="ops-metric">
                <div class="ops-label">Non-brand Share</div>
                <div class="ops-value">{_fmt_pct(nonbrand_share)}</div>
                <div class="ops-note">{nonbrand_clicks:,} non-brand clicks</div>
            </div>
            <div class="ops-metric">
                <div class="ops-label">Brand Product Clicks</div>
                <div class="ops-value">{brand_product_clicks:,}</div>
                <div class="ops-note">Brand terms with model intent</div>
            </div>
            <div class="ops-metric">
                <div class="ops-label">Product Page Clicks</div>
                <div class="ops-value">{product_clicks:,}</div>
                <div class="ops-note">{product_impressions:,} product impressions</div>
            </div>
            <div class="ops-metric">
                <div class="ops-label">Core-country Share</div>
                <div class="ops-value">{_fmt_pct(core_share)}</div>
                <div class="ops-note">{core_clicks:,} clicks from target markets</div>
            </div>
        </div>
    </div>

    <div class="row-2">
        <div class="card">
            <div class="card-title"><span class="icon">KW</span> Keyword Segments</div>
            <div class="tbl-wrap">
            <table>
                <thead><tr>
                    <th>Segment</th><th>Clicks</th><th>Impr.</th><th>CTR</th><th>Pos.</th><th>Rows</th>
                </tr></thead>
                <tbody>{segment_rows}</tbody>
            </table>
            </div>
        </div>
        <div class="card">
            <div class="card-title"><span class="icon">GEO</span> Core Country Top</div>
            <div class="tbl-wrap">
            <table>
                <thead><tr>
                    <th>Country</th><th>Clicks</th><th>Impr.</th><th>CTR</th><th>Pos.</th>
                </tr></thead>
                <tbody>{core_rows}</tbody>
            </table>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-title"><span class="icon">OPS</span> SEO Opportunity Pool</div>
        <div class="tbl-wrap">
        <table>
            <thead><tr>
                <th>#</th><th>Type</th><th>Priority</th><th>Query</th><th>Page</th>
                <th>Page Type</th><th>Impr.</th><th>CTR</th><th>Pos.</th><th>Opp. Clicks</th><th>Action</th>
            </tr></thead>
            <tbody>{opportunity_rows}</tbody>
        </table>
        </div>
    </div>

    <div class="card">
        <div class="card-title"><span class="icon">URL</span> Shopify Page Types</div>
        <div class="tbl-wrap">
        <table>
            <thead><tr>
                <th>Page Type</th><th>Clicks</th><th>Impr.</th><th>CTR</th><th>Pos.</th><th>Rows</th>
            </tr></thead>
            <tbody>{page_type_rows}</tbody>
        </table>
        </div>
    </div>
    '''


def _build_full_html(data):
    totals = data.get('totals', {})
    prev_totals = data.get('prev_totals', {})
    report_type = data['report_type']
    type_names = {'daily': '日报', 'weekly': '周报', 'monthly': '月报'}
    type_name = type_names.get(report_type, '报告')

    ch = {
        'clicks': _calc_change(totals.get('clicks', 0), prev_totals.get('clicks', 0)),
        'impressions': _calc_change(totals.get('impressions', 0), prev_totals.get('impressions', 0)),
        'ctr': round((totals.get('ctr', 0) - prev_totals.get('ctr', 0)) * 100, 2),
        'position': round(totals.get('position', 0) - prev_totals.get('position', 0), 1),
    }

    # --- 趋势图数据 ---
    trend_labels, trend_clicks, trend_impressions, trend_ctr, trend_position = [], [], [], [], []
    for row in sorted(data.get('daily_trend', []), key=lambda x: x['keys'][0]):
        trend_labels.append(row['keys'][0][5:])
        trend_clicks.append(row.get('clicks', 0))
        trend_impressions.append(row.get('impressions', 0))
        trend_ctr.append(round(row.get('ctr', 0) * 100, 2))
        trend_position.append(round(row.get('position', 0), 1))

    # --- 设备数据 ---
    device_map = {'MOBILE': '移动端', 'DESKTOP': '桌面端', 'TABLET': '平板'}
    device_labels, device_values = [], []
    for row in data.get('devices', []):
        device_labels.append(device_map.get(row['keys'][0], row['keys'][0]))
        device_values.append(row.get('clicks', 0))

    # --- 国家数据与北美/欧洲核心市场校验 ---
    country_flags = {
        'chn': '🇨🇳', 'usa': '🇺🇸', 'jpn': '🇯🇵', 'kor': '🇰🇷', 'gbr': '🇬🇧',
        'deu': '🇩🇪', 'fra': '🇫🇷', 'ind': '🇮🇳', 'bra': '🇧🇷', 'can': '🇨🇦',
        'aus': '🇦🇺', 'twn': '🇹🇼', 'hkg': '🇭🇰', 'sgp': '🇸🇬', 'mys': '🇲🇾',
        'tha': '🇹🇭', 'idn': '🇮🇩', 'vnm': '🇻🇳', 'phl': '🇵🇭', 'rus': '🇷🇺',
        'ita': '🇮🇹', 'esp': '🇪🇸', 'mex': '🇲🇽', 'nld': '🇳🇱', 'tur': '🇹🇷',
    }
    
    country_rows = ""
    total_country_clicks = sum(c.get('clicks', 0) for c in data.get('countries', []))
    
    # 核心市场：北美(US, CA) + 欧洲(GB, DE, FR, IT, ES, NL)
    target_markets = {'usa', 'can', 'gbr', 'deu', 'fra', 'ita', 'esp', 'nld'}
    target_clicks = sum(c.get('clicks', 0) for c in data.get('countries', []) if c['keys'][0].lower() in target_markets)
    target_pct = (target_clicks / total_country_clicks * 100) if total_country_clicks > 0 else 0
    
    # 根据占比生成健康度角标
    target_badge = ""
    if target_pct >= 60:
        target_badge = f'<span class="badge up" style="margin-left:8px; font-weight:normal;">核心市场健康: {target_pct:.1f}%</span>'
    elif total_country_clicks > 0:
        target_badge = f'<span class="badge down" style="margin-left:8px; font-weight:normal;">核心市场偏低: {target_pct:.1f}%</span>'

    for c in data.get('countries', []):
        code = c['keys'][0].lower()
        flag = country_flags.get(code, '🌍')
        pct = (c.get('clicks', 0) / total_country_clicks * 100) if total_country_clicks > 0 else 0
        country_rows += f'''<div class="geo-row">
            <span class="geo-flag">{flag}</span>
            <span class="geo-name">{c['keys'][0].upper()}</span>
            <div class="geo-bar-wrap"><div class="geo-bar" style="width:{pct}%"></div></div>
            <span class="geo-val">{c.get('clicks',0):,}</span>
            <span class="geo-pct">{pct:.1f}%</span>
        </div>'''

    # --- 关键词表格 ---
    prev_query_map = {r['keys'][0]: r for r in data.get('queries_prev', [])}
    queries_rows = ""
    for i, row in enumerate(sorted(data.get('queries', []), key=lambda x: x.get('clicks', 0), reverse=True)[:config.TOP_QUERIES], 1):
        q = row['keys'][0]
        prev = prev_query_map.get(q, {})
        cd = row['clicks'] - prev.get('clicks', 0)
        pd_ = prev.get('position', 0) - row.get('position', 0)
        cd_cls = 'up' if cd > 0 else ('down' if cd < 0 else '')
        pd_cls = 'up' if pd_ > 0 else ('down' if pd_ < 0 else '')
        queries_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="kw">{q}</td>
            <td class="val">{row.get('clicks',0):,}</td>
            <td class="chg {cd_cls}">{"▲" if cd>0 else "▼" if cd<0 else " | "} {abs(cd):,}</td>
            <td class="val">{row.get('impressions',0):,}</td>
            <td class="val">{row.get('ctr',0)*100:.1f}%</td>
            <td class="val">{row.get('position',0):.1f}</td>
            <td class="chg {pd_cls}">{"▲" if pd_>0 else "▼" if pd_<0 else " | "} {abs(pd_):.1f}</td>
        </tr>'''

    # --- 页面表格 ---
    prev_page_map = {r['keys'][0]: r for r in data.get('pages_prev', [])}
    pages_rows = ""
    for i, row in enumerate(sorted(data.get('pages', []), key=lambda x: x.get('clicks', 0), reverse=True)[:config.TOP_PAGES], 1):
        p = row['keys'][0]
        short = p.replace(config.SITE_URL, '/') if config.SITE_URL in p else p
        if len(short) > 55:
            short = short[:55] + '…'
        prev = prev_page_map.get(p, {})
        cd = row['clicks'] - prev.get('clicks', 0)
        cd_cls = 'up' if cd > 0 else ('down' if cd < 0 else '')
        pages_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="pg" title="{p}">{short}</td>
            <td class="val">{row.get('clicks',0):,}</td>
            <td class="chg {cd_cls}">{"▲" if cd>0 else "▼" if cd<0 else " | "} {abs(cd):,}</td>
            <td class="val">{row.get('impressions',0):,}</td>
            <td class="val">{row.get('ctr',0)*100:.1f}%</td>
            <td class="val">{row.get('position',0):.1f}</td>
        </tr>'''

    # --- GEO / AI 引擎表现预留模块 ---
    geo_optimization_html = ""
    if data.get('geo_data'):
        # 预留给后端传入的 AI Citation 真实数据
        pass
    else:
        geo_optimization_html = f'''<div class="card">
            <div class="card-title"><span class="icon">🤖</span> GEO (AI 引擎) 搜索可见度</div>
            <div class="diag-summary" style="background: rgba(88,166,255,0.05); color: var(--accent-blue); margin-bottom: 0;">
                💡 系统尚未检测到 ChatGPT / Perplexity 的提及抓取数据。建议接入 AI 引擎品牌提及追踪工具，以监控最新 Generative Engine Optimization 表现。
            </div>
        </div>'''

    # --- 月报专属模块 ---
    monthly_sections_html = ""
    if report_type == 'monthly':
        monthly_sections_html = _build_monthly_sections(data, prev_query_map, prev_page_map)

    # --- 索引问题 ---
    index_html = _build_index_issues_html(data.get('index_issues', {}))

    # --- SEO 诊断 ---
    diagnostics_html = _build_diagnostics_html(data.get('diagnostics', []), report_type)
    seo_ops_html = _build_ops_html(data)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GSC {type_name} | {data["end_date"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
    --bg: #0b0e14;
    --card: #12161f;
    --card-border: rgba(255,255,255,0.04);
    --text: #c9d1d9;
    --text-dim: #6b7280;
    --text-bright: #f0f6fc;
    --accent-blue: #58a6ff;
    --accent-purple: #bc8cff;
    --accent-green: #3fb950;
    --accent-amber: #d29922;
    --accent-red: #f85149;
    --accent-cyan: #39d2c0;
    --radius: 14px;
    --radius-sm: 8px;
}}
*{{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
}}
.wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px 20px; }}

/* --- Header --- */
.header {{
    background: linear-gradient(135deg, #161b27 0%, #1c2333 50%, #1a1f2e 100%);
    border-radius: var(--radius);
    padding: 36px 40px;
    margin-bottom: 20px;
    border: 1px solid var(--card-border);
    position: relative;
    overflow: hidden;
}}
.header::before {{
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(88,166,255,0.06) 0%, transparent 70%);
    border-radius: 50%;
}}
.header-top {{ display: flex; justify-content: space-between; align-items: flex-start; position: relative; }}
.header h1 {{ font-size: 26px; font-weight: 700; color: var(--text-bright); letter-spacing: -0.5px; }}
.header h1 span {{ color: var(--accent-blue); }}
.header-badge {{
    background: rgba(88,166,255,0.12); color: var(--accent-blue);
    padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;
    border: 1px solid rgba(88,166,255,0.2);
}}
.header-meta {{ margin-top: 14px; font-size: 13px; color: var(--text-dim); position: relative; }}
.header-meta span {{ margin-right: 24px; }}

/* --- KPI Grid --- */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }}
.kpi {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 22px 24px;
    border: 1px solid var(--card-border);
    transition: transform .15s, box-shadow .15s;
}}
.kpi:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.kpi-label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-dim); margin-bottom: 8px; }}
.kpi-value {{ font-size: 30px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
.kpi-value.c1 {{ color: var(--accent-blue); }}
.kpi-value.c2 {{ color: var(--accent-purple); }}
.kpi-value.c3 {{ color: var(--accent-green); }}
.kpi-value.c4 {{ color: var(--accent-amber); }}
.badge {{ display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 12px; margin-top: 6px; }}
.badge.up {{ background: rgba(63,185,80,0.12); color: var(--accent-green); }}
.badge.down {{ background: rgba(248,81,73,0.12); color: var(--accent-red); }}
.badge.neutral {{ background: rgba(255,255,255,0.06); color: var(--text-dim); }}

/* --- Cards --- */
.card {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid var(--card-border);
}}
.card-title {{
    font-size: 16px; font-weight: 600; color: var(--text-bright);
    margin-bottom: 18px; display: flex; align-items: center; gap: 10px;
}}
.card-title .icon {{ font-size: 20px; }}
.row-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
.row-2-wide {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }}
.ops-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
.ops-metric {{
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: var(--radius-sm);
    padding: 16px;
}}
.ops-label {{ font-size: 11px; color: var(--text-dim); font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }}
.ops-value {{ margin-top: 8px; font-size: 24px; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--accent-cyan); }}
.ops-note {{ margin-top: 4px; font-size: 12px; color: var(--text-dim); }}
.ops-empty {{ text-align: center; color: var(--text-dim); padding: 18px 12px; }}

/* --- Chart --- */
.chart-box {{ position: relative; height: 280px; }}
.chart-tabs {{ display: flex; gap: 8px; margin-bottom: 14px; }}
.chart-tab {{
    padding: 5px 14px; border-radius: 6px; font-size: 13px; font-weight: 500;
    background: rgba(255,255,255,0.04); color: var(--text-dim); cursor: pointer;
    border: 1px solid transparent; transition: all .15s;
}}
.chart-tab.active {{ background: rgba(88,166,255,0.1); color: var(--accent-blue); border-color: rgba(88,166,255,0.2); }}

/* --- Tables --- */
.tbl-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{
    text-align: left; padding: 10px 12px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px;
    color: var(--text-dim); border-bottom: 1px solid rgba(255,255,255,0.06);
}}
td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }}
tr:hover {{ background: rgba(255,255,255,0.015); }}
.num {{ color: var(--text-dim); width: 36px; }}
.kw {{ color: var(--accent-blue); font-weight: 500; max-width: 260px; word-break: break-all; }}
.pg {{ color: var(--accent-purple); font-size: 12px; font-family: 'JetBrains Mono', monospace; max-width: 340px; word-break: break-all; }}
.val {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; }}
.chg {{ font-weight: 600; font-size: 12px; }}
.chg.up {{ color: var(--accent-green); }}
.chg.down {{ color: var(--accent-red); }}

/* --- Geo --- */
.geo-row {{ display: flex; align-items: center; gap: 10px; padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
.geo-flag {{ font-size: 18px; }}
.geo-name {{ font-weight: 600; width: 40px; font-size: 13px; }}
.geo-bar-wrap {{ flex: 1; height: 6px; background: rgba(255,255,255,0.04); border-radius: 3px; overflow: hidden; }}
.geo-bar {{ height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue)); }}
.geo-val {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; min-width: 50px; text-align: right; }}
.geo-pct {{ color: var(--text-dim); font-size: 12px; min-width: 45px; text-align: right; }}

/* --- Device Donut placeholder --- */
.device-chart {{ position: relative; height: 220px; }}

/* --- Diagnostics --- */
.diag-item {{
    padding: 18px 20px; margin-bottom: 12px;
    border-radius: var(--radius-sm);
    border-left: 4px solid;
}}
.diag-item.high {{ background: rgba(248,81,73,0.05); border-color: var(--accent-red); }}
.diag-item.medium {{ background: rgba(210,153,34,0.05); border-color: var(--accent-amber); }}
.diag-item.low {{ background: rgba(63,185,80,0.05); border-color: var(--accent-green); }}
.diag-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
.diag-title {{ font-weight: 600; font-size: 15px; color: var(--text-bright); }}
.diag-sev {{
    font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 0.5px;
}}
.diag-sev.high {{ background: rgba(248,81,73,0.15); color: var(--accent-red); }}
.diag-sev.medium {{ background: rgba(210,153,34,0.15); color: var(--accent-amber); }}
.diag-sev.low {{ background: rgba(63,185,80,0.15); color: var(--accent-green); }}
.diag-desc {{ font-size: 13px; color: var(--text-dim); margin-bottom: 10px; }}
.diag-actions {{ font-size: 13px; }}
.diag-actions summary {{ cursor: pointer; color: var(--accent-blue); font-weight: 500; margin-bottom: 6px; }}
.diag-actions ol {{ padding-left: 20px; color: var(--text); }}
.diag-actions li {{ margin-bottom: 4px; }}
.diag-owner {{ font-size: 13px; color: var(--accent-cyan); margin-bottom: 8px; padding: 6px 12px; background: rgba(57,210,192,0.05); border-radius: 6px; }}
.diag-expected {{ font-size: 13px; color: var(--accent-green); margin-top: 10px; padding: 8px 12px; background: rgba(63,185,80,0.04); border-radius: 6px; border: 1px solid rgba(63,185,80,0.08); }}
.diag-summary {{ font-size: 14px; font-weight: 600; margin-bottom: 16px; padding: 10px 16px; background: rgba(255,255,255,0.02); border-radius: 8px; }}

/* --- Index Issues --- */
.idx-block {{
    background: rgba(255,255,255,0.015);
    border-radius: var(--radius-sm);
    padding: 18px 20px;
    margin-bottom: 14px;
    border-left: 4px solid var(--accent-amber);
}}
.idx-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
.idx-title {{ font-weight: 600; font-size: 15px; }}
.idx-count {{ background: var(--accent-amber); color: #000; padding: 2px 10px; border-radius: 14px; font-size: 12px; font-weight: 700; }}
.idx-desc {{ font-size: 13px; color: var(--text-dim); margin-bottom: 10px; }}
.idx-url {{
    background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 6px;
    margin-bottom: 5px; font-size: 12px; font-family: 'JetBrains Mono', monospace;
    color: var(--accent-blue); word-break: break-all;
}}
.idx-url-meta {{ display: block; color: var(--text-dim); font-size: 11px; margin-top: 3px; font-family: 'DM Sans', sans-serif; }}
.idx-fix {{
    margin-top: 12px; padding: 12px 16px; border-radius: 6px;
    background: rgba(63,185,80,0.04); border: 1px solid rgba(63,185,80,0.1);
}}
.idx-fix ol {{ padding-left: 18px; font-size: 13px; }}
.idx-fix li {{ margin-bottom: 3px; color: var(--text); }}

/* --- Footer --- */
.footer {{ text-align: center; color: var(--text-dim); font-size: 11px; padding: 24px; letter-spacing: 0.5px; }}

@media (max-width: 768px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .row-2, .row-2-wide, .ops-grid {{ grid-template-columns: 1fr; }}
    .header {{ padding: 24px; }}
    .kpi-value {{ font-size: 22px; }}
}}
</style>
</head>
<body>
<div class="wrap">
    <div class="header">
        <div class="header-top">
            <h1>📊 GSC <span>{type_name}</span></h1>
            <div class="header-badge">{config.SITE_URL.replace("https://","").rstrip("/")}</div>
        </div>
        <div class="header-meta">
            <span>📅 {data['start_date']} ~ {data['end_date']}</span>
            <span>🔄 对比 {data['prev_start']} ~ {data['prev_end']}</span>
            <span>⏰ {data['generated_at']}</span>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-label">🖱️ 总点击</div>
            <div class="kpi-value c1">{totals.get('clicks',0):,}</div>
            {_change_badge(ch['clicks'])}
        </div>
        <div class="kpi">
            <div class="kpi-label">👁️ 总展示</div>
            <div class="kpi-value c2">{totals.get('impressions',0):,}</div>
            {_change_badge(ch['impressions'])}
        </div>
        <div class="kpi">
            <div class="kpi-label">📌 平均 CTR</div>
            <div class="kpi-value c3">{totals.get('ctr',0)*100:.2f}%</div>
            {_change_badge_abs(ch['ctr'])}
        </div>
        <div class="kpi">
            <div class="kpi-label">📍 平均排名</div>
            <div class="kpi-value c4">{totals.get('position',0):.1f}</div>
            {_change_badge_abs(ch['position'], reverse=True)}
        </div>
    </div>

    <div class="card">
        <div class="card-title"><span class="icon">📈</span> 流量趋势</div>
        <div class="chart-tabs">
            <div class="chart-tab active" onclick="switchChart('clicks')">点击</div>
            <div class="chart-tab" onclick="switchChart('impressions')">展示</div>
            <div class="chart-tab" onclick="switchChart('ctr')">CTR</div>
            <div class="chart-tab" onclick="switchChart('position')">排名</div>
        </div>
        <div class="chart-box"><canvas id="trendChart"></canvas></div>
    </div>
    
    {geo_optimization_html}
    {seo_ops_html}

    <div class="row-2-wide">
        <div class="card">
            <div class="card-title"><span class="icon">🔑</span> 关键词 Top {config.TOP_QUERIES}</div>
            <div class="tbl-wrap">
            <table>
                <thead><tr>
                    <th>#</th><th>关键词</th><th>点击</th><th>变化</th>
                    <th>展示</th><th>CTR</th><th>排名</th><th>变化</th>
                </tr></thead>
                <tbody>{queries_rows}</tbody>
            </table>
            </div>
        </div>
        <div>
            <div class="card">
                <div class="card-title"><span class="icon">📱</span> 设备分布</div>
                <div class="device-chart"><canvas id="deviceChart"></canvas></div>
            </div>
            <div class="card">
                <div class="card-title"><span class="icon">🌍</span> 地区 Top {config.TOP_COUNTRIES} {target_badge}</div>
                {country_rows}
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-title"><span class="icon">📄</span> 页面 Top {config.TOP_PAGES}</div>
        <div class="tbl-wrap">
        <table>
            <thead><tr>
                <th>#</th><th>页面</th><th>点击</th><th>变化</th>
                <th>展示</th><th>CTR</th><th>排名</th>
            </tr></thead>
            <tbody>{pages_rows}</tbody>
        </table>
        </div>
    </div>

    {diagnostics_html}
    {monthly_sections_html}
    {index_html}

    <div class="footer">
        GSC Auto Report v3 | thermalmaster.com | {data['generated_at']}
    </div>
</div>

<script>
const DATA = {{
    labels: {json.dumps(trend_labels)},
    clicks: {json.dumps(trend_clicks)},
    impressions: {json.dumps(trend_impressions)},
    ctr: {json.dumps(trend_ctr)},
    position: {json.dumps(trend_position)},
}};
const COLORS = {{
    clicks: ['#58a6ff', 'rgba(88,166,255,0.08)'],
    impressions: ['#bc8cff', 'rgba(188,140,255,0.08)'],
    ctr: ['#3fb950', 'rgba(63,185,80,0.08)'],
    position: ['#d29922', 'rgba(210,153,34,0.08)'],
}};
const CHART_CFG = {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
        legend: {{ display: false }},
        tooltip: {{ backgroundColor: '#1c2333', titleColor: '#f0f6fc', bodyColor: '#c9d1d9',
                    borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1, padding: 12,
                    titleFont: {{ family: 'DM Sans' }}, bodyFont: {{ family: 'JetBrains Mono', size: 12 }} }}
    }},
    scales: {{
        x: {{ ticks: {{ color: '#6b7280', font: {{ size: 11 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }} }},
        y: {{ ticks: {{ color: '#6b7280', font: {{ family: 'JetBrains Mono', size: 11 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }} }}
    }}
}};
let trendChart;
function initTrend() {{
    const ctx = document.getElementById('trendChart').getContext('2d');
    trendChart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: DATA.labels,
            datasets: [{{ label: '点击', data: DATA.clicks, borderColor: COLORS.clicks[0],
                backgroundColor: COLORS.clicks[1], fill: true, tension: 0.4,
                pointRadius: 3, pointHoverRadius: 6, borderWidth: 2 }}]
        }},
        options: structuredClone(CHART_CFG)
    }});
}}
function switchChart(metric) {{
    document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    const names = {{ clicks: '点击', impressions: '展示', ctr: 'CTR (%)', position: '平均排名' }};
    trendChart.data.datasets[0] = {{
        label: names[metric], data: DATA[metric],
        borderColor: COLORS[metric][0], backgroundColor: COLORS[metric][1],
        fill: true, tension: 0.4, pointRadius: 3, pointHoverRadius: 6, borderWidth: 2
    }};
    if (metric === 'position') {{
        trendChart.options.scales.y.reverse = true;
    }} else {{
        trendChart.options.scales.y.reverse = false;
    }}
    trendChart.update();
}}
// Device Doughnut
function initDevice() {{
    const ctx = document.getElementById('deviceChart').getContext('2d');
    new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: {json.dumps(device_labels)},
            datasets: [{{ data: {json.dumps(device_values)},
                backgroundColor: ['#58a6ff', '#bc8cff', '#39d2c0'],
                borderWidth: 0, hoverOffset: 6 }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: {{
                legend: {{ position: 'bottom', labels: {{ color: '#c9d1d9', padding: 16, font: {{ family: 'DM Sans', size: 12 }} }} }},
                tooltip: {{ backgroundColor: '#1c2333', titleColor: '#f0f6fc', bodyColor: '#c9d1d9',
                            borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1 }}
            }}
        }}
    }});
}}
initTrend();
initDevice();
</script>
</body>
</html>'''


def _build_index_issues_html(issues):
    """构建索引问题区块"""
    if not issues:
        return ""

    configs = [
        ('crawled_not_indexed', '🔍 已抓取 | 尚未编入索引',
         'Google 成功抓取了这些页面但未将其编入索引，可能认为内容价值不足或与已有内容重复。',
         ['审查页面内容质量，确保有足够的独特、有价值内容（建议 800 字以上）',
          '增加内部链接指向这些页面，提升其在站内的重要性',
          '在 GSC 中手动请求编入索引',
          '检查是否存在近似重复内容，合并或加 canonical']),
        ('duplicate_canonical_mismatch', '📄 重复网页 | 规范网址不一致',
         'Google 发现这些页面与其他页面重复，且选择的规范 URL 与你指定的不同。',
         ['检查 <link rel="canonical"> 标签是否正确指向首选版本',
          '使用 301 重定向合并重复 URL 变体',
          '确保 URL 参数不会产生大量重复页面']),
        ('blocked_robots', '🤖 被 robots.txt 屏蔽',
         '这些页面的抓取被 robots.txt 规则阻止。',
         ['检查 robots.txt 中 Disallow 规则是否有误封',
          '如需索引，移除对应 Disallow 行',
          '使用 GSC 的 robots.txt 测试工具验证']),
        ('noindex', '🚫 被 noindex 标记排除',
         '页面 HTML 或 HTTP 响应头中包含 noindex 指令。',
         ['确认 noindex 是否为故意设置',
          '如需索引，移除 <meta name="robots" content="noindex">',
          '同时检查 HTTP header 中的 X-Robots-Tag']),
        ('not_found_404', '❌ 未找到 (404)',
         '这些 URL 返回 404 状态码。',
         ['对已迁移页面设置 301 重定向',
          '清理站点地图和内链中的死链',
          '对确实删除的页面在 GSC 中请求移除']),
        ('alternate_canonical', '🔗 备用网页（有规范标记）',
         '这些页面被正确标记为其他页面的备用版本，通常无需处理。',
         ['确认 canonical 指向的主页面已正确索引',
          '如不期望是备用页面，检查 canonical 设置']),
    ]

    blocks = []
    for key, title, desc, solutions in configs:
        urls = issues.get(key, [])
        if not urls:
            continue
        urls_html = ""
        for u in urls[:config.MAX_URLS_PER_REASON]:
            urls_html += f'''<div class="idx-url">{u.get('url','')}<span class="idx-url-meta">抓取: {u.get('crawl_time','N/A')[:10]} | 状态: {u.get('page_fetch_state','N/A')}</span></div>'''
        sols = "".join(f'<li>{s}</li>' for s in solutions)
        blocks.append(f'''<div class="idx-block">
            <div class="idx-header"><span class="idx-title">{title}</span><span class="idx-count">{len(urls)}</span></div>
            <div class="idx-desc">{desc}</div>
            {urls_html}
            <div class="idx-fix"><strong>💡 解决方案</strong><ol>{sols}</ol></div>
        </div>''')

    if not blocks:
        return ""

    return f'''<div class="card">
        <div class="card-title"><span class="icon">⚠️</span> 索引问题分析</div>
        {"".join(blocks)}
    </div>'''


def _build_diagnostics_html(diagnostics, report_type='daily'):
    """构建 SEO 深度诊断区块（含负责人、操作步骤、预期效果）"""
    if not diagnostics:
        return ""

    # 对于日报，后端应该过滤掉长期的策略规划类建议。此处仅在 UI 层面添加提示标签。
    type_notice = ""
    if report_type == 'daily':
        type_notice = " | ⚡ 仅显示敏捷排查动作"

    items = []
    sev_labels = {'high': '高优先级', 'medium': '中优先级', 'low': '低优先级'}
    for d in diagnostics:
        sev = d.get('severity', 'low')
        actions_html = "".join(f'<li>{a}</li>' for a in d.get('actions', []))

        # 负责人
        owner_html = ""
        if d.get('owner'):
            owner_html = f'<div class="diag-owner">👤 <strong>负责人：</strong>{d["owner"]}</div>'

        # 预期效果
        expected_html = ""
        if d.get('expected'):
            expected_html = f'<div class="diag-expected">📈 <strong>预期效果：</strong>{d["expected"]}</div>'

        # 详情（保留换行格式）
        detail = d.get('detail', '').replace('\n', '<br>')

        items.append(f'''<div class="diag-item {sev}">
            <div class="diag-header">
                <span class="diag-title">{d.get('category','')} | {d.get('message','')}</span>
                <span class="diag-sev {sev}">{sev_labels.get(sev, sev)}</span>
            </div>
            <div class="diag-desc">{detail}</div>
            {owner_html}
            <details class="diag-actions" open>
                <summary>🔧 具体操作步骤</summary>
                <ol>{actions_html}</ol>
            </details>
            {expected_html}
        </div>''')

    # 统计
    high_n = sum(1 for d in diagnostics if d.get('severity') == 'high')
    med_n = sum(1 for d in diagnostics if d.get('severity') == 'medium')
    low_n = sum(1 for d in diagnostics if d.get('severity') == 'low')
    summary = f'<div class="diag-summary">🔴 高优先级 {high_n} 项 &nbsp;|&nbsp; 🟡 中优先级 {med_n} 项 &nbsp;|&nbsp; 🟢 低优先级 {low_n} 项 {type_notice}</div>'

    return f'''<div class="card">
        <div class="card-title"><span class="icon">💡</span> SEO 深度诊断</div>
        {summary}
        {"".join(items)}
    </div>'''


def _build_monthly_sections(data, prev_query_map, prev_page_map):
    """月报专属模块：关键词增减排行、流量集中度、国家分布图表"""
    import json
    sections = []

    queries = data.get('queries', [])
    pages = data.get('pages', [])
    countries = data.get('countries', [])

    # ── 1. 关键词增减排行榜 ──
    kw_changes = []
    cur_kws = set()
    for q in queries:
        kw = q['keys'][0]
        cur_kws.add(kw)
        pq = prev_query_map.get(kw, {})
        diff = q.get('clicks', 0) - pq.get('clicks', 0)
        kw_changes.append({
            'keyword': kw,
            'clicks': q.get('clicks', 0),
            'prev_clicks': pq.get('clicks', 0),
            'diff': diff,
            'position': q.get('position', 0),
            'impressions': q.get('impressions', 0),
        })

    # 新增词（本期有上期无）
    new_kws = [k for k in kw_changes if k['keyword'] not in prev_query_map and k['clicks'] >= 3]
    new_kws.sort(key=lambda x: x['clicks'], reverse=True)

    # 丢失词（上期有本期无）
    lost_kws = []
    for kw, pq in prev_query_map.items():
        if kw not in cur_kws and pq.get('clicks', 0) >= 3:
            lost_kws.append({'keyword': kw, 'prev_clicks': pq.get('clicks', 0), 'impressions': pq.get('impressions', 0)})
    lost_kws.sort(key=lambda x: x['prev_clicks'], reverse=True)

    # 增长最多 & 下降最多
    gainers = sorted([k for k in kw_changes if k['diff'] > 0], key=lambda x: x['diff'], reverse=True)[:10]
    losers = sorted([k for k in kw_changes if k['diff'] < 0], key=lambda x: x['diff'])[:10]

    gainer_rows = ""
    for i, k in enumerate(gainers, 1):
        gainer_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="kw">{k['keyword']}</td>
            <td class="val">{k['prev_clicks']:,} → {k['clicks']:,}</td>
            <td class="chg up">▲ {k['diff']:,}</td>
            <td class="val">{k['position']:.1f}</td>
        </tr>'''

    loser_rows = ""
    for i, k in enumerate(losers, 1):
        loser_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="kw">{k['keyword']}</td>
            <td class="val">{k['prev_clicks']:,} → {k['clicks']:,}</td>
            <td class="chg down">▼ {abs(k['diff']):,}</td>
            <td class="val">{k['position']:.1f}</td>
        </tr>'''

    new_rows = ""
    for i, k in enumerate(new_kws[:10], 1):
        new_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="kw">✅ {k['keyword']}</td>
            <td class="val">{k['clicks']:,}</td>
            <td class="val">{k['impressions']:,}</td>
            <td class="val">{k['position']:.1f}</td>
        </tr>'''

    lost_rows = ""
    for i, k in enumerate(lost_kws[:10], 1):
        lost_rows += f'''<tr>
            <td class="num">{i}</td>
            <td class="kw">❌ {k['keyword']}</td>
            <td class="val">{k['prev_clicks']:,}</td>
            <td class="val">{k['impressions']:,}</td>
            <td class="val">-</td>
        </tr>'''

    sections.append(f'''<div class="card">
        <div class="card-title"><span class="icon">🔄</span> 月度关键词变动分析</div>
        <div class="diag-summary" style="background: rgba(88,166,255,0.05); color: var(--accent-blue);">
            📊 增长词 {len(gainers)} 个 | 下降词 {len(losers)} 个 | 新增词 {len(new_kws)} 个 | 丢失词 {len(lost_kws)} 个
        </div>
        <div class="row-2-wide">
            <div>
                <h3 style="color:var(--accent-green);margin:12px 0 8px;font-size:14px;">📈 增长 Top 10</h3>
                <div class="tbl-wrap"><table>
                    <thead><tr><th>#</th><th>关键词</th><th>点击变化</th><th>增量</th><th>排名</th></tr></thead>
                    <tbody>{gainer_rows}</tbody>
                </table></div>
            </div>
            <div>
                <h3 style="color:var(--accent-red);margin:12px 0 8px;font-size:14px;">📉 下降 Top 10</h3>
                <div class="tbl-wrap"><table>
                    <thead><tr><th>#</th><th>关键词</th><th>点击变化</th><th>降幅</th><th>排名</th></tr></thead>
                    <tbody>{loser_rows}</tbody>
                </table></div>
            </div>
        </div>
        <div class="row-2-wide" style="margin-top:16px;">
            <div>
                <h3 style="color:var(--accent-cyan);margin:12px 0 8px;font-size:14px;">🆕 新增关键词</h3>
                <div class="tbl-wrap"><table>
                    <thead><tr><th>#</th><th>关键词</th><th>点击</th><th>展示</th><th>排名</th></tr></thead>
                    <tbody>{new_rows if new_rows else '<tr><td colspan="5" style="text-align:center;color:var(--text-dim);">无新增</td></tr>'}</tbody>
                </table></div>
            </div>
            <div>
                <h3 style="color:var(--accent-amber);margin:12px 0 8px;font-size:14px;">💀 丢失关键词</h3>
                <div class="tbl-wrap"><table>
                    <thead><tr><th>#</th><th>关键词</th><th>上期点击</th><th>上期展示</th><th>排名</th></tr></thead>
                    <tbody>{lost_rows if lost_rows else '<tr><td colspan="5" style="text-align:center;color:var(--text-dim);">无丢失</td></tr>'}</tbody>
                </table></div>
            </div>
        </div>
    </div>''')

    # ── 2. 流量集中度（树状图 Treemap）──
    if pages:
        sorted_pages = sorted(pages, key=lambda x: x.get('clicks', 0), reverse=True)
        total_clicks = sum(p.get('clicks', 0) for p in pages)
        treemap_data = []
        for p in sorted_pages[:15]:
            short = p['keys'][0].replace(config.SITE_URL, '/')
            if len(short) > 40:
                short = short[:40] + '…'
            clicks = p.get('clicks', 0)
            pct = (clicks / total_clicks * 100) if total_clicks > 0 else 0
            treemap_data.append({'label': short, 'value': clicks, 'pct': round(pct, 1)})

        # 用柱状图展示 Top 15 页面流量分布
        tm_labels = json.dumps([d['label'] for d in treemap_data], ensure_ascii=False)
        tm_values = json.dumps([d['value'] for d in treemap_data])
        tm_pcts = json.dumps([d['pct'] for d in treemap_data])

        top1_pct = treemap_data[0]['pct'] if treemap_data else 0
        top3_pct = sum(d['pct'] for d in treemap_data[:3])
        health = "🟢 健康" if top1_pct < 30 else ("🟡 偏高" if top1_pct < 50 else "🔴 过度集中")

        sections.append(f'''<div class="card">
            <div class="card-title"><span class="icon">📊</span> 流量集中度分析</div>
            <div class="diag-summary" style="background: rgba(88,166,255,0.05); color: var(--accent-blue);">
                Top1 占比 {top1_pct:.1f}% | Top3 占比 {top3_pct:.1f}% | 集中度 {health}
            </div>
            <div class="chart-box" style="height:350px;"><canvas id="treemapChart"></canvas></div>
        </div>
        <script>
        (function() {{
            const ctx = document.getElementById('treemapChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {tm_labels},
                    datasets: [{{
                        label: '点击量',
                        data: {tm_values},
                        backgroundColor: [
                            '#58a6ff','#bc8cff','#3fb950','#d29922','#39d2c0',
                            '#f85149','#79c0ff','#d2a8ff','#56d364','#e3b341',
                            '#a5d6ff','#e8daff','#7ee787','#f0cc56','#76e4d4'
                        ],
                        borderWidth: 0,
                        borderRadius: 4,
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: '#1c2333',
                            titleColor: '#f0f6fc',
                            bodyColor: '#c9d1d9',
                            callbacks: {{
                                label: function(ctx) {{
                                    const pcts = {tm_pcts};
                                    return ctx.raw.toLocaleString() + ' 点击 (' + pcts[ctx.dataIndex] + '%)';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: '#6b7280', font: {{ family: 'JetBrains Mono', size: 11 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }} }},
                        y: {{ ticks: {{ color: '#c9d1d9', font: {{ size: 11 }}, autoSkip: false }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
        }})();
        </script>''')

    # ── 3. 国家/地区分布饼图（月报专属）──
    if countries and len(countries) >= 2:
        total_geo = sum(c.get('clicks', 0) for c in countries)
        country_chart_labels = []
        country_chart_values = []
        for c in countries[:8]:
            code = c['keys'][0].lower()
            name = config.COUNTRY_NAMES.get(code, c['keys'][0].upper())
            country_chart_labels.append(name)
            country_chart_values.append(c.get('clicks', 0))

        # 其他归为一类
        other_clicks = total_geo - sum(country_chart_values)
        if other_clicks > 0:
            country_chart_labels.append('其他')
            country_chart_values.append(other_clicks)

        sections.append(f'''<div class="card">
            <div class="card-title"><span class="icon">🌍</span> 月度国家/地区流量分布</div>
            <div class="chart-box" style="height:300px;max-width:500px;margin:0 auto;"><canvas id="countryPieChart"></canvas></div>
        </div>
        <script>
        (function() {{
            const ctx = document.getElementById('countryPieChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(country_chart_labels, ensure_ascii=False)},
                    datasets: [{{
                        data: {json.dumps(country_chart_values)},
                        backgroundColor: ['#58a6ff','#bc8cff','#3fb950','#d29922','#39d2c0','#f85149','#79c0ff','#d2a8ff','#56d364'],
                        borderWidth: 0,
                        hoverOffset: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '55%',
                    plugins: {{
                        legend: {{ position: 'right', labels: {{ color: '#c9d1d9', padding: 12, font: {{ family: 'DM Sans', size: 12 }} }} }},
                        tooltip: {{
                            backgroundColor: '#1c2333',
                            titleColor: '#f0f6fc',
                            bodyColor: '#c9d1d9',
                            callbacks: {{
                                label: function(ctx) {{
                                    const total = ctx.dataset.data.reduce((a,b) => a+b, 0);
                                    const pct = (ctx.raw / total * 100).toFixed(1);
                                    return ctx.label + ': ' + ctx.raw.toLocaleString() + ' (' + pct + '%)';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }})();
        </script>''')

    return "\n".join(sections)
