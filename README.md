# GSC 自动报告系统 v4

## 📦 部署步骤

1. 把旧项目的 `client_secret.json` 和 `token.json` 复制到本目录
2. 编辑 `config.py`，填入你的 `FEISHU_WEBHOOK` 地址
3. 安装依赖: `pip install -r requirements.txt`
4. 手动测试:
   ```
   python main.py --type daily
   python main.py --type weekly
   python main.py --type monthly
   ```
5. 管理员身份运行 `setup_scheduler.bat` 安装定时任务

## 📁 文件结构
```
gsc-report-v4/
├── config.py              # 配置
├── main.py                # 主入口 (5步流程)
├── gsc_client.py          # GSC API (searchconsole v1 + 小写方法名)
├── report_generator.py    # HTML 看板 (全新 v4 设计)
├── feishu_push.py         # 飞书卡片推送
├── seo_diagnostics.py     # SEO 诊断 (8类自动分析)
├── setup_scheduler.bat    # Windows 定时任务
├── requirements.txt
├── client_secret.json     # ← 从旧项目复制
├── token.json             # ← 从旧项目复制
└── reports/               # 生成的报告
```

## ⏰ 定时任务
| 类型 | 时间 (北京时间) | 命令 |
|------|----------------|------|
| 日报 | 每天 09:00     | `python main.py --type daily` |
| 周报 | 每周日 12:00   | `python main.py --type weekly` |
| 月报 | 每月最后一天 09:00 | `python main.py --type monthly` |

## 🆕 v4 改进
- **SEO 健康评分**: 顶部评分环，综合 CTR/排名/索引/流量趋势
- **环比趋势对比**: 图表叠加上期虚线，一眼看出变化
- **CTR 颜色标注**: 关键词表格 CTR 列 红/黄/绿 直观区分
- **入场动画**: fadeUp + slideIn + barGrow 提升专业感
- **Plus Jakarta Sans**: 替换通用字体，更高端的排版
- **API 修复**: searchconsole v1 + 小写 searchanalytics()
- **诊断升级**: 8 类诊断 + 具体操作步骤
