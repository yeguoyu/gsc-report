"""
SEO 深度诊断模块 v5
逐关键词、逐页面级分析，给出：
- 具体是哪个词/哪个页面有问题
- 问题的根因分析
- 谁来做（内容/技术/运营）
- 具体怎么做（步骤级）
- 预期效果
"""

import config


def _row_key(row, index=0):
    keys = row.get('keys', [])
    return keys[index] if len(keys) > index else ''


def _short_url(url):
    return str(url).replace(config.SITE_URL, '/')


def _add_query_page_diagnostics(diagnostics, query_pages):
    by_query = {}
    for row in query_pages:
        query = _row_key(row, 0)
        page = _row_key(row, 1)
        if not query or not page:
            continue
        if row.get('impressions', 0) < 20:
            continue
        by_query.setdefault(query, []).append(row)

    cannibalized = []
    for query, rows in by_query.items():
        if len(rows) < 2:
            continue
        total_clicks = sum(r.get('clicks', 0) for r in rows)
        total_impressions = sum(r.get('impressions', 0) for r in rows)
        if total_impressions < 100:
            continue

        rows_sorted = sorted(rows, key=lambda r: (r.get('clicks', 0), r.get('impressions', 0)), reverse=True)
        leader = rows_sorted[0]
        leader_metric = leader.get('clicks', 0) if total_clicks else leader.get('impressions', 0)
        total_metric = total_clicks if total_clicks else total_impressions
        leader_share = leader_metric / total_metric if total_metric else 1

        if leader_share < 0.75:
            cannibalized.append({
                'query': query,
                'pages': rows_sorted[:3],
                'total_clicks': total_clicks,
                'total_impressions': total_impressions,
                'leader_share': leader_share,
            })

    cannibalized.sort(key=lambda x: (x['total_clicks'], x['total_impressions']), reverse=True)
    if not cannibalized:
        return

    detail = "这些关键词的点击/展示分散在多个页面，建议确认主排名页，避免内容互相抢排名：\n"
    for item in cannibalized[:5]:
        detail += f"\n    - {item['query']} | clicks {item['total_clicks']} | impressions {item['total_impressions']:,} | main share {item['leader_share']:.0%}"
        for page_row in item['pages']:
            detail += (
                f"\n      · {_short_url(_row_key(page_row, 1))}"
                f" | clicks {page_row.get('clicks', 0)}"
                f" | impressions {page_row.get('impressions', 0):,}"
                f" | pos {page_row.get('position', 0):.1f}"
            )

    diagnostics.append({
        'severity': 'medium',
        'category': '关键词页面分流',
        'message': f'{len(cannibalized)} 个关键词可能存在页面内耗/意图分散',
        'detail': detail,
        'owner': 'SEO + 内容团队',
        'actions': [
            '为每个关键词指定唯一主页面，并把重复页面合并、canonical 或改成补充长尾意图',
            '把分流页面的内链锚文本统一指向主页面，减少页面之间互抢排名',
            '检查主页面标题、H1、首屏内容是否覆盖该关键词的主要搜索意图',
        ],
        'expected': '减少页面内耗后，主页面排名和 CTR 通常比新增内容更快见效。',
    })


