"""可复用 UI 小组件：状态徽章、可排序表格项、搜索栏、日期筛选器。"""

from datetime import date, timedelta
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QWidget, QDateEdit
)


# ============== 状态颜色 ==============
STATUS_COLORS = {
    "已预约": ("#E8F1FB", "#2C5C8E"),
    "已就诊": ("#E5F6EC", "#1F8B4C"),
    "已取消": ("#ECEEF1", "#7F8C8D"),
    "爽约":   ("#FBEAE7", "#C0392B"),
    "正常":   ("#E5F6EC", "#1F8B4C"),
    "停诊":   ("#FBEAE7", "#C0392B"),
    "在职":   ("#E5F6EC", "#1F8B4C"),
    "离职":   ("#ECEEF1", "#7F8C8D"),
    "启用":   ("#E5F6EC", "#1F8B4C"),
    "停用":   ("#FBEAE7", "#C0392B"),
    "待支付": ("#FFF4DC", "#9C6B14"),
    "已支付": ("#E5F6EC", "#1F8B4C"),
    "已退款": ("#ECEEF1", "#7F8C8D"),
    "admin":   ("#F2E4F8", "#7B3F9C"),
    "doctor":  ("#E8F1FB", "#2C5C8E"),
    "patient": ("#E5F6EC", "#1F8B4C"),
}


class NumericItem(QTableWidgetItem):
    """按数值排序的表格项。"""
    def __init__(self, value, display=None):
        super().__init__(str(display if display is not None else value))
        try:
            self._v = float(value)
        except (TypeError, ValueError):
            self._v = 0.0
        self.setData(Qt.UserRole, self._v)

    def __lt__(self, other):
        try:
            return self._v < other._v
        except AttributeError:
            return super().__lt__(other)


def make_status_item(text):
    item = QTableWidgetItem(str(text))
    color = STATUS_COLORS.get(str(text))
    if color:
        bg, fg = color
        item.setBackground(QBrush(QColor(bg)))
        item.setForeground(QBrush(QColor(fg)))
        item.setTextAlignment(Qt.AlignCenter)
    return item


def setup_table(tbl: QTableWidget, headers: list[str], stretch: bool = True):
    """统一表格初始化：列头、可排序、整行选择、隔行底色。"""
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    if stretch:
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setSelectionMode(QTableWidget.SingleSelection)
    tbl.setAlternatingRowColors(True)
    tbl.setSortingEnabled(True)
    tbl.verticalHeader().setDefaultSectionSize(30)
    tbl.verticalHeader().setVisible(False)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)


def fill_table(tbl: QTableWidget, rows: list[dict], columns: list):
    """填充表格内容。

    columns 元素：(key, kind)
        kind ∈ {"text", "int", "float", "status"}
    或 (key, kind, formatter) — 自定义文本。
    """
    tbl.setSortingEnabled(False)
    tbl.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, spec in enumerate(columns):
            key = spec[0]; kind = spec[1]
            val = row.get(key) if isinstance(row, dict) else None
            display = spec[2](val, row) if len(spec) >= 3 else (val if val is not None else "")
            if kind in ("int", "float") and val is not None and val != "":
                item = NumericItem(val, display)
            elif kind == "status":
                item = make_status_item(display)
            else:
                item = QTableWidgetItem("" if val is None else str(display))
            tbl.setItem(r, c, item)
    tbl.setSortingEnabled(True)


def search_field(placeholder: str = "搜索…"):
    le = QLineEdit()
    le.setProperty("search", True)
    le.setPlaceholderText(placeholder)
    le.setClearButtonEnabled(True)
    return le


def make_combo(items: list, current=None):
    cb = QComboBox()
    for it in items:
        if isinstance(it, tuple):
            cb.addItem(it[0], it[1])
        else:
            cb.addItem(str(it), it)
    if current is not None:
        idx = cb.findData(current)
        if idx >= 0:
            cb.setCurrentIndex(idx)
    return cb


def label(text, kind: str = ""):
    lb = QLabel(text)
    if kind == "h1": lb.setObjectName("H1")
    elif kind == "h2": lb.setObjectName("H2")
    elif kind == "tip": lb.setObjectName("tip")
    return lb


def primary_btn(text, kind: str = ""):
    b = QPushButton(text)
    if kind:
        b.setProperty("kind", kind)
    return b


