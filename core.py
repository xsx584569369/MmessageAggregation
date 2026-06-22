#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 后端核心层：复用 daily_news 的抓取逻辑，叠加配置 / 已读 / 关键词。

GUI 只跟本模块打交道，不直接碰 daily_news 的全局变量。
"""

import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import daily_news as dn

# 与 daily_news 共用基目录（打包后指向用户可写数据目录）
BASE = dn.APP_DIR
DATA_DIR = dn.DATA_DIR
CONFIG_FILE = BASE / "config.json"

# 出处标识 -> 展示名（GUI 按数据源筛选 / 卡片来源标签用；origin 由 dn.fetch_company 标注）
ORIGIN_LABEL = {
    "em_feed": "东财个股流", "em_search": "东财搜索",
    "google": "Google", "yahoo": "Yahoo",
}

FETCH_WORKERS = 8  # 并发抓取的线程数

APP_VERSION = "1.0.3"                          # 当前版本（发版时改这里 / 与 git tag 对应）
GITHUB_REPO = "xsx584569369/MmessageAggregation"  # 检查更新用的仓库

# 默认配置（首次运行写入 config.json，之后以文件为准）
DEFAULT_CONFIG = {
    "enable": dict(dn.ENABLE),          # 数据源开关
    "loose_match": False,                # 关键词搜索是否放宽到正文
    "days": dn.DEFAULT_DAYS_BACK,        # 展示最近 N 天
    "interval_min": 5,                   # 自动刷新间隔（分钟），0=关闭
    "notify_desktop": True,              # 桌面弹窗通知
    "notify_only_keyword": False,        # 仅命中关键词才提醒
    "keywords": ["HBM", "涨价", "减产", "财报", "量产", "大宗交易"],
    "theme": "dark",                     # 界面主题：dark / light
}


# ----------------------------------------------------------- 配置持久化

def _default_watchlist():
    return json.loads(json.dumps(dn.WATCHLIST))


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝默认
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    # enable 补齐新源
    base_enable = dict(dn.ENABLE)
    base_enable.update(cfg.get("enable", {}))
    cfg["enable"] = base_enable
    cfg.setdefault("watchlist", _default_watchlist())  # 监控清单可在界面编辑
    return cfg


def apply_watchlist(cfg):
    """把配置里的监控清单应用到 daily_news（供抓取/导航读取）。"""
    wl = cfg.get("watchlist")
    if wl:
        dn.WATCHLIST = wl


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                           encoding="utf-8")


# ----------------------------------------------------------- 本地消息库
# 所有抓到的消息累积存到 messages.json，去重、保留已读/收藏状态。
# 每条记录的主键 id = url（无 url 时用标题归一化）。

STORE_FILE = DATA_DIR / "messages.json"
STORE_CAP = 3000  # 最多保留多少条（按时间保新，防止无限增长）

# 消息库常驻内存，所有读写都走缓存 + 锁；落盘由 flush() 防抖完成。
_LOCK = threading.RLock()
_STORE = None     # dict: id -> record（None 表示尚未从磁盘加载）
_DIRTY = False    # 内存是否有未落盘的改动


def _msg_id(url, title):
    return url if url else "t:" + dn._norm_title(title)


def _ensure_store():
    global _STORE
    if _STORE is None:
        if STORE_FILE.exists():
            try:
                data = json.loads(STORE_FILE.read_text(encoding="utf-8"))
                _STORE = {r["id"]: r for r in data}
            except Exception:  # noqa: BLE001
                _STORE = {}
        else:
            _STORE = {}
    return _STORE


def load_store():
    """返回内存库的浅拷贝快照（id -> record）。"""
    with _LOCK:
        return dict(_ensure_store())


def flush():
    """有改动则原子落盘；无改动直接返回。供定时器 / 退出时调用。"""
    global _DIRTY
    with _LOCK:
        if not _DIRTY or _STORE is None:
            return
        rows = sorted(_STORE.values(), key=lambda r: r.get("date", ""), reverse=True)
        rows = rows[:STORE_CAP]
        DATA_DIR.mkdir(exist_ok=True)
        tmp = STORE_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")  # 紧凑
        tmp.replace(STORE_FILE)  # 原子写，防写一半损坏
        _DIRTY = False


def mark_read(urls):
    global _DIRTY
    ids = set(urls)
    with _LOCK:
        store = _ensure_store()
        for r in store.values():
            if (r.get("url") in ids or r.get("id") in ids) and not r.get("read"):
                r["read"] = True
                _DIRTY = True


def toggle_fav(url):
    """切换收藏，返回切换后是否已收藏。"""
    global _DIRTY
    with _LOCK:
        store = _ensure_store()
        for r in store.values():
            if r.get("url") == url or r.get("id") == url:
                r["fav"] = not r.get("fav", False)
                _DIRTY = True
                return r["fav"]
    return False


def watchlist():
    """返回 [(country, company_dict), ...] 顺序展开，供 GUI 构建导航。"""
    out = []
    for country, comps in dn.WATCHLIST.items():
        for c in comps:
            out.append((country, c))
    return out


# ----------------------------------------------------------- 抓取

def fetch_all(cfg, progress=None):
    """抓取并并入本地消息库，返回库内全部消息 + 本次新到列表。

    progress(done, total, company_name) 可选回调，用于进度条。
    返回: {"items": [...], "arrived": [...]}
      item: id/country/company/title/summary/date/source/origin/url
            + is_unread / is_fav / kw_hit（展示态，每次按库内 read/fav 计算）
      arrived: 本次首次入库的条目（用于通知；首次建库不计，避免刷屏）
    """
    global _DIRTY
    dn.ENABLE.update(cfg.get("enable", {}))
    dn.LOOSE_MATCH = bool(cfg.get("loose_match", False))
    apply_watchlist(cfg)
    days = int(cfg.get("days", dn.DEFAULT_DAYS_BACK))
    keywords = [k for k in cfg.get("keywords", []) if k.strip()]

    wl = watchlist()
    done = [0]

    def work(entry):
        country, company = entry
        try:
            fetched = dn.fetch_company(company, days)
        except Exception:  # noqa: BLE001
            fetched = []
        done[0] += 1
        if progress:
            progress(done[0], len(wl), company["name"])
        return country, company["name"], fetched

    # 各公司并发抓取（每家内部仍按源串行），大幅缩短整体耗时
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        results = list(ex.map(work, wl))

    # 合并入库：单线程在锁内完成，无竞态
    arrived_ids = []
    with _LOCK:
        store = _ensure_store()
        first_build = not store
        for country, cname, fetched in results:
            for it in fetched:
                title, url = it.get("title", ""), it.get("url", "")
                if not title:
                    continue
                mid = _msg_id(url, title)
                if mid in store:  # 已存在：保留 read/fav，仅补全摘要
                    r = store[mid]
                    r["summary"] = it.get("summary", "") or r.get("summary", "")
                    continue
                store[mid] = {
                    "id": mid, "country": country, "company": cname,
                    "title": title, "summary": it.get("summary", ""),
                    "date": it.get("date", ""), "source": it.get("source", ""),
                    "origin": it.get("origin", ""), "url": url,
                    "read": False, "fav": False,
                }
                arrived_ids.append(mid)
        if arrived_ids:
            _DIRTY = True
        # 组装展示列表（库内全部，按时间倒序），叠加关键词高亮
        items = [{
            **r,
            "is_unread": not r.get("read", False),
            "is_fav": r.get("fav", False),
            "kw_hit": next((k for k in keywords if k in r["title"]), ""),
        } for r in store.values()]

    flush()  # 新消息及时落盘
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    arrived_set = set(arrived_ids)
    arrived = [] if first_build else [it for it in items if it["id"] in arrived_set]
    return {"items": items, "arrived": arrived}


# ----------------------------------------------------------- 检查更新

def _ver_tuple(s):
    """'v1.2.3' / '1.2.3-dev' -> (1,2,3)，用于比较版本大小。"""
    s = (s or "").lstrip("vV").split("-")[0].split("+")[0]
    out = []
    for p in s.split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out) or (0,)


def check_update():
    """查询 GitHub 最新 Release，返回 {latest, url, has_update} 或 None（查询失败）。"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    txt = dn._http_get(url, extra_headers={"Accept": "application/vnd.github+json"})
    if not txt:
        return None
    try:
        d = json.loads(txt)
    except Exception:  # noqa: BLE001
        return None
    tag = d.get("tag_name")
    if not tag:
        return None
    return {
        "latest": tag.lstrip("vV"),
        "url": d.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases",
        "has_update": _ver_tuple(tag) > _ver_tuple(APP_VERSION),
    }
