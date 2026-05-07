"""统一主题样式 — 现代化、扁平、配色协调。

设计要点：
- 主色：#4F8AC9（柔和蓝）
- 强调色：#27AE60（绿）/ #E67E22（橙）/ #E74C3C（红）
- 背景层级：#F4F7FB（窗口）/ #FFFFFF（卡片/表格）/ #ECF1F7（边框）
- 字号：标题 18-20 / 正文 13-14
- 圆角：6px；按钮 hover 反馈；输入框 focus 高亮
"""

PRIMARY    = "#4F8AC9"
PRIMARY_HV = "#3B72AE"
SUCCESS    = "#27AE60"
SUCCESS_HV = "#1F8B4C"
WARN       = "#E67E22"
WARN_HV    = "#C9651A"
DANGER     = "#E74C3C"
DANGER_HV  = "#C0392B"
GREY       = "#7F8C8D"

APP_QSS = f"""
QWidget {{
    background: #F4F7FB;
    color: #2C3E50;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{ background: #F4F7FB; }}

/* ===== 标题 / 文本 ===== */
QLabel#H1   {{ font-size: 20px; font-weight: 600; color: #1B2A41; padding: 6px 2px; }}
QLabel#H2   {{ font-size: 15px; font-weight: 600; color: #1B2A41; padding: 4px 2px; }}
QLabel#tip  {{ color: {GREY}; font-size: 12px; }}
QLabel#tag  {{ background:{PRIMARY}; color:white; border-radius:10px;
              padding: 2px 10px; font-size:12px; }}

/* ===== 输入控件 ===== */
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    background: white;
    border: 1px solid #D8DFEA;
    border-radius: 6px;
    padding: 6px 9px;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {PRIMARY};
}}
QLineEdit[search="true"] {{
    background: white;
    padding: 7px 12px;
    border-radius: 18px;
    border: 1px solid #D8DFEA;
}}
QLineEdit[search="true"]:focus {{ border: 1px solid {PRIMARY}; }}

QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: none; }}

/* ===== 按钮 ===== */
QPushButton {{
    background: {PRIMARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}}
QPushButton:hover  {{ background: {PRIMARY_HV}; }}
QPushButton:disabled {{ background: #B5BCC6; color:#ECF1F7; }}

QPushButton[kind="success"] {{ background: {SUCCESS}; }}
QPushButton[kind="success"]:hover {{ background: {SUCCESS_HV}; }}
QPushButton[kind="warn"]    {{ background: {WARN}; }}
QPushButton[kind="warn"]:hover    {{ background: {WARN_HV}; }}
QPushButton[kind="danger"]  {{ background: {DANGER}; }}
QPushButton[kind="danger"]:hover  {{ background: {DANGER_HV}; }}
QPushButton[kind="ghost"] {{
    background: transparent; color: {PRIMARY};
    border: 1px solid #D8DFEA;
}}
QPushButton[kind="ghost"]:hover {{
    background: #EAF1FA; border: 1px solid {PRIMARY};
}}

/* ===== 表格 ===== */
QTableWidget, QTableView {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #EEF2F8;
    selection-background-color: #DCE9F8;
    selection-color: #1B2A41;
    alternate-background-color: #FAFCFE;
}}
QTableWidget::item {{ padding: 6px; }}
QHeaderView::section {{
    background: #EDF2F8;
    color: #34495E;
    border: none;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #E2E8F0;
    padding: 7px 8px;
    font-weight: 600;
}}
QTableCornerButton::section {{ background: #EDF2F8; border:none; }}

/* ===== Tabs ===== */
QTabWidget::pane {{
    border: 1px solid #E2E8F0;
    background: white;
    border-radius: 8px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    padding: 9px 22px;
    border: 1px solid transparent;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #7F8C8D;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background: white;
    color: {PRIMARY};
    border: 1px solid #E2E8F0;
    border-bottom: 1px solid white;
}}
QTabBar::tab:hover:!selected {{ color: {PRIMARY_HV}; }}

/* ===== 菜单/状态栏 ===== */
QMenuBar {{ background: white; border-bottom: 1px solid #E2E8F0; }}
QMenuBar::item {{ padding: 6px 14px; background: transparent; }}
QMenuBar::item:selected {{ background: #EAF1FA; color: {PRIMARY}; }}
QMenu {{ background: white; border: 1px solid #E2E8F0; }}
QMenu::item:selected {{ background: #EAF1FA; color: {PRIMARY}; }}
QStatusBar {{ background: white; border-top: 1px solid #E2E8F0; }}

/* ===== 滚动条 ===== */
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #C8D2DF; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #A6B3C2; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: #C8D2DF; border-radius: 5px; min-width: 30px; }}
"""


def apply_theme(app):
    """对 QApplication 应用主题。"""
    app.setStyleSheet(APP_QSS)