def _add_country_device_diagnostics(diagnostics, country_devices):
    target_markets = {'usa', 'can', 'gbr', 'deu', 'fra', 'ita', 'esp', 'nld'}
    by_country = {}
    for row in country_devices:
        country = _row_key(row, 0).lower()
        device = _row_key(row, 1).upper()
        if country not in target_markets or device not in {'MOBILE', 'DESKTOP'}:
            continue
        by_country.setdefault(country, {})[device] = row

    weak_mobile = []
    for country, devices in by_country.items():
        mobile = devices.get('MOBILE')
        desktop = devices.get('DESKTOP')
        if not mobile or not desktop:
            continue
        if mobile.get('impressions', 0) < 50 or desktop.get('impressions', 0) < 20:
            continue
        mobile_ctr = mobile.get('ctr', 0)
        desktop_ctr = desktop.get('ctr', 0)
        if desktop_ctr > 0 and mobile_ctr < desktop_ctr * 0.7:
            weak_mobile.append({
                'country': country.upper(),
                'mobile_ctr': mobile_ctr,
                'desktop_ctr': desktop_ctr,
                'mobile_clicks': mobile.get('clicks', 0),
                'mobile_impressions': mobile.get('impressions', 0),
                'desktop_clicks': desktop.get('clicks', 0),
                'desktop_impressions': desktop.get('impressions', 0),
            })

    weak_mobile.sort(key=lambda x: x['mobile_impressions'], reverse=True)
    if not weak_mobile:
        return

    detail = "核心市场移动端 CTR 明显弱于桌面端，优先检查移动端标题展示、摘要截断和页面体验：\n"
    for item in weak_mobile[:6]:
        detail += (
            f"\n    - {item['country']} | mobile CTR {item['mobile_ctr']*100:.2f}%"
            f" vs desktop {item['desktop_ctr']*100:.2f}%"
            f" | mobile impressions {item['mobile_impressions']:,}"
        )

    diagnostics.append({
        'severity': 'medium',
        'category': '核心市场移动端异常',
        'message': f'{len(weak_mobile)} 个核心市场移动端 CTR 明显低于桌面端',
        'detail': detail,
        'owner': 'SEO + 前端/内容团队',
        'actions': [
            '用移动端 SERP 检查标题是否被截断，优先把核心卖点放在标题前 30 个字符',
            '检查移动端首屏加载和主要内容是否足够快、足够直接',
            '为核心市场页面补充本地化措辞、价格/配送/使用场景等更强点击理由',
        ],
        'expected': '移动端 CTR 修复会直接放大核心市场流量，尤其适合优先处理高展示国家。',
    })


def _add_search_appearance_diagnostics(diagnostics, search_appearance):
    if not search_appearance:
        return

    total_clicks = sum(r.get('clicks', 0) for r in search_appearance)
    total_impressions = sum(r.get('impressions', 0) for r in search_appearance)
    if total_impressions <= 0:
        return

    rows = sorted(search_appearance, key=lambda r: r.get('impressions', 0), reverse=True)
    detail = "当前搜索外观分布：\n"
    for row in rows[:8]:
        label = _row_key(row, 0)
        detail += (
            f"\n    - {label}: clicks {row.get('clicks', 0)}"
            f" | impressions {row.get('impressions', 0):,}"
            f" | CTR {row.get('ctr', 0)*100:.2f}%"
        )

    diagnostics.append({
        'severity': 'low',
        'category': '搜索外观机会',
        'message': f'已拉取 {len(search_appearance)} 类搜索外观，可用于判断结构化数据机会',
        'detail': detail,
        'owner': 'SEO + 技术团队',
        'actions': [
            '对产品页补 Product、Review、FAQ 结构化数据，争取更丰富的搜索结果展示',
            '对教程类内容补 HowTo/FAQ，并观察 searchAppearance 变化',
            '把搜索外观 CTR 低的类型与普通结果 CTR 对比，判断是否需要改标题摘要',
        ],
        'expected': '结构化数据不会保证富结果，但能提高获得富结果和更高 CTR 的概率。',
    })


