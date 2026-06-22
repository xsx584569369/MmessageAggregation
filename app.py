#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""芯讯 · 存储芯片资讯台 —— PySide6 桌面应用。

运行：  uv run app.py   （或 python3 app.py）
依赖：  PySide6（见 pyproject.toml / requirements.txt）
打包：  pyinstaller -F -w -n 芯讯 app.py
"""

import sys
import datetime
import webbrowser

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize

import core

APP_VERSION = core.APP_VERSION   # 单一来源在 core.py
SOURCES = [("em_feed", "东财个股流"), ("em_search", "东财搜索"),
           ("google", "Google"), ("yahoo", "Yahoo")]

PALETTES = {
    "dark": {
        "bg": "#15171c", "surface": "#1b1d22", "surface2": "#22252b",
        "border": "#30343c", "border_hover": "#3a6ea5", "sep": "#2a2d33",
        "text": "#e6e8ec", "muted": "#9aa0a8", "tree_hover": "#23262c",
        "accent": "#4ea1ff", "accent_soft": "#1d2a3d", "accent_text": "#0c1116",
        "chip_bg": "#22252b", "chip_text": "#aab0b8",
        "scroll": "#3a3f47", "scroll_hover": "#525862",
        "menu_bg": "#1b1d22", "menu_border": "#30343c", "star": "#5a5f68",
        "card_bg": "#1e2026", "card_bg_hit": "#262219",
        "card_border": "#2c2f36", "card_border_hit": "#5e4d23",
        "card_hover_bg": "#23262d",
        "title": "#e8eaed", "summary": "#9aa0a8", "date": "#767b84", "src": "#7f858d",
        "new_bg": "#16301d", "new_fg": "#6fd18f", "kw_bg": "#33280f", "kw_fg": "#e0a34a",
        "ok": "#6fd18f", "err": "#f0938a",
        "country": {"韩国": ("KR", "#1e2a44", "#9cc2ff"), "美国": ("US", "#3a1f1d", "#f0938a"),
                    "日本": ("JP", "#332813", "#e6b667"), "中国": ("CN", "#16301d", "#7fd39a")},
    },
    "light": {
        "bg": "#f3f3f3", "surface": "#fafafa", "surface2": "#ffffff",
        "border": "#d9d9d9", "border_hover": "#b9d4ef", "sep": "#e6e6e6",
        "text": "#1f1f1f", "muted": "#6b6b6b", "tree_hover": "#eef0f2",
        "accent": "#185FA5", "accent_soft": "#e6f1fb", "accent_text": "#ffffff",
        "chip_bg": "#ffffff", "chip_text": "#5a5a5a",
        "scroll": "#d0d2d6", "scroll_hover": "#aab0b8",
        "menu_bg": "#ffffff", "menu_border": "#e0e0e0", "star": "#c4c4c4",
        "card_bg": "#ffffff", "card_bg_hit": "#fffdf6",
        "card_border": "#e7e7e7", "card_border_hit": "#f0cd8a",
        "card_hover_bg": "#fbfcfe",
        "title": "#1b1b1b", "summary": "#7d7d7d", "date": "#a8a8a8", "src": "#9a9a9a",
        "new_bg": "#e7f7e3", "new_fg": "#2e7d32", "kw_bg": "#fcedd2", "kw_fg": "#955b0a",
        "ok": "#2e7d32", "err": "#b23b2e",
        "country": {"韩国": ("KR", "#e9efff", "#2a4d9b"), "美国": ("US", "#fdecea", "#b23b2e"),
                    "日本": ("JP", "#fdf0db", "#955b0a"), "中国": ("CN", "#eaf6e6", "#2e7d32")},
    },
}
PAL = PALETTES["dark"]      # 运行时由配置覆盖（apply_theme）
ACCENT = PAL["accent"]


def build_qss(p):
    return f"""
