# GSC 报告优化说明

## 本次已优化

1. 多维表格写入从 Top 200 改为 Top 100。

   - `关键词历史表现` 默认写入点击量 Top 100。
   - `页面历史表现` 默认写入点击量 Top 100。
   - 可在 GitHub Actions Variables 中调整：
     - `BITABLE_TOP_QUERIES`
     - `BITABLE_TOP_PAGES`

2. Search Analytics 拉取改为分页模式。

   旧逻辑只请求 `startRow=0` 的第一页。新逻辑会根据 `rowLimit` 和 `startRow` 分页拉取，最多单页 25,000 行，减少数据被第一页截断的风险。

3. 新增 GSC 组合维度。

   - `query_pages`: `query + page`
   - `query_pages_prev`: 上期 `query + page`
   - `country_devices`: `country + device`
   - `search_appearance`: `searchAppearance`
   - `fetch_summary`: 本次各维度抓取行数与上限摘要

4. 新增诊断项。

   - `关键词页面分流`: 找出同一关键词被多个页面共同承接的情况，用于判断页面内耗、canonical、合并内容或内链收口。
   - `核心市场移动端异常`: 找出美国、德国、日本、挪威及主要欧洲市场里，移动端 CTR 明显弱于桌面端的国家。
   - `搜索外观机会`: 记录当前搜索外观分布，用于后续评估 Product、FAQ、HowTo、Review 等结构化数据机会。

## 当前 GSC 数据口径

当前报告主要围绕 Web Search 数据生成：

- 趋势：`date`
- 关键词：`query`
- 页面：`page`
- 设备：`device`
- 国家：`country`
- 关键词页面组合：`query + page`
- 国家设备组合：`country + device`
- 搜索外观：`searchAppearance`
- 站点地图：`sitemaps`
- 抽样索引检查：URL Inspection API 检查低展示页面前 30 个

当前默认限制：

- `ALL_QUERIES_LIMIT = 5000`
- `ALL_PAGES_LIMIT = 2000`
- `QUERY_PAGE_LIMIT = 2000`
- `COUNTRY_DEVICE_LIMIT = 1000`
- `SEARCH_APPEARANCE_LIMIT = 1000`
- `GSC_API_PAGE_SIZE = 25000`
- `GSC_SEARCH_TYPE = web`

这些都可以在 GitHub Actions Variables 中配置。

## 完整度判断

这套数据已经足够做周报、月报、Top 机会分析和异常提醒，但还不是完整的 GSC 数据仓库。

原因是 Google Search Analytics API 返回的是聚合后的 top rows。官方接口支持 `rowLimit` 和 `startRow`，但数据仍受 Search Console 聚合与隐私/内部限制影响。参考文档：

- [Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [URL Inspection API inspect](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)

URL Inspection API 适合抽样诊断索引状态，不适合当作全站索引覆盖全量数据源。

## 建议的数据分析方向

### 1. 机会优先级

优先看：

- 展示高、CTR 低、排名在 1-20 的关键词
- 排名 5-20、展示高的冲刺词
- 核心国家移动端 CTR 异常低的页面
- 同一关键词被多个页面分流的关键词

建议评分：

```text
机会分 = 展示量 * 目标CTR - 当前点击量
```

目标 CTR 可按排名段粗略设置：

```text
1-3名: 15%-30%
4-10名: 5%-12%
11-20名: 2%-6%
20名以后: 1%-3%
```

### 2. 内容内耗

如果 `query + page` 显示同一个关键词分散到多个页面：

- 保留一个主页面
- 弱相关页面改成长尾意图
- 重复内容合并或 canonical
- 内链锚文本统一指向主页面

### 3. 核心市场

核心市场建议重点盯：

```text
USA, DEU, JPN, NOR, GBR, FRA, ITA, ESP, NLD, SWE, FIN, DNK, CHE, AUT, BEL, POL, PRT, IRL, CZE, HUN
```

如果移动端 CTR 明显低于桌面端：

- 检查移动端标题是否截断
- 把核心卖点放在标题前 30 个字符
- 检查移动端首屏速度与内容直接性
- 增加国家本地化措辞，如配送、认证、价格、使用场景

### 4. 搜索外观

搜索外观适合用于判断结构化数据是否带来增益：

- Product
- Review
- FAQ
- HowTo
- Video
- Image

如果搜索外观长期单一，说明结构化数据和富结果机会还没有被充分利用。

## 后续可继续做

1. 新增 `机会表` 到飞书多维表格。

   字段建议：

   - 日期
   - 关键词
   - 主页面
   - 当前排名
   - 展示量
   - 当前 CTR
   - 目标 CTR
   - 机会点击
   - 问题类型
   - 建议动作

2. 新增 `关键词页面映射表`。

   用来长期观察关键词是否稳定由同一 URL 承接。

3. 新增 `国家设备表现表`。

   用来判断核心市场移动端/桌面端差异。

4. 分搜索类型拉取。

   除 `web` 外，可额外跑：

   - `image`
   - `video`
   - `news`
   - `discover`

5. 把 HTML 报告中的诊断项拆成“问题、证据、动作、负责人、预期收益”，更适合团队执行。

## 本次 SEO 运营看板新增

已新增 `seo_ops.py`，HTML 周报/月报会自动生成 SEO Operations Snapshot：

- `Non-brand Share`：非品牌词点击占比，用来判断自然搜索是否只靠品牌词。
- `Brand Product Clicks`：品牌词里带产品型号意图的点击，例如 P1、P2、NV300、Thor 等。
- `Product Page Clicks`：Shopify `/products/` 页面带来的 GSC 点击。
- `Core-country Share`：核心国家点击占比，默认覆盖美国、德国、日本、挪威，以及主要欧洲市场。

同时新增三个运营表：

- `Keyword Segments`：把关键词拆成 Non-brand、Brand Product、Brand。
- `SEO Opportunity Pool`：按展示量、CTR、排名和页面类型筛出优先优化项。
- `Shopify Page Types`：按 Shopify URL 结构识别 Product、Collection、Blog、Page、Policy、Home 等页面类型。

当前默认品牌词来自用户提供的 Thermal Master 品牌词列表，并已去重。后续可以通过 GitHub Actions Variables 覆盖：

```text
BRAND_TERMS=thermal master,thermalmaster,thermal master p1
BRAND_PRODUCT_TERMS=p1,p2,p2 pro,p3,nv300,nv300 max,t2 max,thor,x3,camera,thermal camera,iphone,app
CORE_COUNTRIES=usa,deu,jpn,nor,gbr,fra,ita,esp,nld,swe,fin,dnk,che,aut,bel,pol,prt,irl,cze,hun
SEO_OPPORTUNITY_LIMIT=12
```
