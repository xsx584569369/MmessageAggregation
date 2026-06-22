#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储/芯片厂商每日资讯汇总脚本
--------------------------------
每天手动运行 `python3 daily_news.py` 即可拉取并展示最新资讯。

数据源说明：
- 主力引擎：东方财富资讯搜索接口（结构化、稳定，用中文名可覆盖国内外全部厂商）。
- 补充：同花顺大盘推送流，按 A 股代码匹配后标注来源为「同花顺」。
- 同花顺/富途的"原生"个股资讯需要浏览器+登录，纯脚本拿不到；
  相关适配器留了占位（见 SOURCES 区），后续接浏览器自动化可补。

输出：
- 终端打印按「国家 / 公司」分组的汇总，🆕 标记本次新增。
- data/YYYY-MM-DD.md   当日 Markdown 汇总
- data/YYYY-MM-DD.json 当日结构化数据
- data/_seen.json      已见资讯链接（用于增量标记 🆕）
"""

import json
import re
import sys
import time
import html
import datetime
import argparse
import os
import subprocess
import email.utils
from pathlib import Path
from urllib.parse import quote

# ------------------------------------------------------------------ 配置区

# 只展示最近 N 天内的资讯（含当天）
DEFAULT_DAYS_BACK = 3
# 每家公司每个源最多取多少条
MAX_PER_COMPANY = 8
# 相关性：False=仅标题命中关键词（精准，默认）；True=正文命中也算（更全但有噪声）
LOOSE_MATCH = False

# 数据源开关。想关掉某个源（比如不要英文资讯），把对应项设为 False。
#   em_feed   东方财富个股新闻流（需 secid，A股/美股）
#   em_search 东方财富资讯搜索（中文，按关键词）
#   google    Google News RSS（英文，按英文名，海外公司主力）
#   yahoo     Yahoo Finance 个股新闻（英文，需美股代码）
ENABLE = {"em_feed": True, "em_search": True, "google": True, "yahoo": True}

# 应用基目录：开发时=源码目录；打包成 exe(frozen)时=用户可写数据目录，
# 避免写进只读的安装目录或临时解压目录。
if getattr(sys, "frozen", False):
    APP_DIR = Path(os.environ.get("LOCALAPPDATA")
                   or os.environ.get("APPDATA") or Path.home()) / "ChipNews"
else:
    APP_DIR = Path(__file__).resolve().parent
APP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = APP_DIR / "data"
SEEN_FILE = DATA_DIR / "_seen.json"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
}

# 监控的公司清单。每家会自动聚合多个数据源（见 ENABLE / adapters_for）：
#   secid    东方财富代码。有则用「个股新闻流」(em_feed)；美股代码(105/106/107.)还会启用 yahoo
#            格式：市场号.代码  1=沪 0=深 105=纳斯达克 106=纽交所 107=美交所 116=港股
#   keyword  中文关键词（em_search 用），尽量精确避免同名干扰
#   en       英文名（google 用），海外公司主力来源；带引号可精确匹配
WATCHLIST = {
    "韩国": [
        {"name": "三星",     "secid": "",          "keyword": "三星电子",   "en": '"Samsung" memory'},
        {"name": "SK海力士", "secid": "",          "keyword": "SK海力士",   "en": '"SK Hynix"'},
    ],
    "美国": [
        {"name": "英伟达",   "secid": "105.NVDA",  "keyword": "英伟达",     "en": "Nvidia"},
        {"name": "美光",     "secid": "105.MU",    "keyword": "美光科技",   "en": '"Micron"'},
        {"name": "闪迪",     "secid": "105.SNDK",  "keyword": "闪迪",       "en": '"SanDisk"'},
    ],
    "日本": [
        {"name": "东芝",     "secid": "",          "keyword": "东芝",       "en": '"Toshiba" semiconductor'},
        {"name": "铠侠",     "secid": "",          "keyword": "铠侠",       "en": '"Kioxia"'},  # 即「凯侠」
    ],
    "中国": [
        {"name": "长江存储", "secid": "",          "keyword": "长江存储",   "en": '"YMTC" OR "Yangtze Memory"'},
        {"name": "兆易创新", "secid": "1.603986",  "keyword": "兆易创新",   "en": '"GigaDevice"'},
        {"name": "江波龙",   "secid": "0.301308",  "keyword": "江波龙",     "en": '"Longsys"'},
        {"name": "旺宏电子", "secid": "",          "keyword": "旺宏电子",   "en": '"Macronix"'},   # 台股 2337
        {"name": "德明利",   "secid": "0.001309",  "keyword": "德明利",     "en": ""},
        {"name": "南亚科技", "secid": "",          "keyword": "南亚科技",   "en": '"Nanya Technology"'},  # 台股 2408
        {"name": "华邦电子", "secid": "",          "keyword": "华邦电子",   "en": '"Winbond"'},    # 台股 2344
    ],
}

# ------------------------------------------------------------------ 工具

def _today():
    return datetime.date.today()


# Windows 下隐藏子进程的控制台窗口（否则每次调 curl 都会闪一个黑窗口）
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _http_get(url, extra_headers=None):
    """用系统 curl 发请求并返回响应文本。
    用 curl 而非 requests：东方财富等站点会对 requests 做 TLS 指纹识别返回空兜底，
    curl 的指纹则正常放行。返回 str（成功）或 None（失败）。"""
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    cmd = ["curl", "-s", "-m", "12", "--connect-timeout", "6", "--compressed", url]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    last = None
    for _ in range(2):  # 2 次足够；过多重试在断网时会拖很久
        try:
            # stdin=DEVNULL 必须：打包成无控制台程序后父进程 stdin 句柄无效，
            # 不重定向会导致子进程启动报 WinError 6（句柄无效），抓取全失败
            p = subprocess.run(cmd, capture_output=True, timeout=15,
                               stdin=subprocess.DEVNULL,
                               creationflags=_NO_WINDOW)
            if p.returncode == 0 and p.stdout:
                return p.stdout.decode("utf-8", errors="replace")
            last = f"rc={p.returncode}"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(0.6)
    print(f"  [warn] 请求失败: {url[:80]} ({last})", file=sys.stderr)
    return None


def _within_days(date_str, days_back):
    """date_str 形如 '2026-06-12 17:31:00'，判断是否在最近 days_back 天内。"""
    if not date_str:
        return True
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if not m:
        return True
    d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (_today() - d).days <= (days_back - 1)


def _clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)  # 去 <em> 等高亮标签
    return text.replace("　", " ").strip()


def _norm_title(title):
    """归一化标题用于跨源去重：去空白/标点、转小写。"""
    if not title:
        return ""
    return re.sub(r"[\s\W_]+", "", title).lower()


# ------------------------------------------------------------------ 数据源

def fetch_em_stock_feed(company, days_back):
    """东方财富「个股新闻流」：新闻直接挂在该股票下，效果同同花顺个股资讯页。
    适用于有 secid 的 A 股 / 美股 / 港股。无需关键词过滤——本就是该股专属资讯。"""
    secid = company["secid"]
    url = ("https://np-listapi.eastmoney.com/comm/web/getListInfo"
           f"?client=web&typefetch_em_stock_feed=1&mTypeAndCode={secid}&pageSize=30&pageIndex=1")
    txt = _http_get(url, extra_headers={"Referer": "https://quote.eastmoney.com/"})
    if not txt:
        return []
    try:
        lst = json.loads(txt)["data"]["list"]
    except Exception:  # noqa: BLE001
        return []
    out = []
    for it in lst:
        date = it.get("Art_ShowTime", "")
        if not _within_days(date, days_back):
            continue
        out.append({
            "company": company["name"],
            "title": _clean(it.get("Art_Title")),
            "summary": "",
            "date": date,
            "source": "东方财富·个股",
            "url": it.get("Art_Url") or it.get("Art_OriginUrl", ""),
        })
    return out


def fetch_eastmoney(company, days_back):
    """东方财富资讯搜索：按关键词搜，用于 EM 无个股流的韩/日/台股及未上市公司。"""
    kw = company["keyword"]
    param = {
        "uid": "",
        "keyword": kw,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "param": {"cmsArticleWebOld": {
            "searchScope": "default", "sort": "time",
            "pageIndex": 1, "pageSize": 20,  # 多取候选，过滤后保留前 MAX_PER_COMPANY
        }},
    }
    # 注意：param 必须紧凑编码（无空格），否则东方财富解析失败返回无关结果
    url = ("https://search-api-web.eastmoney.com/search/jsonp?cb=x&param="
           + quote(json.dumps(param, ensure_ascii=False, separators=(",", ":"))))
    txt = _http_get(url, extra_headers={"Referer": "https://so.eastmoney.com/"})
    if not txt:
        return []
    m = re.match(r"^[^(]*\((.*)\)\s*;?\s*$", txt, re.S)  # 去掉 jsonp 包裹
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
        items = data["result"]["cmsArticleWebOld"]
    except Exception:  # noqa: BLE001
        return []

    out = []
    for it in items:
        title = _clean(it.get("title"))
        content = _clean(it.get("content"))
        # 相关性过滤。默认要求关键词出现在标题里（过滤大盘综述类噪声）；
        # LOOSE_MATCH=True 时正文命中也算。
        kw_core = kw.replace("电子", "").replace("科技", "")
        if kw_core not in title and not (LOOSE_MATCH and kw_core in content):
            continue
        if not _within_days(it.get("date"), days_back):
            continue
        out.append({
            "company": company["name"],
            "title": title,
            "summary": content[:120],
            "date": it.get("date", ""),
            "source": it.get("mediaName") or "东方财富",
            "url": it.get("url", ""),
        })
    return out


def fetch_google(company, days_back):
    """Google News RSS：按英文名搜全球英文资讯。海外公司主力，来源权威、及时。"""
    en = company.get("en")
    if not en:
        return []
    url = ("https://news.google.com/rss/search?q=" + quote(en)
           + "&hl=en-US&gl=US&ceid=US:en")
    txt = _http_get(url)
    if not txt:
        return []
    out = []
    for block in re.findall(r"<item>(.*?)</item>", txt, re.S)[:MAX_PER_COMPANY * 2]:
        m = re.search(r"<title>(.*?)</title>", block, re.S)
        title = html.unescape(_clean(m.group(1))) if m else ""
        # Google 标题结尾常带 " - 来源名"，拆出来源
        src = "Google News"
        ms = re.search(r"<source[^>]*>(.*?)</source>", block, re.S)
        if ms:
            src = html.unescape(ms.group(1))
            title = re.sub(r"\s*-\s*" + re.escape(src) + r"\s*$", "", title)
        mp = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        date = ""
        if mp:
            try:
                date = email.utils.parsedate_to_datetime(mp.group(1)).strftime(
                    "%Y-%m-%d %H:%M:%S")
            except Exception:  # noqa: BLE001
                date = ""
        if not _within_days(date, days_back):
            continue
        ml = re.search(r"<link>(.*?)</link>", block, re.S)
        out.append({
            "company": company["name"],
            "title": title,
            "summary": "",
            "date": date,
            "source": src,
            "url": ml.group(1).strip() if ml else "",
        })
    return out


def fetch_yahoo(company, days_back):
    """Yahoo Finance：按美股代码取个股英文新闻。需 secid 为美股(105/106/107.)。"""
    secid = company.get("secid", "")
    mkt = secid.split(".")[0] if "." in secid else ""
    if mkt not in ("105", "106", "107"):
        return []
    ticker = secid.split(".")[1]
    url = ("https://query1.finance.yahoo.com/v1/finance/search?q=" + quote(ticker)
           + "&newsCount=15&quotesCount=0")
    txt = _http_get(url)
    if not txt:
        return []
    try:
        news = json.loads(txt).get("news", [])
    except Exception:  # noqa: BLE001
        return []
    out = []
    for n in news:
        date = ""
        ts = n.get("providerPublishTime")
        if ts:
            date = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
        if not _within_days(date, days_back):
            continue
        out.append({
            "company": company["name"],
            "title": _clean(n.get("title")),
            "summary": "",
            "date": date,
            "source": n.get("publisher") or "Yahoo Finance",
            "url": n.get("link", ""),
        })
    return out


def adapters_for(company):
    """按公司可用性挑选数据源（再经 ENABLE 过滤），返回 [(origin_key, fn), ...]。"""
    picked = []
    if company.get("secid"):
        picked.append(("em_feed", fetch_em_stock_feed))
    else:
        picked.append(("em_search", fetch_eastmoney))  # 无个股流时用中文搜索
    if company.get("en"):
        picked.append(("google", fetch_google))
    picked.append(("yahoo", fetch_yahoo))  # 内部自判是否美股
    return [(k, fn) for k, fn in picked if ENABLE.get(k, True)]


def fetch_company(company, days_back):
    """抓取单家公司的所有数据源，按标题去重并标注 origin，按时间倒序。
    CLI 与 GUI 共用此函数（唯一的"遍历数据源"逻辑）。"""
    items, seen = [], set()
    for origin, fetch in adapters_for(company):
        try:
            fetched = fetch(company, days_back)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] {company['name']}/{origin} 源出错: {e}", file=sys.stderr)
            fetched = []
        for it in fetched:
            key = _norm_title(it["title"])
            if not key or key in seen:
                continue
            seen.add(key)
            it["origin"] = origin
            items.append(it)
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


# ------------------------------------------------------------------ 汇总

def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            return set()
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=0),
                         encoding="utf-8")


def collect(days_back):
    result = {}  # country -> company -> [items]
    seen_titles = set()
    for country, companies in WATCHLIST.items():
        result[country] = {}
        for company in companies:
            items = []
            for it in fetch_company(company, days_back):  # 复用共享抓取
                key = _norm_title(it["title"])
                if not key or key in seen_titles:  # 再做跨公司去重
                    continue
                seen_titles.add(key)
                items.append(it)
            result[country][company["name"]] = items[:MAX_PER_COMPANY]
            print(f"  · {country}/{company['name']}: {len(items)} 条")
    return result


def render_markdown(result, today, new_urls):
    lines = [f"# 存储/芯片厂商资讯汇总 · {today}", ""]
    total = 0
    for country, companies in result.items():
        lines.append(f"## {country}")
        for name, items in companies.items():
            lines.append(f"\n### {name}")
            if not items:
                lines.append("- （近期无资讯）")
                continue
            for it in items:
                total += 1
                flag = " 🆕" if it["url"] in new_urls else ""
                date = it["date"][:16]
                lines.append(f"- **[{date}]** {it['title']}{flag}  "
                             f"_（{it['source']}）_")
                if it["summary"]:
                    lines.append(f"  - {it['summary']}")
                if it["url"]:
                    lines.append(f"  - {it['url']}")
        lines.append("")
    lines.insert(1, f"\n> 共 {total} 条，🆕 为本次新增 {len(new_urls)} 条\n")
    return "\n".join(lines)


def print_terminal(result, new_urls):
    print("\n" + "=" * 70)
    for country, companies in result.items():
        any_news = any(companies.values())
        print(f"\n【{country}】")
        for name, items in companies.items():
            if not items:
                print(f"  {name}：—")
                continue
            print(f"  {name}：")
            for it in items:
                flag = "🆕" if it["url"] in new_urls else "  "
                print(f"    {flag} [{it['date'][5:16]}] {it['title']}  ({it['source']})")
                if it["url"]:
                    print(f"        {it['url']}")
    print("\n" + "=" * 70)


def main():
    ap = argparse.ArgumentParser(description="存储/芯片厂商每日资讯汇总")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS_BACK,
                    help=f"展示最近 N 天的资讯（默认 {DEFAULT_DAYS_BACK}）")
    ap.add_argument("--loose", action="store_true",
                    help="放宽相关性：正文提到关键词也算（更全但有噪声）")
    args = ap.parse_args()

    global LOOSE_MATCH
    LOOSE_MATCH = args.loose

    today = _today().isoformat()
    print(f"拉取资讯中（最近 {args.days} 天）...")
    result = collect(args.days)

    # 增量标记
    seen = load_seen()
    new_urls = set()
    all_urls = set()
    for companies in result.values():
        for items in companies.values():
            for it in items:
                if it["url"]:
                    all_urls.add(it["url"])
                    if it["url"] not in seen:
                        new_urls.add(it["url"])
    save_seen(seen | all_urls)

    # 落盘
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / f"{today}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / f"{today}.md").write_text(
        render_markdown(result, today, new_urls), encoding="utf-8")

    print_terminal(result, new_urls)
    print(f"\n已保存：data/{today}.md  与  data/{today}.json")
    print(f"本次新增 🆕 {len(new_urls)} 条")


if __name__ == "__main__":
    main()
