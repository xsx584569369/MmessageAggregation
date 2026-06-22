# 存储/芯片厂商资讯汇总

监控存储/芯片厂商的最新资讯，多源聚合、本地存储。两种用法：

- **命令行** `daily_news.py`：每天手动跑一次，打印汇总 + 存 md/json。
- **桌面应用** `app.py`（PySide6）：常驻托盘、实时通知、信息流、可视化配置数据源与关键词。

---

## 桌面应用（推荐）

```bash
pip install -r requirements.txt   # 装 PySide6
python3 app.py                    # 启动
```

界面：
- 顶部工具栏：刷新 / 搜索 / 设置
- 左侧：全部消息、未读，及按国家分组的监控清单（点击筛选）
- 中间：信息流卡片（国家·公司·来源·时间，未读标「新」，命中关键词高亮），点击打开原文并标记已读
- 底部状态栏：上次刷新、条数、未读数、在线数据源数
- 托盘：关闭窗口后最小化到托盘后台刷新；有新消息弹 Windows 通知

设置里可：切换深/浅色主题、开关数据源、增删关键词（命中即高亮/强提醒）、桌面通知开关、仅关键词提醒、自动刷新间隔。左下角「＋ 管理监控公司」可在界面里增删公司（含 secid/关键词/英文名），无需改代码。

数据与持久化：
- `config.json`：界面配置 + 监控清单（含敏感偏好，**不入版本库**）
- `data/messages.json`：本地消息库，累积去重，存每条的已读/收藏状态；常驻内存、定时+退出落盘
- 抓取为多公司并发（约几秒），点击已读/收藏为就地更新（不重建列表）

> ⚠️ 安全：`cookie_ths.txt`（同花顺登录 cookie）和 `config.json` 已加入 `.gitignore`，不会进版本库。若 fork/提交本项目，请确认这两个文件未被包含。

文件分层：`daily_news.py`（抓取逻辑）→ `core.py`（配置/已读/聚合）→ `app.py`（界面）。

---

## 打包成 Windows 安装包

> ⚠️ 必须在 **Windows** 上构建：PyInstaller 不支持从 macOS/Linux 交叉编译出 Windows 程序。

把整个项目拷到一台 Windows 机器，然后：

```bat
build_win.bat
```

它会自动建虚拟环境、装 PySide6 + PyInstaller，并用 PyInstaller 打出 `dist\ChipNews\ChipNews.exe`（可直接运行的绿色版）。

要生成**正式安装包**（带开始菜单/桌面快捷方式、卸载程序）：先装 [Inno Setup](https://jrsoftware.org/isdl.php)，再运行：

```bat
iscc installer.iss
```

安装包输出在 `installer_output\芯讯_安装包_v1.0.0.exe`。

说明：
- 用户数据（`config.json` / `messages.json`）打包后写入 `%LOCALAPPDATA%\ChipNews`，卸载不会删除。
- 程序依赖系统自带的 `curl`（Windows 10 1803+ 已内置）；更老的系统需自行安装 curl。
- 图标用项目里的 `icon.ico`。

---

## 命令行用法

```bash
python3 daily_news.py            # 默认展示最近 3 天
python3 daily_news.py --days 7   # 展示最近 7 天
python3 daily_news.py --loose    # 放宽相关性（正文提到也算，更全但有噪声）
```

无需安装任何依赖：只用 Python 标准库 + 系统自带的 `curl`。

## 输出

- 终端：按「国家 / 公司」分组打印，`🆕` 标记本次新增（相对上次运行）。
- `data/YYYY-MM-DD.md`：当日 Markdown 汇总（可直接阅读）。
- `data/YYYY-MM-DD.json`：当日结构化数据。
- `data/_seen.json`：已见资讯链接，用于 `🆕` 增量标记，勿手动删（删了会把全部当成新的）。

## 监控清单

在 `daily_news.py` 顶部的 `WATCHLIST` 里增删公司即可。每家两种取数方式，二选一：

- **`secid` 不为空** → 用东方财富「个股新闻流」接口，新闻直接挂在该股下，
  效果等同同花顺 App 的「个股 → 资讯 → 新闻」列表。无需关键词过滤。
  - 格式 `市场号.代码`：`1`=沪市 `0`=深市 `105`=纳斯达克 `106`=纽交所 `116`=港股
  - 例：兆易创新 `1.603986`、江波龙 `0.301308`、美光 `105.MU`、英伟达 `105.NVDA`
- **`secid` 为空** → 用关键词搜索（东方财富无个股流的韩/日/台股及未上市公司），
  按标题命中过滤。`keyword` 尽量精确（如「南亚科技」而非「南亚」）。

新增公司想用个股流时，secid 可在 `quote.eastmoney.com` 搜到该股后看 URL，
或用东方财富搜索建议接口解析。

## 数据源（多源聚合 + 跨源去重）

每家公司会自动聚合下列可用数据源，合并后按标题去重、按时间排序。
顶部 `ENABLE` 开关可单独关闭某源（例如只要中文就把 `google`/`yahoo` 设为 `False`）。

| 源 | 接口 | 语言 | 适用 |
|---|---|---|---|
| `em_feed` 东财个股新闻流 | `np-listapi.eastmoney.com/.../getListInfo` | 中 | 有 secid 的 A股/美股，效果同同花顺个股资讯页 |
| `em_search` 东财资讯搜索 | `search-api-web.eastmoney.com/search/jsonp` | 中 | 无 secid 的韩/日/台股、未上市公司，按标题命中 |
| `google` Google News RSS | `news.google.com/rss/search` | 英 | 海外公司主力，来源权威（Nikkei/Reuters/Barron's…），也给 A股补英文 |
| `yahoo` Yahoo Finance | `query1.finance.yahoo.com/v1/finance/search` | 英 | 美股代码（NVDA/MU/SNDK）|

每家公司的 `secid`/`keyword`/`en` 字段决定启用哪些源，见 `WATCHLIST` 注释。

注意事项：
- Google News 的链接是 `news.google.com/rss/articles/...` 跳转链（点开会自动跳到原文），
  非原站直链，这是 Google RSS 的固有限制。
- 台股小厂、未上市公司中英文资讯本就少，某天为空属正常。
- **原始的「同花顺 / 富途」需求**：两家*个股*接口需 App 签名或登录态（富途还要
  quote-token），纯脚本无法稳定直取。现用东财个股流 + Google/Yahoo 提供同类且更广的内容。
  若必须原生同花顺/富途，需接浏览器自动化（Playwright + 登录）。

## 技术备注

- 东方财富对 python-requests 会做 TLS 指纹识别并返回空兜底响应，故统一改用
  系统 `curl` 发请求（见 `_http_get`）。
- 还实测过但未采用的源：财联社电报（最快但需签名，当前算法失效）、
  华尔街见闻 / 新浪 / 东财 7×24（均为综合快讯流，非个股，需关键词过滤）。