# ============== 日期筛选器 ==============
class DateRangeFilter(QWidget):
    """日期范围筛选 — 模式下拉 + 按需展开的日期选择框。

    模式：今天 / 本周 / 本月 / 最近30天 / 自定义 / 全部
    用法：
        flt = DateRangeFilter()
        flt.changed.connect(self._reload)
        start, end = flt.start_date(), flt.end_date()  # 可能为 None
    """
    changed = pyqtSignal()

    PRESETS = [
        ("今天",       "today"),
        ("本周",       "week"),
        ("本月",       "month"),
        ("最近 30 天", "30d"),
        ("自定义",     "custom"),
        ("全部",       "all"),
    ]

    def __init__(self, default: str = "month", parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(6)

        self.cmb = QComboBox()
        for label_, key in self.PRESETS:
            self.cmb.addItem(label_, key)
        idx = next((i for i, p in enumerate(self.PRESETS) if p[1] == default), 0)
        self.cmb.setCurrentIndex(idx)
        h.addWidget(self.cmb)

        self.dt_start = QDateEdit(QDate.currentDate().addDays(-30))
        self.dt_start.setCalendarPopup(True); self.dt_start.setDisplayFormat("yyyy-MM-dd")
        self.lb_to = QLabel(" 至 ")
        self.dt_end   = QDateEdit(QDate.currentDate().addDays(30))
        self.dt_end.setCalendarPopup(True); self.dt_end.setDisplayFormat("yyyy-MM-dd")
        h.addWidget(self.dt_start); h.addWidget(self.lb_to); h.addWidget(self.dt_end)

        self.cmb.currentIndexChanged.connect(self._on_mode_change)
        self.dt_start.dateChanged.connect(lambda *_: self.changed.emit())
        self.dt_end.dateChanged.connect(lambda *_: self.changed.emit())
        self._on_mode_change()

    def _on_mode_change(self):
        is_custom = self.cmb.currentData() == "custom"
        for w in (self.dt_start, self.lb_to, self.dt_end):
            w.setVisible(is_custom)
        self.changed.emit()

    def _today(self):
        return date.today()

    def start_date(self):
        m = self.cmb.currentData()
        t = self._today()
        if m == "today":  return t
        if m == "week":   return t - timedelta(days=t.weekday())
        if m == "month":  return t.replace(day=1)
        if m == "30d":    return t - timedelta(days=30)
        if m == "custom": return self.dt_start.date().toPyDate()
        return None  # all

    def end_date(self):
        m = self.cmb.currentData()
        t = self._today()
        if m == "today":  return t
        if m == "week":   return t + timedelta(days=6 - t.weekday())
        if m == "month":
            # 月末
            if t.month == 12:
                return date(t.year + 1, 1, 1) - timedelta(days=1)
            return date(t.year, t.month + 1, 1) - timedelta(days=1)
        if m == "30d":    return t
        if m == "custom": return self.dt_end.date().toPyDate()
        return None  # all


class DateFilter(QWidget):
    """单日期筛选 — 模式下拉 + 按需展开的日期选择框。

    模式：今天 / 昨天 / 选择日期 / 全部（可选）
    """
    changed = pyqtSignal()

    def __init__(self, default: str = "today", allow_all: bool = True, parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(6)

        presets = [("今天", "today"), ("昨天", "yesterday"), ("选择日期", "custom")]
        if allow_all:
            presets.append(("全部", "all"))

        self.cmb = QComboBox()
        for label_, key in presets:
            self.cmb.addItem(label_, key)
        idx = next((i for i, p in enumerate(presets) if p[1] == default), 0)
        self.cmb.setCurrentIndex(idx)
        h.addWidget(self.cmb)

        self.dt = QDateEdit(QDate.currentDate())
        self.dt.setCalendarPopup(True); self.dt.setDisplayFormat("yyyy-MM-dd")
        h.addWidget(self.dt)

        self.cmb.currentIndexChanged.connect(self._on_mode_change)
        self.dt.dateChanged.connect(lambda *_: self.changed.emit())
        self._on_mode_change()

    def _on_mode_change(self):
        self.dt.setVisible(self.cmb.currentData() == "custom")
        self.changed.emit()

    def value(self):
        m = self.cmb.currentData()
        t = date.today()
        if m == "today":     return t
        if m == "yesterday": return t - timedelta(days=1)
        if m == "custom":    return self.dt.date().toPyDate()
        return None  # all

    def set_value(self, d):
        """主动设值（用于初始化或外部联动）。"""
        if d is None:
            i = self.cmb.findData("all")
            if i >= 0: self.cmb.setCurrentIndex(i)
            return
        self.cmb.setCurrentIndex(self.cmb.findData("custom"))
        self.dt.setDate(QDate(d.year, d.month, d.day))