* {{ font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif; font-size: 13px; }}
QMainWindow, QDialog {{ background: {p['bg']}; color: {p['text']}; }}
QLabel {{ color: {p['text']}; background: transparent; }}
QToolBar {{ background: {p['surface']}; border: none; border-bottom: 1px solid {p['sep']}; spacing: 8px; padding: 7px 12px; }}
QToolButton {{ border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 12px; min-height: 22px; color: {p['text']}; background: {p['surface2']}; }}
QToolButton:hover {{ background: {p['accent_soft']}; border-color: {p['border_hover']}; }}
QToolButton#accent {{ color: {p['accent']}; border-color: {p['border_hover']}; }}
QLineEdit {{ border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 10px; min-height: 22px; background: {p['surface2']}; color: {p['text']}; selection-background-color: {p['accent']}; }}
QLineEdit:focus {{ border: 1px solid {p['accent']}; }}
QComboBox {{ border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 10px; min-height: 22px; background: {p['surface2']}; color: {p['text']}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{ background: {p['surface2']}; color: {p['text']}; selection-background-color: {p['accent_soft']}; selection-color: {p['accent']}; outline: none; }}
QSpinBox {{ border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 8px; background: {p['surface2']}; color: {p['text']}; }}
QListWidget {{ border: 1px solid {p['border']}; border-radius: 6px; background: {p['surface2']}; color: {p['text']}; }}
QListWidget::item {{ padding: 4px 6px; }}
QListWidget::item:selected {{ background: {p['accent_soft']}; color: {p['accent']}; }}
QPushButton {{ border: 1px solid {p['border']}; border-radius: 6px; padding: 6px 14px; background: {p['surface2']}; color: {p['text']}; }}
QPushButton:hover {{ background: {p['accent_soft']}; }}
QPushButton:default {{ background: {p['accent']}; color: {p['accent_text']}; border-color: {p['accent']}; }}
QPushButton#chip {{ border: 1px solid {p['border']}; border-radius: 13px; padding: 4px 13px; background: {p['chip_bg']}; color: {p['chip_text']}; font-size: 12px; }}
QPushButton#chip:hover {{ border-color: {p['border_hover']}; }}
QPushButton#chip:checked {{ background: {p['accent']}; color: {p['accent_text']}; border-color: {p['accent']}; }}
QToolButton#star {{ border: none; background: transparent; padding: 0 2px; font-size: 15px; color: {p['star']}; }}
QToolButton#star:hover {{ color: #f0a73a; }}
QToolButton#star:checked {{ color: #f0a73a; }}
#sidebar {{ background: {p['surface']}; border-right: 1px solid {p['sep']}; }}
QTreeWidget {{ border: none; background: transparent; color: {p['text']}; font-size: 13px; outline: none; }}
QTreeWidget::item {{ padding: 5px 4px; border-radius: 6px; margin: 1px 4px; }}
QTreeWidget::item:selected {{ background: {p['accent_soft']}; color: {p['accent']}; }}
QTreeWidget::item:hover {{ background: {p['tree_hover']}; }}
#chipbar {{ background: {p['bg']}; border-bottom: 1px solid {p['sep']}; }}
QScrollArea {{ border: none; background: {p['bg']}; }}
#feed {{ background: {p['bg']}; }}
QStatusBar {{ background: {p['surface']}; border-top: 1px solid {p['sep']}; color: {p['muted']}; }}
QStatusBar::item {{ border: none; }}
QCheckBox {{ font-size: 13px; spacing: 8px; color: {p['text']}; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 3px 2px; }}
QScrollBar::handle:vertical {{ background: {p['scroll']}; border-radius: 5px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {p['scroll_hover']}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px 3px; }}
QScrollBar::handle:horizontal {{ background: {p['scroll']}; border-radius: 5px; min-width: 36px; }}
QScrollBar::handle:horizontal:hover {{ background: {p['scroll_hover']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QToolBar::separator {{ background: {p['sep']}; width: 1px; margin: 4px 6px; }}
QMenu {{ background: {p['menu_bg']}; border: 1px solid {p['menu_border']}; border-radius: 8px; padding: 4px; color: {p['text']}; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {p['accent_soft']}; color: {p['accent']}; }}
"""


def glyph_icon(ch, px=18):
    """把一个字符/emoji 渲染成定尺寸 QIcon，保证工具栏/侧栏图标大小一致、与文字对齐。"""
    pm = QtGui.QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setRenderHint(QtGui.QPainter.TextAntialiasing)
    f = p.font()
    f.setPixelSize(int(px * 0.72))
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter | Qt.TextDontClip, ch)
    p.end()
    return QtGui.QIcon(pm)


def dot_icon(color="#b6b6b6", px=16):
    pm = QtGui.QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setBrush(QtGui.QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(px // 2 - 3, px // 2 - 3, 6, 6)
    p.end()
    return QtGui.QIcon(pm)


def make_icon(color=ACCENT):
    pm = QtGui.QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setBrush(QtGui.QColor(color))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(10, 10, 44, 44, 12, 12)
    p.setPen(QtGui.QPen(QtGui.QColor("white"), 5))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(24, 24, 16, 16, 3, 3)
    for off in (16, 32, 48):
        p.drawLine(off, 14, off, 20)
        p.drawLine(off, 44, off, 50)
        p.drawLine(14, off, 20, off)
        p.drawLine(44, off, 50, off)
    p.end()
    return QtGui.QIcon(pm)


class FetchWorker(QThread):
    done = Signal(dict)
    progress = Signal(int, int, str)
    failed = Signal(str)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg

    def run(self):
        try:
            res = core.fetch_all(
                self.cfg, progress=lambda d, t, n: self.progress.emit(d, t, n))
            self.done.emit(res)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


def _pill(text, bg, fg, bold=False):
    lb = QtWidgets.QLabel(text)
    w = "500" if bold else "400"
    lb.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:9px; padding:1px 8px;"
        f" font-size:11px; font-weight:{w};")
    return lb


class UpdateWorker(QThread):
    checked = Signal(object)  # core.check_update() 的结果，或 None

    def run(self):
        try:
            self.checked.emit(core.check_update())
        except Exception:  # noqa: BLE001
            self.checked.emit(None)


class Card(QtWidgets.QFrame):
    opened = Signal(str)
    starred = Signal(str, bool)

    def __init__(self, item):
        super().__init__()
        self.url = item.get("url", "")
        self.setCursor(Qt.PointingHandCursor)
        hit = item.get("kw_hit")
        unread = bool(item.get("is_unread"))
        bg = PAL["card_bg_hit"] if hit else PAL["card_bg"]
        border = PAL["card_border_hit"] if hit else PAL["card_border"]
        self.setStyleSheet(
            f"Card {{ background:{bg}; border:1px solid {border}; border-radius:10px; }}"
            f"Card:hover {{ border-color:{PAL['accent']}; background:{PAL['card_hover_bg']}; }}"
            "QLabel { background: transparent; }")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(15, 11, 13, 12)
        lay.setSpacing(7)

        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        code, pbg, pfg = PAL["country"].get(
            item["country"], (item["country"], PAL["chip_bg"], PAL["muted"]))
        top.addWidget(_pill(code, pbg, pfg))
        comp = QtWidgets.QLabel(item["company"])
        comp.setStyleSheet(f"color:{PAL['accent']}; font-weight:500; font-size:12px;")
        top.addWidget(comp)
        src = core.ORIGIN_LABEL.get(item.get("origin"), "")
        pub = item.get("source", "")
        srctxt = f"{src} · {pub}" if src and pub and src not in pub else (src or pub)
        if srctxt:
            sl = QtWidgets.QLabel("· " + srctxt)
            sl.setStyleSheet(f"color:{PAL['src']}; font-size:11px;")
            top.addWidget(sl)
        top.addStretch(1)
        self.new_badge = None
        if unread:
            self.new_badge = _pill("新", PAL["new_bg"], PAL["new_fg"], bold=True)
            top.addWidget(self.new_badge)
        if hit:
            top.addWidget(_pill(item["kw_hit"], PAL["kw_bg"], PAL["kw_fg"], bold=True))
        dl = QtWidgets.QLabel(item.get("date", "")[5:16])
        dl.setStyleSheet(f"color:{PAL['date']}; font-size:11px;")
        top.addWidget(dl)
        self.star = QtWidgets.QToolButton()
        self.star.setObjectName("star")
        self.star.setCheckable(True)
        self.star.setChecked(bool(item.get("is_fav")))
        self.star.setText("★" if item.get("is_fav") else "☆")
        self.star.setCursor(Qt.PointingHandCursor)
        self.star.setToolTip("收藏 / 取消收藏")
        self.star.clicked.connect(self._toggle_star)
        top.addWidget(self.star)
        lay.addLayout(top)

        title = QtWidgets.QLabel(item.get("title", ""))
        title.setWordWrap(True)
        title.setStyleSheet(
            f"font-size:15px; color:{PAL['title']};"
            f" font-weight:{'500' if unread else '400'};")
        self.title_lbl = title
        lay.addWidget(title)

        if item.get("summary"):
            s = QtWidgets.QLabel(item["summary"])
            s.setWordWrap(True)
            s.setStyleSheet(f"color:{PAL['summary']}; font-size:12px; line-height:150%;")
            lay.addWidget(s)

    def set_read(self):
        """就地标记已读：去掉「新」徽章、标题取消加粗（不重建整列表）。"""
        self.title_lbl.setStyleSheet(
            f"font-size:15px; color:{PAL['title']}; font-weight:400;")
        if self.new_badge is not None:
            self.new_badge.hide()

    def _toggle_star(self):
        now = self.star.isChecked()
        self.star.setText("★" if now else "☆")
        self.starred.emit(self.url, now)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.opened.emit(self.url)
        super().mousePressEvent(e)


class SettingsDialog(QtWidgets.QDialog):
    SRC = [("em_feed", "东财个股流", "A股 / 美股 · 分钟级"),
           ("em_search", "东财资讯搜索", "中文 · 按关键词"),
           ("google", "Google News", "英文 · 海外公司主力"),
           ("yahoo", "Yahoo Finance", "英文 · 美股代码")]

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("设置 · 数据源与关键词")
        self.resize(470, 540)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(9)

        lay.addWidget(self._h("数据源"))
        self.src_checks = {}
        for key, name, desc in self.SRC:
            cb = QtWidgets.QCheckBox(f"{name}    —  {desc}")
            cb.setChecked(cfg["enable"].get(key, True))
            self.src_checks[key] = cb
            lay.addWidget(cb)
        note = QtWidgets.QLabel("同花顺（需 cookie）、富途（需登录）待接入，暂未启用。")
        note.setStyleSheet("color:#999; font-size:12px;")
        lay.addWidget(note)

        lay.addWidget(self._h("关键词（命中即高亮 / 强提醒）"))
        row = QtWidgets.QHBoxLayout()
        self.kw_input = QtWidgets.QLineEdit()
        self.kw_input.setPlaceholderText("输入关键词后回车或点添加")
        self.kw_input.returnPressed.connect(self._add_kw)
        addbtn = QtWidgets.QPushButton("添加")
        addbtn.clicked.connect(self._add_kw)
        row.addWidget(self.kw_input)
        row.addWidget(addbtn)
        lay.addLayout(row)
        self.kw_list = QtWidgets.QListWidget()
        self.kw_list.setMaximumHeight(120)
        self.kw_list.itemDoubleClicked.connect(
            lambda it: self.kw_list.takeItem(self.kw_list.row(it)))
        for k in cfg.get("keywords", []):
            self.kw_list.addItem(k)
        lay.addWidget(self.kw_list)
        tip = QtWidgets.QLabel("双击关键词可删除。")
        tip.setStyleSheet("color:#999; font-size:12px;")
        lay.addWidget(tip)

        lay.addWidget(self._h("通知与刷新"))
        self.cb_notify = QtWidgets.QCheckBox("桌面弹窗通知")
        self.cb_notify.setChecked(cfg.get("notify_desktop", True))
        self.cb_only_kw = QtWidgets.QCheckBox("仅命中关键词才提醒")
        self.cb_only_kw.setChecked(cfg.get("notify_only_keyword", False))
        lay.addWidget(self.cb_notify)
        lay.addWidget(self.cb_only_kw)

        trow = QtWidgets.QHBoxLayout()
        trow.addWidget(QtWidgets.QLabel("界面主题"))
        self.theme = QtWidgets.QComboBox()
        self.themes = [("深色科技", "dark"), ("浅色", "light")]
        for label, _ in self.themes:
            self.theme.addItem(label)
        self.theme.setCurrentIndex(
            0 if cfg.get("theme", "dark") == "dark" else 1)
        trow.addWidget(self.theme)
        trow.addStretch()
        lay.addLayout(trow)

        frow = QtWidgets.QHBoxLayout()
        frow.addWidget(QtWidgets.QLabel("自动刷新"))
        self.interval = QtWidgets.QComboBox()
        self.intervals = [("关闭", 0), ("每 5 分钟", 5), ("每 15 分钟", 15),
                          ("每 30 分钟", 30), ("每 60 分钟", 60)]
        for label, _ in self.intervals:
            self.interval.addItem(label)
        cur = cfg.get("interval_min", 5)
        self.interval.setCurrentIndex(
            next((i for i, (_, v) in enumerate(self.intervals) if v == cur), 1))
        frow.addWidget(self.interval)
        frow.addStretch()
        lay.addLayout(frow)

        lay.addStretch()
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _h(self, text):
        lb = QtWidgets.QLabel(text)
        lb.setStyleSheet("color:#666; font-size:12px; margin-top:6px;")
        return lb

    def _add_kw(self):
        k = self.kw_input.text().strip()
        if k and not self.kw_list.findItems(k, Qt.MatchExactly):
            self.kw_list.addItem(k)
        self.kw_input.clear()

    def result_config(self):
        self.cfg["enable"] = {k: cb.isChecked() for k, cb in self.src_checks.items()}
        self.cfg["keywords"] = [self.kw_list.item(i).text()
                                for i in range(self.kw_list.count())]
        self.cfg["notify_desktop"] = self.cb_notify.isChecked()
        self.cfg["notify_only_keyword"] = self.cb_only_kw.isChecked()
        self.cfg["interval_min"] = self.intervals[self.interval.currentIndex()][1]
        self.cfg["theme"] = self.themes[self.theme.currentIndex()][1]
        return self.cfg


class WatchlistDialog(QtWidgets.QDialog):
    """编辑监控清单：每行一家公司，可增删。"""
    COLS = ["国家", "名称", "关键词", "secid", "英文名(en)"]

    def __init__(self, watchlist, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理监控公司")
        self.resize(680, 520)
        lay = QtWidgets.QVBoxLayout(self)
        hint = QtWidgets.QLabel(
            "secid：1.沪 0.深 105.纳斯达克 116.港股，留空则用关键词搜索；"
            "英文名用于 Google News。改完保存会重新抓取。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#888; font-size:12px;")
        lay.addWidget(hint)

        self.table = QtWidgets.QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table, 1)
        for country, comps in watchlist.items():
            for c in comps:
                self._add_row(country, c.get("name", ""), c.get("keyword", ""),
                              c.get("secid", ""), c.get("en", ""))

        btnrow = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton("＋ 添加一行")
        add.clicked.connect(lambda: self._add_row("中国", "", "", "", ""))
        rm = QtWidgets.QPushButton("－ 删除选中行")
        rm.clicked.connect(self._del_rows)
        btnrow.addWidget(add)
        btnrow.addWidget(rm)
        btnrow.addStretch()
        lay.addLayout(btnrow)

        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _add_row(self, *vals):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, v in enumerate(vals):
            self.table.setItem(r, c, QtWidgets.QTableWidgetItem(v))

    def _del_rows(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)

    def result_watchlist(self):
        def cell(r, c):
            it = self.table.item(r, c)
            return it.text().strip() if it else ""
        wl = {}
        for r in range(self.table.rowCount()):
            country, name = cell(r, 0) or "其他", cell(r, 1)
            if not name:
                continue
            wl.setdefault(country, []).append({
                "name": name, "secid": cell(r, 3),
                "keyword": cell(r, 2) or name, "en": cell(r, 4),
            })
        return wl


class MainWindow(QtWidgets.QMainWindow):
    DAYS = [("近 1 天", 1), ("近 3 天", 3), ("近 7 天", 7), ("近 14 天", 14)]

    def __init__(self):
        super().__init__()
        self.cfg = core.load_config()
        if not core.CONFIG_FILE.exists():
            core.save_config(self.cfg)
        self.items = []
        self.scope = ("all", None)
        self.read_filter = "all"
        self.src_filter = set(k for k, _ in SOURCES)
        self.last_new = 0
        self.worker = None
        self.BATCH = 30          # 信息流分批渲染，每批条数
        self._rows = []          # 当前过滤后的全部条目
        self._shown = 0          # 已渲染条数
        self._cards = {}         # url -> Card，供就地更新
        self._fav_item = None    # 左侧「收藏」树项，供就地更新计数
        self._all_item = None    # 左侧「全部消息」树项，未读/全部视图回到它

        self.setWindowTitle(f"芯讯 · 存储芯片资讯台  v{APP_VERSION}")
        self.setWindowIcon(make_icon())
        self.resize(1180, 760)
        self.setMinimumSize(880, 560)
        self._build_toolbar()
        self._build_body()
        self._build_status()
        self._build_tray()
        self.apply_theme(self.cfg.get("theme", "dark"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self._apply_interval()

        # 已读/收藏改动常驻内存，定时 + 退出时落盘（避免每次点击都全量重写）
        self.flush_timer = QTimer(self)
        self.flush_timer.timeout.connect(core.flush)
        self.flush_timer.start(8000)
        app = QtWidgets.QApplication.instance()
        if app:
            app.aboutToQuit.connect(core.flush)

        self._update_url = ""
        self._manual_upd = False
        QTimer.singleShot(300, self.refresh)
        QTimer.singleShot(2500, self.check_update)  # 启动后静默检查更新

    # ---------- 工具栏
    def _build_toolbar(self):
        tb = QtWidgets.QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(tb)

        self.act_refresh = QtGui.QAction(glyph_icon("🔄"), "刷新", self)
        self.act_refresh.triggered.connect(self.refresh)
        btn = QtWidgets.QToolButton()
        btn.setObjectName("accent")
        btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn.setDefaultAction(self.act_refresh)
        tb.addWidget(btn)

        self.days_combo = QtWidgets.QComboBox()
        for label, _ in self.DAYS:
            self.days_combo.addItem(label)
        self.days_combo.setCurrentIndex(
            next((i for i, (_, v) in enumerate(self.DAYS)
                  if v == self.cfg.get("days", 3)), 1))
        self.days_combo.setMinimumContentsLength(5)
        self.days_combo.currentIndexChanged.connect(self._on_days)
        tb.addWidget(self.days_combo)

        tb.addSeparator()

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("搜索标题 / 公司 / 关键词…")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(220)
        self.search.setMaximumWidth(420)
        self.search.textChanged.connect(self.render_feed)
        tb.addWidget(self.search)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self.act_read_all = QtGui.QAction(glyph_icon("✔️"), "全部已读", self)
        self.act_read_all.triggered.connect(self._mark_all_read)
        readbtn = QtWidgets.QToolButton()
        readbtn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        readbtn.setDefaultAction(self.act_read_all)
        tb.addWidget(readbtn)

        self.bell = QtWidgets.QToolButton()
        self.bell.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.bell.setIcon(glyph_icon("🔔"))
        self.bell.setText("0")
        self.bell.setToolTip("查看未读")
        self.bell.clicked.connect(self._show_unread)
        tb.addWidget(self.bell)

        self.upd_btn = QtWidgets.QToolButton()
        self.upd_btn.setObjectName("accent")
        self.upd_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.upd_btn.setIcon(glyph_icon("⬆️"))
        self.upd_btn.setToolTip("有新版本可更新，点击前往下载")
        self.upd_btn.clicked.connect(self._open_update)
        self.upd_btn.hide()  # 仅在发现新版本时显示
        tb.addWidget(self.upd_btn)

        tb.addSeparator()

        act_set = QtGui.QAction(glyph_icon("⚙️"), "", self)
        act_set.setToolTip("设置")
        act_set.triggered.connect(self.open_settings)
        setbtn = QtWidgets.QToolButton()
        setbtn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        setbtn.setDefaultAction(act_set)
        tb.addWidget(setbtn)

    # ---------- 主体
    def _build_body(self):
        central = QtWidgets.QWidget()
        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        side = QtWidgets.QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(192)
        sl = QtWidgets.QVBoxLayout(side)
        sl.setContentsMargins(8, 10, 8, 10)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(10)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tree.itemClicked.connect(self._on_tree)
        sl.addWidget(self.tree)
        mng = QtWidgets.QPushButton("＋ 管理监控公司")
        mng.setCursor(Qt.PointingHandCursor)
        mng.clicked.connect(self.open_watchlist)
        sl.addWidget(mng)
        root.addWidget(side)

        right = QtWidgets.QWidget()
        rl = QtWidgets.QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        chipbar = QtWidgets.QWidget()
        chipbar.setObjectName("chipbar")
        cl = QtWidgets.QHBoxLayout(chipbar)
        cl.setContentsMargins(14, 9, 14, 9)
        cl.setSpacing(7)
        self.read_chips = {}
        for key, label in [("all", "全部"), ("unread", "未读")]:
            b = self._chip(label, checked=(key == "all"))
            b.clicked.connect(lambda _=0, k=key: self._set_read(k))
            self.read_chips[key] = b
            cl.addWidget(b)
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.VLine)
        sep.setStyleSheet("color:#dcdcdc;")
        cl.addWidget(sep)
        self.src_chips = {}
        for key, label in SOURCES:
            b = self._chip(label, checked=True)
            b.clicked.connect(lambda _=0, k=key: self._toggle_src(k))
            self.src_chips[key] = b
            cl.addWidget(b)
        cl.addStretch()
        rl.addWidget(chipbar)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.feed = QtWidgets.QWidget()
        self.feed.setObjectName("feed")
        self.feed_lay = QtWidgets.QVBoxLayout(self.feed)
        self.feed_lay.setContentsMargins(14, 12, 14, 14)
        self.feed_lay.setSpacing(9)
        self.feed_lay.addStretch()
        self.scroll.setWidget(self.feed)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        rl.addWidget(self.scroll, 1)

        root.addWidget(right, 1)
        self.setCentralWidget(central)

    def _chip(self, label, checked=False):
        b = QtWidgets.QPushButton(label)
        b.setObjectName("chip")
        b.setCheckable(True)
        b.setChecked(checked)
        b.setCursor(Qt.PointingHandCursor)
        return b

    def _build_status(self):
        self.status = self.statusBar()
        self.lbl_status = QtWidgets.QLabel("准备就绪")
        self.lbl_sources = QtWidgets.QLabel("")
        self.lbl_clock = QtWidgets.QLabel("")
        self.lbl_clock.setStyleSheet("color:#8a8a8a;")
        self.status.addWidget(self.lbl_status)
        self.status.addPermanentWidget(self.lbl_sources)
        self.status.addPermanentWidget(self.lbl_clock)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self._tick)
        self.clock.start(1000)
        self._tick()

    def _tick(self):
        t = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
        self.lbl_clock.setText("北京时间 " + t.strftime("%H:%M:%S") + "  ")

    def _build_tray(self):
        self.tray = QtWidgets.QSystemTrayIcon(make_icon(), self)
        self.tray.setToolTip("芯讯 · 存储芯片资讯台")
        menu = QtWidgets.QMenu()
        menu.addAction("显示主窗口", self.showNormal)
        menu.addAction("立即刷新", self.refresh)
        menu.addAction("检查更新", lambda: self.check_update(manual=True))
        menu.addSeparator()
        menu.addAction("退出", QtWidgets.QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.showNormal()
            if r == QtWidgets.QSystemTrayIcon.Trigger else None)
        self.tray.show()

    # ---------- 行为
    def _on_days(self, idx):
        self.cfg["days"] = self.DAYS[idx][1]
        core.save_config(self.cfg)
        self.refresh()

    def _set_read(self, kind):
        self.read_filter = kind
        for k, b in self.read_chips.items():
            b.setChecked(k == kind)
        # 「全部/未读」是全局视图：重置左侧分类到「全部消息」，
        # 否则若之前选了某公司/收藏，未读可能不在该范围内而显示为空
        self.scope = ("all", None)
        if self._all_item is not None:
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(self._all_item)
            self.tree.blockSignals(False)
        self.render_feed()

    def _toggle_src(self, key):
        if self.src_chips[key].isChecked():
            self.src_filter.add(key)
        else:
            self.src_filter.discard(key)
        self.render_feed()

    def _show_unread(self):
        self._set_read("unread")

    def _mark_all_read(self):
        urls = [it["url"] for it in self.items if it["url"] and it["is_unread"]]
        if not urls:
            return
        core.mark_read(urls)
        for it in self.items:
            it["is_unread"] = False
        self._build_tree()
        self.render_feed()
        self._update_status()

    def apply_theme(self, theme):
        global PAL, ACCENT
        PAL = PALETTES.get(theme, PALETTES["dark"])
        ACCENT = PAL["accent"]
        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet(build_qss(PAL))
        if self.items:        # 重新渲染以应用卡片内联配色
            self._build_tree()
            self.render_feed()

    def check_update(self, manual=False):
        self._manual_upd = manual
        self._uw = UpdateWorker()
        self._uw.checked.connect(self._on_update)
        self._uw.start()

    def _on_update(self, res):
        manual = self._manual_upd
        self._manual_upd = False
        if res is None:
            if manual:
                QtWidgets.QMessageBox.information(
                    self, "检查更新",
                    "暂时无法获取更新信息（可能尚未发布任何版本，或网络问题）。")
            return
        if res["has_update"]:
            self._update_url = res["url"]
            self.upd_btn.setText(f"新版 v{res['latest']}")
            self.upd_btn.show()
            self.tray.showMessage(
                f"发现新版本 v{res['latest']}",
                "点工具栏「新版」按钮前往下载", make_icon(), 8000)
            if manual:
                self._open_update()
        else:
            self.upd_btn.hide()
            if manual:
                QtWidgets.QMessageBox.information(
                    self, "检查更新", f"当前已是最新版本（v{core.APP_VERSION}）。")

    def _open_update(self):
        url = self._update_url or f"https://github.com/{core.GITHUB_REPO}/releases"
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass

    def _apply_interval(self):
        mins = int(self.cfg.get("interval_min", 5))
        self.timer.stop()
        if mins > 0:
            self.timer.start(mins * 60 * 1000)

    def open_watchlist(self):
        cfg = core.load_config()
        wl = cfg.get("watchlist") or core._default_watchlist()
        dlg = WatchlistDialog(wl, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_wl = dlg.result_watchlist()
            if not new_wl:
                return
            self.cfg["watchlist"] = new_wl
            core.save_config(self.cfg)
            core.apply_watchlist(self.cfg)
            self.refresh()

    def open_settings(self):
        dlg = SettingsDialog(core.load_config(), self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.cfg = dlg.result_config()
            self.cfg["days"] = self.DAYS[self.days_combo.currentIndex()][1]
            core.save_config(self.cfg)
            self.apply_theme(self.cfg.get("theme", "dark"))
            self._apply_interval()
            self.refresh()

    def refresh(self):
        if self.worker and self.worker.isRunning():
            return
        self.act_refresh.setEnabled(False)
        self.lbl_status.setText("正在拉取资讯…")
        self.worker = FetchWorker(self.cfg)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, done, total, name):
        if name:
            self.lbl_status.setText(f"拉取中 {done}/{total}：{name}")

    def _on_failed(self, msg):
        self.act_refresh.setEnabled(True)
        self.lbl_status.setText(f"抓取失败：{msg}")

    def _on_done(self, res):
        self.act_refresh.setEnabled(True)
        self.items = res["items"]
        self.last_new = len(res["arrived"])
        self._notify(res["arrived"])
        self._build_tree()
        self.render_feed()
        self._update_status()

    def _update_status(self):
        now = QtCore.QTime.currentTime().toString("HH:mm")
        unread = sum(1 for it in self.items if it["is_unread"])
        self.bell.setText(f"  {unread}")
        if not self.items:
            self.lbl_status.setText(
                f'<span style="color:{PAL["err"]};">未获取到资讯——可能网络异常或数据源暂不可用，'
                '请稍后点刷新重试</span>')
            self.lbl_status.setTextFormat(Qt.RichText)
            on = [k for k, v in self.cfg["enable"].items() if v]
            self.lbl_sources.setText(f"{len(on)} 个数据源   ")
            return
        new_html = (f' · <span style="color:{PAL["ok"]};">新增 {self.last_new}</span>'
                    if self.last_new else "")
        self.lbl_status.setText(
            f'<span>上次刷新 {now} · 共 {len(self.items)} 条 · 未读 {unread}{new_html}</span>')
        self.lbl_status.setTextFormat(Qt.RichText)
        on = [k for k, v in self.cfg["enable"].items() if v]
        self.lbl_sources.setText(
            f'<span style="color:{PAL["ok"]};">●</span> {len(on)} 个数据源在线   ')
        self.lbl_sources.setTextFormat(Qt.RichText)

    def _notify(self, arrived):
        if not arrived or not self.cfg.get("notify_desktop", True):
            return
        only = self.cfg.get("notify_only_keyword", False)
        picks = [a for a in arrived if a["kw_hit"]] if only else arrived
        if not picks:
            return
        if len(picks) == 1:
            a = picks[0]
            self.tray.showMessage(f"新消息 · {a['company']}", a["title"],
                                  make_icon(), 8000)
        else:
            head = "；".join(a["company"] for a in picks[:4])
            self.tray.showMessage(f"新增 {len(picks)} 条资讯", head, make_icon(), 8000)

    # ---------- 导航树
    def _build_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        fav = sum(1 for it in self.items if it.get("is_fav"))

        def header(text):
            h = QtWidgets.QTreeWidgetItem([text])
            h.setFlags(Qt.ItemIsEnabled)
            f = h.font(0)
            f.setBold(True)
            h.setFont(0, f)
            h.setForeground(0, QtGui.QColor("#9a9a9a"))
            self.tree.addTopLevelItem(h)
            return h

        def leaf(parent, text, data, icon=None):
            it = QtWidgets.QTreeWidgetItem([text])
            it.setData(0, Qt.UserRole, data)
            if icon:
                it.setIcon(0, icon)
            parent.addChild(it)
            return it

        flags = {"韩国": "🇰🇷", "美国": "🇺🇸", "日本": "🇯🇵", "中国": "🇨🇳"}

        h1 = header("信息流")
        all_item = leaf(h1, f"全部消息   ({len(self.items)})", ("all", None),
                        glyph_icon("📥", 16))
        self._all_item = all_item
        self._fav_item = leaf(h1, f"收藏   ({fav})" if fav else "收藏",
                              ("fav", None), glyph_icon("⭐", 16))
        h1.setExpanded(True)

        counts = {}
        for it in self.items:
            counts[(it["country"], it["company"])] = \
                counts.get((it["country"], it["company"]), 0) + 1
        h2 = header("监控清单")
        import daily_news as dn
        for country, comps in dn.WATCHLIST.items():
            node = leaf(h2, country, ("country", country),
                        glyph_icon(flags.get(country, "🏳"), 16))
            f = node.font(0)
            f.setBold(True)
            node.setFont(0, f)
            for c in comps:
                n = counts.get((country, c["name"]), 0)
                leaf(node, f"{c['name']}" + (f"   ({n})" if n else ""),
                     ("company", c["name"]), dot_icon())
            node.setExpanded(True)
        h2.setExpanded(True)
        self.tree.setCurrentItem(all_item)
        self.tree.blockSignals(False)

    def _on_tree(self, item):
        data = item.data(0, Qt.UserRole)
        if data:
            self.scope = data
            self.render_feed()

    # ---------- 信息流
    def _filtered(self):
        kind, key = self.scope
        q = self.search.text().strip().lower()
        out = []
        for it in self.items:
            if kind == "fav" and not it.get("is_fav"):
                continue
            if kind == "country" and it["country"] != key:
                continue
            if kind == "company" and it["company"] != key:
                continue
            if self.read_filter == "unread" and not it["is_unread"]:
                continue
            if it.get("origin") and it["origin"] not in self.src_filter:
                continue
            if q and q not in (it["title"] + it["company"] +
                               it.get("kw_hit", "")).lower():
                continue
            out.append(it)
        return out

    def _clear_feed(self):
        while self.feed_lay.count() > 1:
            w = self.feed_lay.takeAt(0).widget()
            if w:
                w.deleteLater()

    def render_feed(self):
        self._clear_feed()
        self._cards.clear()
        self._rows = self._filtered()
        self._shown = 0
        if not self._rows:
            empty = QtWidgets.QLabel("（无符合条件的资讯）")
            empty.setStyleSheet("color:#aaa; padding:40px;")
            empty.setAlignment(Qt.AlignCenter)
            self.feed_lay.insertWidget(0, empty)
            return
        self._render_more()

    def _render_more(self):
        end = min(self._shown + self.BATCH, len(self._rows))
        for it in self._rows[self._shown:end]:
            card = Card(it)
            card.opened.connect(self._open)
            card.starred.connect(self._star)
            if it.get("url"):
                self._cards[it["url"]] = card
            self.feed_lay.insertWidget(self.feed_lay.count() - 1, card)
        self._shown = end
        QTimer.singleShot(0, self._fill_check)

    def _fill_check(self):
        # 内容不足以产生滚动条但仍有剩余时，自动补一批
        if self._shown < len(self._rows) and \
                self.scroll.verticalScrollBar().maximum() == 0:
            self._render_more()

    def _on_scroll(self, value):
        vbar = self.scroll.verticalScrollBar()
        if self._shown < len(self._rows) and value >= vbar.maximum() - 60:
            self._render_more()

    def _open(self, url):
        if not url:
            return
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
        core.mark_read([url])
        for it in self.items:
            if it["url"] == url:
                it["is_unread"] = False
        # 就地更新：未读视图下该条移除→重渲染；否则只更新这张卡片
        if self.read_filter == "unread":
            self.render_feed()
        elif url in self._cards:
            self._cards[url].set_read()
        self._update_status()  # 仅刷新未读数 / 铃铛，不重建树

    def _star(self, url, now):
        if not url:
            return
        core.toggle_fav(url)
        for it in self.items:
            if it["url"] == url:
                it["is_fav"] = now
        if self._fav_item is not None:  # 就地更新收藏计数
            favn = sum(1 for it in self.items if it.get("is_fav"))
            self._fav_item.setText(0, f"收藏   ({favn})" if favn else "收藏")
        if self.scope[0] == "fav" and not now:  # 收藏视图里取消→移除该卡
            self.render_feed()

    def closeEvent(self, e):
        if self.tray.isVisible():
            e.ignore()
            self.hide()
            self.tray.showMessage("仍在后台运行", "已最小化到托盘，继续监控资讯。",
                                  make_icon(), 3000)


def main():
    # Windows：显式设置 AppUserModelID，让系统通知/任务栏正确归属到本应用
    # （否则通知标题会显示成进程名 ChipNews / Python）
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "ChipNews.芯讯")
        except Exception:  # noqa: BLE001
            pass

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("芯讯")
    app.setApplicationDisplayName("芯讯 · 存储芯片资讯台")
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()  # 主题在 MainWindow 内 apply_theme 应用
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
