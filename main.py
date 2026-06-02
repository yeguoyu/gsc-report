"""
GSC 自动报告系统 v5 - 主入口
"""

import argparse
import os
import sys
from datetime import datetime

import config
from gsc_client import collect_all_data, calc_totals
from feishu_push import push_to_feishu
from seo_diagnostics import run_diagnostics
from seo_ops import build_seo_ops_summary
from feishu_bitable import push_to_bitable, get_tenant_access_token, get_table_ids
from report_generator import generate_html_report
from feishu_file import upload_and_send

def determine_report_type():
    now = datetime.now()
    if now.month == 12:
        next_first = datetime(now.year + 1, 1, 1)
    else:
        next_first = datetime(now.year, now.month + 1, 1)
    is_last_day = (next_first.date() - now.date()).days == 1
    if is_last_day:
        return 'monthly'
    elif now.weekday() == 6:
        return 'weekly'
    else:
        return 'daily'

def run(report_type):
    type_zh = {'daily': '日报', 'weekly': '周报', 'monthly': '月报'}
    print(f"\n{'='*50}")
    print(f"  GSC {type_zh.get(report_type, '报告')} 生成中...")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 1. 拉取 GSC 数据
    print("[STEP 1/5] 拉取 GSC 数据...")
    data = collect_all_data(report_type)

    # 2. 计算汇总
    print("[STEP 2/5] 计算汇总指标...")
    data['totals'] = calc_totals(data.get('daily_trend', []))
    data['prev_totals'] = calc_totals(data.get('daily_trend_prev', []))

    if 'index_issues' in data:
        data['index_issues_summary'] = {k: len(v) for k, v in data['index_issues'].items()}

    data['seo_ops'] = build_seo_ops_summary(data)

    # 3. SEO 诊断
    print("[STEP 3/5] SEO 深度诊断分析...")
    data['diagnostics'] = run_diagnostics(data)
    for d in data['diagnostics']:
        icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(d['severity'], '⚪')
        print(f"  {icon} [{d['category']}] {d['message']}")

    # 4. 卡片推送与表格写入
    print("[STEP 4/6] 组装飞书卡片与持久化数据...")
    push_to_feishu(data)       # 推送群卡片小报
    push_to_bitable(data)      # 写入多维表格大报

    # 5. 生成 HTML 图表报告并发送到飞书群（仅周报/月报）
    print("[STEP 5/6] 生成 HTML 图表报告...")
    if report_type == 'daily':
        print("  ℹ️ 日报不生成图表报告")
    elif config.HTML_REPORT_ENABLED:
        html_path = generate_html_report(data)
        if html_path:
            print(f"[INFO] HTML 报告已生成: {html_path}")
            upload_and_send(html_path)
        else:
            print("[WARN] HTML 报告生成失败")
    else:
        print("  ℹ️ HTML 报告已禁用")

    # 6. GA4 AI 可见度追踪
    print("[STEP 6/6] GA4 AI 可见度追踪...")
    if getattr(config, 'GA4_ENABLED', False) and getattr(config, 'GA4_PROPERTY_ID', ''):
        try:
            from ga4_geo_tracker import fetch_ai_traffic, push_geo_to_bitable, build_geo_summary

            # 拉取与报告同周期的 AI 引荐流量
            geo_records = fetch_ai_traffic(data['start_date'], data['end_date'])

            if geo_records:
                # 汇总写入报告数据（供飞书卡片使用）
                data['geo_data'] = build_geo_summary(geo_records)

                # 写入飞书多维表格
                token = get_tenant_access_token()
                if token:
                    table_map = get_table_ids(token)
                    geo_table_id = table_map.get("GEO 品牌提及追踪")
                    if geo_table_id:
                        push_geo_to_bitable(geo_records, token, geo_table_id)
                    else:
                        print("[WARN] 未找到「GEO 品牌提及追踪」表，请检查多维表格中的表名")
                else:
                    print("[WARN] 获取飞书 Token 失败，跳过 GEO 表写入")

                # 打印摘要
                summary = data['geo_data']
                print(f"  🤖 AI 引荐总会话: {summary['total_sessions']}")
                for src, cnt in sorted(summary['by_source'].items(), key=lambda x: -x[1]):
                    print(f"     • {src}: {cnt} 会话")
            else:
                print("  ℹ️ 本期暂无 AI 引擎引荐流量")

        except Exception as e:
            print(f"[WARN] GA4 AI 可见度追踪失败（不影响主报告）: {e}")
    else:
        print("  ℹ️ GA4 未启用，跳过 AI 可见度追踪（config.py 中设置 GA4_ENABLED = True）")

    print(f"\n✅ 完成！已安全推送到飞书群组与多维表格。")
    return True

def main():
    parser = argparse.ArgumentParser(description='GSC 自动报告系统 v5')
    parser.add_argument('--type', '-t', choices=['daily', 'weekly', 'monthly'])
    parser.add_argument('--auto', '-a', action='store_true')
    args = parser.parse_args()

    if args.auto:
        report_type = determine_report_type()
        print(f"[AUTO] 自动判断: {report_type}")
    elif args.type:
        report_type = args.type
    else:
        parser.print_help()
        sys.exit(1)

    try:
        run(report_type)
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
