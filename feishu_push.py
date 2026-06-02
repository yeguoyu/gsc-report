"""
飞书推送模块 v5
- 纯卡片化，包含核心市场校验与跳转按钮
"""

import json
import os
import requests
import config

def push_to_feishu(report_data):
    if not config.FEISHU_PUSH_ENABLED:
        print("[INFO] 飞书推送已禁用")
        return

    card = build_full_card(report_data)
    payload = {"msg_type": "interactive", "card": card}
    _send_webhook(payload, "数据概览卡片")

    diag_card = build_diagnostics_card(report_data)
    if diag_card:
        payload2 = {"msg_type": "interactive", "card": diag_card}
        _send_webhook(payload2, "SEO 诊断卡片")

def _send_webhook(payload, label=""):
    try:
        resp = requests.post(
            config.FEISHU_WEBHOOK, json=payload,
            headers={'Content-Type': 'application/json'}, timeout=15
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get('code') == 0:
                print(f"[INFO] 飞书推送成功: {label}")
            else:
                print(f"[WARN] 飞书返回错误({label}): {result}")
        else:
            print(f"[ERROR] 飞书推送 HTTP 错误({label}): {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] 飞书推送失败({label}): {e}")

def build_full_card(data):
    type_map = {
        'daily': ('📊 GSC 日报', 'blue'),
        'weekly': ('📈 GSC 周报', 'green'),
        'monthly': ('📋 GSC 月报', 'purple'),
    }
    title, default_color = type_map.get(data['report_type'], ('📊 GSC 报告', 'blue'))
    date_range = data['start_date']
    if data['start_date'] != data['end_date']:
        date_range += f" ~ {data['end_date']}"
    title += f" | {date_range}"

    totals = data.get('totals', {})
    prev = data.get('prev_totals', {})
    elements = []

    countries = data.get('countries', [])
    target_badge_text = ""
    card_template_color = default_color

    if countries:
        total_geo_clicks = sum(c.get('clicks', 0) for c in countries)
        target_markets = {'usa', 'can', 'gbr', 'deu', 'fra', 'ita', 'esp', 'nld'}
        target_clicks = sum(c.get('clicks', 0) for c in countries if c['keys'][0].lower() in target_markets)
        target_pct = (target_clicks / total_geo_clicks * 100) if total_geo_clicks > 0 else 0

        if target_pct >= 60:
            target_badge_text = f" | 核心市场平稳: {target_pct:.1f}%"
        elif total_geo_clicks > 0:
            target_badge_text = f" | 核心市场偏低: {target_pct:.1f}%"
            card_template_color = "red"

    title += target_badge_text

    kpi_text = _build_kpi_text(totals, prev)
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": kpi_text}})
    elements.append({"tag": "hr"})

    idx_summary = data.get('index_issues_summary', {})
    if idx_summary and sum(idx_summary.values()) > 0:
        issue_names = {
            'crawled_not_indexed': '🔍 已抓取未索引',
            'duplicate_canonical_mismatch': '📄 重复/规范不一致',
            'blocked_robots': '🤖 robots.txt 屏蔽',
            'noindex': '🚫 noindex 排除',
            'not_found_404': '❌ 404 未找到',
            'alternate_canonical': '🔗 备用页面',
            'other': '❓ 其他'
        }
        idx_text = "**⚠️ 索引异常概况**\n"
        for key, count in idx_summary.items():
            if count > 0:
                idx_text += f"• {issue_names.get(key, key)}: **{count}** 个\n"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": idx_text}})
        elements.append({"tag": "hr"})

    # ⚠️ 这里的链接已经替换为你真实的表格链接！
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {
                    "tag": "plain_text",
                    "content": "📊 查看多维表格全量大报"
                },
                "type": "primary",
                "multi_url": {
                    "url": "https://jcnkf44tmfdp.feishu.cn/base/CBTybVdv6agwdIsmeAOcu0EUnoc?table=tblpzuh48F3Flze6&view=vew8p6mkOj",
                    "pc_url": "",
                    "android_url": "",
                    "ios_url": ""
                }
            }
        ]
    })

    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"⏰ {data.get('generated_at', '')} | RayNeo 流量中心"}]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": card_template_color},
        "elements": elements
    }

def _build_kpi_text(totals, prev):
    def fmt_change(cur, pre, is_pct=False, reverse=False):
        if pre == 0:
            return "🆕"
        diff = cur - pre
        pct = (diff / pre) * 100
        if is_pct:
            val_str = f"{diff*100:+.2f}pp"
        else:
            val_str = f"{diff:+,.0f}"
        if (diff > 0 and not reverse) or (diff < 0 and reverse):
            return f"🔺 {val_str} ({pct:+.1f}%)"
        elif (diff < 0 and not reverse) or (diff > 0 and reverse):
            return f"🔻 {val_str} ({pct:+.1f}%)"
        return "➖ 持平"

    clicks = totals.get('clicks', 0)
    impressions = totals.get('impressions', 0)
    ctr = totals.get('ctr', 0) * 100
    pos = totals.get('position', 0)

    return (
        "**📊 核心指标**\n\n"
        f"🖱️ **点击数**: **{clicks:,}** {fmt_change(clicks, prev.get('clicks', 0))}\n"
        f"👁️ **展示数**: **{impressions:,}** {fmt_change(impressions, prev.get('impressions', 0))}\n"
        f"📌 **平均CTR**: **{ctr:.2f}%** {fmt_change(totals.get('ctr',0), prev.get('ctr',0), is_pct=True)}\n"
        f"📍 **平均排名**: **{pos:.1f}** {fmt_change(pos, prev.get('position', 0), reverse=True)}"
    )

def build_diagnostics_card(data):
    diagnostics = data.get('diagnostics', [])
    if not diagnostics:
        return None
    type_zh = {'daily': '日报', 'weekly': '周报', 'monthly': '月报'}
    rtype = type_zh.get(data['report_type'], '报告')

    high_count = sum(1 for d in diagnostics if d.get('severity') == 'high')
    medium_count = sum(1 for d in diagnostics if d.get('severity') == 'medium')
    low_count = sum(1 for d in diagnostics if d.get('severity') == 'low')
    elements = []

    summary = f"**诊断结果**: 🔴 高优先级 {high_count} 项 | 🟡 中优先级 {medium_count} 项 | 🟢 低优先级 {low_count} 项\n"
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": summary}})
    elements.append({"tag": "hr"})

    for idx, d in enumerate(diagnostics):
        sev = d.get('severity', 'low')
        sev_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(sev, '⚪')
        sev_label = {'high': '高优先级', 'medium': '中优先级', 'low': '低优先级'}.get(sev, '')
        content = f"{sev_icon} **[{sev_label}] {d.get('category', '')}**\n\n"
        content += f"**问题**: {d.get('message', '')}\n\n"
        detail = d.get('detail', '')
        if detail:
            content += f"**详情**:\n{detail}\n\n"
        owner = d.get('owner', '')
        if owner:
            content += f"**👤 负责人**: {owner}\n\n"
        actions = d.get('actions', [])
        if actions:
            content += "**🔧 操作步骤**:\n"
            for i, a in enumerate(actions, 1):
                content += f"{i}. {a}\n"
            content += "\n"
        expected = d.get('expected', '')
        if expected:
            content += f"**📈 预期效果**: {expected}\n"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
        if idx < len(diagnostics) - 1:
            elements.append({"tag": "hr"})

    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"⏰ {data.get('generated_at', '')} | SEO 自动诊断 v5"}]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"💡 GSC {rtype} | SEO 深度诊断"},
            "template": "orange"
        },
        "elements": elements
    }