def run_diagnostics(data):
    """全面 SEO 深度诊断（根据报告类型自动过滤）"""
    report_type = data.get('report_type', 'daily')
    diagnostics = []

    totals = data.get('totals', {})
    prev_totals = data.get('prev_totals', {})
    queries = data.get('queries', [])
    queries_prev = data.get('queries_prev', [])
    pages = data.get('pages', [])
    pages_prev = data.get('pages_prev', [])
    devices = data.get('devices', [])
    countries = data.get('countries', [])
    query_pages = data.get('query_pages', [])
    country_devices = data.get('country_devices', [])
    search_appearance = data.get('search_appearance', [])

    prev_q_map = {r['keys'][0]: r for r in queries_prev}
    prev_p_map = {r['keys'][0]: r for r in pages_prev}
    _add_query_page_diagnostics(diagnostics, query_pages)
    _add_country_device_diagnostics(diagnostics, country_devices)
    _add_search_appearance_diagnostics(diagnostics, search_appearance)

    # ═══════════════════════════════════════════
    # 1. 流量异常 - 精确到哪些词/页面导致下降
    # ═══════════════════════════════════════════
    if prev_totals.get('clicks', 0) > 0:
        click_change = (totals.get('clicks', 0) - prev_totals['clicks']) / prev_totals['clicks'] * 100

        if click_change < -10:
            drop_keywords = []
            for q in queries:
                kw = q['keys'][0]
                pq = prev_q_map.get(kw, {})
                if pq.get('clicks', 0) > 0:
                    diff = q.get('clicks', 0) - pq['clicks']
                    if diff < 0:
                        drop_keywords.append({
                            'keyword': kw,
                            'current_clicks': q.get('clicks', 0),
                            'prev_clicks': pq['clicks'],
                            'diff': diff,
                            'current_pos': q.get('position', 0),
                            'prev_pos': pq.get('position', 0),
                        })
            drop_keywords.sort(key=lambda x: x['diff'])

            drop_pages = []
            for p in pages:
                url = p['keys'][0]
                pp = prev_p_map.get(url, {})
                if pp.get('clicks', 0) > 0:
                    diff = p.get('clicks', 0) - pp['clicks']
                    if diff < 0:
                        short_url = url.replace(config.SITE_URL, '/')
                        drop_pages.append({'url': short_url, 'full_url': url, 'current_clicks': p.get('clicks', 0), 'prev_clicks': pp['clicks'], 'diff': diff})
            drop_pages.sort(key=lambda x: x['diff'])

            severity = 'high' if click_change < -20 else 'medium'
            kw_detail = ""
            for k in drop_keywords[:5]:
                pos_txt = f"排名 {k['prev_pos']:.1f}→{k['current_pos']:.1f}" if k['prev_pos'] > 0 else ""
                kw_detail += f"\n    • 「{k['keyword']}」点击 {k['prev_clicks']}→{k['current_clicks']}（{k['diff']:+d}）{pos_txt}"
            pg_detail = ""
            for p in drop_pages[:3]:
                pg_detail += f"\n    • {p['url']}  点击 {p['prev_clicks']}→{p['current_clicks']}（{p['diff']:+d}）"

            diagnostics.append({
                'severity': severity,
                'category': '流量下降',
                'message': f'点击量环比下降 {abs(click_change):.1f}%（{prev_totals["clicks"]}→{totals.get("clicks",0)}）',
                'detail': f'下降最多的关键词：{kw_detail}\n\n    下降最多的页面：{pg_detail}',
                'owner': '内容团队 + SEO 负责人',
                'actions': [
                    f'【立即】打开 GSC 逐一检查以上 {len(drop_keywords[:5])} 个下降关键词的排名变化，确认是排名下滑还是搜索量季节性波动',
                    '【立即】检查以上下降页面是否有技术问题：打开 Chrome DevTools → Network 确认状态码是否 200，加载时间是否 < 3 秒',
                    '【当天】在 Google 搜索这些关键词，观察竞争对手 SERP 变化：是否有新竞品入场、是否有广告挤占、是否出现精选摘要',
                    '【本周】检查 Google Search Status Dashboard 确认是否有算法更新',
                    '【本周】对排名下降的页面：更新内容加入最新数据/案例，优化 H1 和前 200 字包含核心关键词',
                ],
                'expected': f'如果是排名下滑导致，优化后 1-2 周内可恢复；如果是算法更新需要更长时间调整内容策略',
            })

        elif click_change > 20:
            grow_keywords = []
            for q in queries:
                kw = q['keys'][0]
                pq = prev_q_map.get(kw, {})
                diff = q.get('clicks', 0) - pq.get('clicks', 0)
                if diff > 0:
                    grow_keywords.append({'keyword': kw, 'diff': diff, 'clicks': q.get('clicks', 0)})
            grow_keywords.sort(key=lambda x: x['diff'], reverse=True)
            kw_detail = ""
            for k in grow_keywords[:5]:
                kw_detail += f"\n    • 「{k['keyword']}」新增 +{k['diff']} 次点击（当前 {k['clicks']}）"

            diagnostics.append({
                'severity': 'low',
                'category': '流量增长',
                'message': f'🎉 点击量环比增长 {click_change:.1f}%（{prev_totals["clicks"]}→{totals.get("clicks",0)}）',
                'detail': f'增长贡献最大的关键词：{kw_detail}',
                'owner': '内容团队',
                'actions': [
                    '【本周】分析以上增长词对应页面的内容特征（结构、字数、多媒体、内链数量），总结为可复制的内容模板',
                    '【本周】对增长页面补充 3-5 个相关内链，将权重传导给其他弱势页面',
                    '【下周】根据增长关键词拓展长尾词，创建 2-3 篇同类主题新文章',
                ],
                'expected': '复制成功模式可带动 15-30% 的额外流量增长',
            })

    # ═══════════════════════════════════════════
    # 2. 逐词 CTR 分析
    # ═══════════════════════════════════════════
    wasted_keywords = []
    for q in queries:
        imp = q.get('impressions', 0)
        ctr = q.get('ctr', 0)
        pos = q.get('position', 0)
        if imp >= 50 and ctr < 0.02 and pos <= 20:
            wasted = max(0, int(imp * 0.05) - q.get('clicks', 0))
            wasted_keywords.append({
                'keyword': q['keys'][0], 'impressions': imp, 'clicks': q.get('clicks', 0),
                'ctr': ctr * 100, 'position': pos, 'wasted_potential': wasted,
            })
    wasted_keywords.sort(key=lambda x: x['wasted_potential'], reverse=True)

    if wasted_keywords:
        total_wasted = sum(k['wasted_potential'] for k in wasted_keywords)
        detail = f"如果将这些词的 CTR 提升到 5%，预计可多获得 {total_wasted:,} 次点击\n"
        for k in wasted_keywords[:8]:
            detail += f"\n    • 「{k['keyword']}」展示 {k['impressions']:,} | 点击 {k['clicks']} | CTR {k['ctr']:.1f}% | 排名 {k['position']:.1f} | 浪费 ≈{k['wasted_potential']} 次点击"

        diagnostics.append({
            'severity': 'high',
            'category': '高展示低点击',
            'message': f'{len(wasted_keywords)} 个关键词 CTR<2%，预估浪费 {total_wasted:,} 次潜在点击',
            'detail': detail,
            'owner': '内容团队（改标题描述）+ 技术团队（加结构化数据）',
            'actions': [
                f'【优先级最高】逐一优化以上 {min(len(wasted_keywords), 8)} 个词对应页面的 Title Tag：\n      - 前 30 字必须包含核心关键词\n      - 加入数字和年份（如 "2026最新"、"Top 10"）\n      - 加入利益点（如 "免费"、"对比评测"、"一文搞懂"）',
                '【优先级最高】优化 Meta Description（150-160 字符）：\n      - 第一句话直接回答搜索意图\n      - 中间突出差异化卖点\n      - 末尾加 CTA（如 "立即查看"）',
                '【本周】Google 搜索这些关键词，截图 SERP 前 5 名标题写法做对比分析',
                '【本周】技术团队添加 FAQ Schema / HowTo Schema 结构化数据争取富媒体搜索结果',
                '【下周】在 GSC 检查这些页面的实际显示标题（Google 可能重写了 Title）',
            ],
            'expected': f'Title 优化通常 1-3 周见效，CTR 从 2% 提升到 5% 意味着点击量翻 2.5 倍',
        })

    # ═══════════════════════════════════════════
    # 3. 潜力词冲刺 Top 5
    # ═══════════════════════════════════════════
    potential_kws = []
    for q in queries:
        pos = q.get('position', 99)
        imp = q.get('impressions', 0)
        if 5 <= pos <= 20 and imp >= 30:
            gain = max(0, int(imp * (0.10 - q.get('ctr', 0))))
            potential_kws.append({
                'keyword': q['keys'][0], 'position': pos, 'impressions': imp,
                'clicks': q.get('clicks', 0), 'potential_gain': gain,
            })
    potential_kws.sort(key=lambda x: x['potential_gain'], reverse=True)

    if potential_kws:
        total_potential = sum(k['potential_gain'] for k in potential_kws)
        detail = f"冲进 Top 3 后预计可增加 {total_potential:,} 次点击\n"
        for k in potential_kws[:8]:
            detail += f"\n    • 「{k['keyword']}」排名 {k['position']:.1f} | 展示 {k['impressions']:,} | 点击 {k['clicks']} | 冲Top3预估 +{k['potential_gain']}"

        diagnostics.append({
            'severity': 'medium',
            'category': '排名冲刺机会',
            'message': f'{len(potential_kws)} 个词排名 5-20，冲进 Top 3 可增加 {total_potential:,} 次点击',
            'detail': detail,
            'owner': '内容团队（优化）+ 外链团队（权重提升）',
            'actions': [
                f'【本周】对排名最高的 {min(len(potential_kws),5)} 个词执行页面加强：\n      - 文章字数 > 1500 字\n      - H2/H3 标题自然融入关键词变体\n      - 添加图表、表格、视频等多媒体\n      - 增加 FAQ 段落覆盖常见问题',
                '【本周】从站内 3-5 个高权重页面添加锚文本内链到目标页面',
                '【本月】为 Top 3 目标词获取 2-3 个高质量外链：Guest Post / Quora / 行业目录',
                '【持续】每周在 GSC 跟踪排名变化，进入 Top 5 后重点观察 CTR',
            ],
            'expected': '内容+内链 2-4 周见效，外链 1-3 个月；每个词进入 Top 3 约带来 3-5 倍点击增长',
        })

    # ═══════════════════════════════════════════
    # 4. 逐页面性能诊断
    # ═══════════════════════════════════════════
    underperform = []
    if pages:
        avg_ctr = totals.get('ctr', 0)
        for p in pages:
            if p.get('impressions', 0) >= 50 and p.get('ctr', 0) < avg_ctr * 0.5 and p.get('position', 99) <= 20:
                short = p['keys'][0].replace(config.SITE_URL, '/')
                underperform.append({
                    'url': short, 'full_url': p['keys'][0], 'impressions': p.get('impressions', 0),
                    'clicks': p.get('clicks', 0), 'ctr': p.get('ctr', 0) * 100, 'avg_ctr': avg_ctr * 100,
                    'position': p.get('position', 0),
                })
        underperform.sort(key=lambda x: x['impressions'], reverse=True)

    if underperform:
        detail = f"全站均值 CTR {avg_ctr*100:.2f}%，以下页面 CTR 不足均值一半：\n"
        for p in underperform[:5]:
            detail += f"\n    • {p['url']}\n      展示 {p['impressions']:,} | 点击 {p['clicks']} | CTR {p['ctr']:.1f}%（均值{p['avg_ctr']:.1f}%）| 排名 {p['position']:.1f}"

        diagnostics.append({
            'severity': 'medium',
            'category': '页面CTR不佳',
            'message': f'{len(underperform)} 个页面 CTR 不到全站均值一半',
            'detail': detail,
            'owner': '内容团队',
            'actions': [
                '【本周】逐一检查这些页面：标题是否准确反映内容？首屏是否直接回答搜索意图？是否有大量弹窗影响体验？',
                '【本周】Google 搜索目标关键词，对比排名前 3 竞品的标题和描述，找差距',
                '【下周】重写 Title 和 Meta Description，每次只改一个页面观察 2 周效果',
            ],
            'expected': '单页面 CTR 优化空间 50-200%，排名不变也能大幅增加点击',
        })

    # ═══════════════════════════════════════════
    # 5. 设备端差异
    # ═══════════════════════════════════════════
    if devices:
        dev = {d['keys'][0]: d for d in devices}
        total_dev = sum(d.get('clicks', 0) for d in devices)
        mobile = dev.get('MOBILE', {})
        desktop = dev.get('DESKTOP', {})
        if total_dev > 0 and mobile and desktop:
            m_ctr = mobile.get('ctr', 0) * 100
            d_ctr = desktop.get('ctr', 0) * 100
            ctr_gap = d_ctr - m_ctr
            pos_gap = mobile.get('position', 0) - desktop.get('position', 0)

            if ctr_gap > 1 or pos_gap > 2:
                issues = []
                if ctr_gap > 1:
                    issues.append(f"移动端 CTR {m_ctr:.2f}% 比桌面端 {d_ctr:.2f}% 低 {ctr_gap:.1f}pp")
                if pos_gap > 2:
                    issues.append(f"移动端排名 {mobile.get('position',0):.1f} 比桌面端 {desktop.get('position',0):.1f} 差 {pos_gap:.1f} 位")

                detail = f"移动端：点击 {mobile.get('clicks',0):,} | CTR {m_ctr:.2f}% | 排名 {mobile.get('position',0):.1f}\n    桌面端：点击 {desktop.get('clicks',0):,} | CTR {d_ctr:.2f}% | 排名 {desktop.get('position',0):.1f}"

                diagnostics.append({
                    'severity': 'medium',
                    'category': '移动端差距',
                    'message': '；'.join(issues),
                    'detail': detail,
                    'owner': '技术团队（性能）+ 内容团队（适配）',
                    'actions': [
                        '【立即】用 PageSpeed Insights 测试首页+Top 5 页面的移动端得分',
                        '【本周】技术团队修复：LCP<2.5秒、CLS<0.1、图片 WebP+懒加载、启用 CDN',
                        '【本周】手机打开 Top 10 页面检查：字体≥16px？按钮间距≥48px？无水平滚动？',
                    ],
                    'expected': '移动端优化后排名 2-4 周改善，CTR 提升 10-30%',
                })

    # ═══════════════════════════════════════════
    # 6. 索引问题逐URL
    # ═══════════════════════════════════════════
    idx = data.get('index_issues', {})
    if idx:
        crawled = idx.get('crawled_not_indexed', [])
        if crawled:
            urls = ""
            for u in crawled[:8]:
                short = u['url'].replace(config.SITE_URL, '/')
                urls += f"\n    • {short}  （最后抓取: {u.get('crawl_time','N/A')[:10]}）"

            diagnostics.append({
                'severity': 'high',
                'category': '已抓取未索引',
                'message': f'{len(crawled)} 个页面被 Google 抓取但拒绝索引',
                'detail': f'Google 认为质量不够或内容重复：{urls}',
                'owner': '内容团队 + 技术团队',
                'actions': [
                    '【本周】逐一检查内容质量：正文>800字？有独特价值？有专业观点/数据/案例？',
                    '【本周】用 Siteliner.com 检查是否与站内其他页面大面积重复',
                    '【有价值的页面】丰富到 1500+ 字 → 加原创图表 → 加内链 → GSC 手动提交索引',
                    '【低质量/重复的页面】合并到主题相近的页面 → 301 重定向 → 或 noindex',
                ],
                'expected': '手动提交索引后 1-7 天重新评估，内容加强后索引通过率 60-80%',
            })

        err404 = idx.get('not_found_404', [])
        if err404:
            urls = ""
            for u in err404[:8]:
                urls += f"\n    • {u['url'].replace(config.SITE_URL, '/')}"
            diagnostics.append({
                'severity': 'high' if len(err404) > 5 else 'medium',
                'category': '404 死链',
                'message': f'{len(err404)} 个页面返回 404 错误',
                'detail': f'以下 URL 无法访问：{urls}',
                'owner': '技术团队',
                'actions': [
                    '【立即】检查这些 URL 之前是否有流量（GSC 搜索查看历史数据）',
                    '【本周】有历史流量的 → 301 重定向到最相关的现存页面',
                    '【本周】sitemap.xml 移除所有 404 URL 并重新提交',
                    '【本周】全站搜索指向 404 的内链并修改为正确链接',
                ],
                'expected': '修复后可回收链接权重，抓取效率提升 10-20%',
            })

        robots = idx.get('blocked_robots', [])
        if robots:
            urls = ""
            for u in robots[:5]:
                urls += f"\n    • {u['url'].replace(config.SITE_URL, '/')}"
            diagnostics.append({
                'severity': 'medium',
                'category': 'Robots.txt 屏蔽',
                'message': f'{len(robots)} 个页面被 robots.txt 屏蔽',
                'detail': f'无法被 Google 抓取：{urls}',
                'owner': '技术团队',
                'actions': [
                    '【立即】检查 robots.txt 的 Disallow 规则',
                    '【如果误封】修改 robots.txt 移除错误规则',
                    '【如果故意屏蔽】确认这些页面确实不需要索引',
                ],
                'expected': '修改后 Google 通常 1-3 天重新抓取',
            })

    # ═══════════════════════════════════════════
    # 7. 流量集中度
    # ═══════════════════════════════════════════
    if pages and len(pages) > 3:
        sorted_p = sorted(pages, key=lambda x: x.get('clicks', 0), reverse=True)
        tc = sum(p.get('clicks', 0) for p in pages)
        if tc > 0:
            t1 = sorted_p[0].get('clicks', 0) / tc * 100
            t3 = sum(p.get('clicks', 0) for p in sorted_p[:3]) / tc * 100
            if t1 > 40 or t3 > 70:
                detail = "流量分布：\n"
                for i, p in enumerate(sorted_p[:5], 1):
                    short = p['keys'][0].replace(config.SITE_URL, '/')
                    pct = p.get('clicks', 0) / tc * 100
                    detail += f"    {i}. {short} — {p.get('clicks',0):,} 次（{pct:.1f}%）\n"
                diagnostics.append({
                    'severity': 'medium',
                    'category': '流量过度集中',
                    'message': f'Top1 占比 {t1:.0f}%，Top3 占比 {t3:.0f}%',
                    'detail': detail,
                    'owner': '内容团队 + SEO 负责人',
                    'actions': [
                        '【本月】制定内容日历，计划 5-10 篇围绕不同关键词集群的新文章',
                        '【本月】对 Top1 页面做长尾词挖掘，拓展 20+ 个相关话题创建专题文章',
                        '【持续】监控 Top1 占比，目标降到 30% 以下',
                    ],
                    'expected': '内容扩展 2-3 个月后集中度可降低 15-25pp',
                })

    # ═══════════════════════════════════════════
    # 8. 地域分布
    # ═══════════════════════════════════════════
    if countries and len(countries) >= 2:
        tg = sum(c.get('clicks', 0) for c in countries)
        if tg > 0:
            names = getattr(config, 'COUNTRY_NAMES', {})
            detail = "地域分布：\n"
            for c in countries[:8]:
                code = c['keys'][0].lower()
                nm = names.get(code, c['keys'][0].upper())
                pct = c.get('clicks', 0) / tg * 100
                detail += f"    • {nm}（{c['keys'][0].upper()}）— {c.get('clicks',0):,} 次（{pct:.1f}%）\n"
            diagnostics.append({
                'severity': 'low',
                'category': '地域分布',
                'message': f'流量覆盖 {len(countries)} 个国家/地区',
                'detail': detail,
                'owner': '运营团队',
                'actions': [
                    '确认分布是否符合业务目标市场',
                    '目标市场占比低 → 检查 hreflang、创建本地化内容、获取本地外链',
                    '非目标市场占比高 → 评估是否有转化价值',
                ],
                'expected': '地域优化 3-6 个月见效',
            })

    # ═══════════════════════════════════════════
    # 9. 新增/丢失关键词（去噪：过滤低点击波动）
    # ═══════════════════════════════════════════
    new_kw_min = getattr(config, 'NEW_KW_MIN_CLICKS', 3)
    lost_kw_min = getattr(config, 'LOST_KW_MIN_CLICKS', 3)

    cur_kw_map = {q['keys'][0]: q for q in queries}
    pre_kw_map = {q['keys'][0]: q for q in queries_prev}
    cur_kws = set(cur_kw_map.keys())
    pre_kws = set(pre_kw_map.keys())

    # 新增词：本期有、上期无，且本期点击 >= 阈值
    new_kws = {kw for kw in (cur_kws - pre_kws) if cur_kw_map[kw].get('clicks', 0) >= new_kw_min}
    # 丢失词：上期有、本期无，且上期点击 >= 阈值
    lost_kws = {kw for kw in (pre_kws - cur_kws) if pre_kw_map[kw].get('clicks', 0) >= lost_kw_min}

    if new_kws or lost_kws:
        detail = ""
        if new_kws:
            nwd = sorted([q for q in queries if q['keys'][0] in new_kws], key=lambda x: x.get('clicks', 0), reverse=True)
            detail += f"新增 {len(new_kws)} 个有效关键词（≥{new_kw_min}次点击）：\n"
            for k in nwd[:5]:
                detail += f"    ✅ 「{k['keys'][0]}」点击 {k.get('clicks',0)} | 展示 {k.get('impressions',0)} | 排名 {k.get('position',0):.1f}\n"
        if lost_kws:
            lwd = sorted([q for q in queries_prev if q['keys'][0] in lost_kws], key=lambda x: x.get('clicks', 0), reverse=True)
            detail += f"\n丢失 {len(lost_kws)} 个有效关键词（上期≥{lost_kw_min}次点击）：\n"
            for k in lwd[:5]:
                detail += f"    ❌ 「{k['keys'][0]}」上期点击 {k.get('clicks',0)} | 展示 {k.get('impressions',0)}\n"

        lost_clicks = sum(pre_kw_map[kw].get('clicks', 0) for kw in lost_kws)
        severity = 'high' if len(lost_kws) > 5 and lost_clicks > 20 else 'low'
        diagnostics.append({
            'severity': severity,
            'category': '关键词变动',
            'message': f'新增 {len(new_kws)} 个词，丢失 {len(lost_kws)} 个词',
            'detail': detail,
            'owner': '内容团队',
            'actions': [
                '【对新增词】确认哪些页面带来新排名，强化其内容和内链',
                '【对丢失词】GSC 搜索检查对应页面是否存在、排名是否跌出 100 名',
                '【高价值丢失词】立即检查页面技术问题，必要时重新优化并手动提交索引',
            ],
            'expected': '关键词波动正常，但高价值词丢失需 1 周内处理',
        })

    # ═══════════════════════════════════════════
    # 按报告类型过滤诊断项
    # 日报：仅保留可当天排查的紧急问题
    # 周报：保留战术级建议
    # 月报：全部保留（含长期策略）
    # ═══════════════════════════════════════════
    if report_type == 'daily':
        # 日报只保留 high 和流量下降/404/索引异常等紧急项
        daily_categories = {'流量下降', '已抓取未索引', '404 死链', 'Robots.txt 屏蔽', '关键词变动'}
        diagnostics = [d for d in diagnostics if d['severity'] == 'high' or d['category'] in daily_categories]
    elif report_type == 'weekly':
        # 周报过滤掉纯信息性的低优先级项（如地域分布）
        weekly_skip = {'地域分布'}
        diagnostics = [d for d in diagnostics if d['category'] not in weekly_skip or d['severity'] != 'low']

    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    diagnostics.sort(key=lambda x: severity_order.get(x.get('severity', ''), 3))
    return diagnostics
