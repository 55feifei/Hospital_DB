"""登录窗口（含角色选择 + 患者注册入口）。"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QApplication, QFrame, QToolButton, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

from dao.account_dao import AccountDAO
from utils import is_valid_username
from config import APP_NAME
from ui.register_dialog import RegisterDialog


ROLE_LIST = [
    ("patient", "患者", "#27AE60"),
    ("doctor",  "医生", "#4F8AC9"),
    ("admin",   "管理员", "#8E44AD"),
]


class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.selected_role = "patient"
        self._role_buttons = {}
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"{APP_NAME} - 登录")
        self.resize(820, 520)
        self.setStyleSheet("""
            QWidget#loginRoot { background: #F4F7FB; }
            QFrame#card {
                background: white;
                border-radius: 14px;
            }
            QFrame#hero {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1F4974, stop:1 #3B72AE);
                border-top-left-radius: 14px;
                border-bottom-left-radius: 14px;
            }
            QFrame#hero QLabel {
                background: transparent;
                color: #FFFFFF;
            }
            QLabel#hero_title  {
                background: transparent;
                color: #FFFFFF;
                font-size: 28px; font-weight: 800; letter-spacing: 1px;
            }
            QLabel#hero_sub    {
                background: transparent;
                color: #F4F8FE;
                font-size: 14px; font-weight: 500;
            }
            QLabel#title       { font-size: 22px; font-weight: 700; color: #1B2A41; }
            QLabel#tip         { color: #7F8C8D; font-size: 12px; }
            QLineEdit {
                padding: 9px 12px;
                border: 1px solid #D8DFEA; border-radius: 6px;
                background: white; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #4F8AC9; }
            QPushButton#primary {
                padding: 10px;
                background: #4F8AC9; color: white;
                border: none; border-radius: 6px; font-size: 14px; font-weight: 600;
            }
            QPushButton#primary:hover { background: #3B72AE; }
            QPushButton#linklike {
                background: transparent; color: #4F8AC9; border: none;
                font-size: 13px; padding: 2px;
            }
            QPushButton#linklike:hover { color: #3B72AE; text-decoration: underline; }
            QToolButton[role-btn="true"] {
                background: white;
                border: 1.5px solid #D8DFEA;
                border-radius: 8px;
                padding: 9px 0;
                font-size: 13px;
                color: #34495E;
            }
            QToolButton[role-btn="true"]:hover { border-color: #4F8AC9; }
            QToolButton[role-btn="true"][selected="true"] {
                background: #EAF1FA;
                border: 1.5px solid #4F8AC9;
                color: #2C5C8E;
                font-weight: 600;
            }
        """)
        self.setObjectName("loginRoot")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(40, 35, 40, 35)

        card = QFrame()
        card.setObjectName("card")
        outer.addWidget(card)

        h = QHBoxLayout(card)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # ---------- 左侧 hero ----------
        hero = QFrame()
        hero.setObjectName("hero")
        hero.setFixedWidth(320)
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(34, 34, 34, 34)
        hv.addStretch(1)
        ht = QLabel("医院门诊\n预约管理系统")
        ht.setObjectName("hero_title")
        ht.setWordWrap(True)
        hv.addWidget(ht)
        hs = QLabel("登录后即可在线挂号、查看就诊记录、\n医生写病历、管理员调度排班。")
        hs.setObjectName("hero_sub")
        hs.setWordWrap(True)
        hv.addWidget(hs)
        hv.addStretch(2)
        h.addWidget(hero)

        # ---------- 右侧表单 ----------
        right = QWidget()
        h.addWidget(right, 1)
        v = QVBoxLayout(right)
        v.setContentsMargins(40, 30, 40, 30)
        v.setSpacing(12)

        title = QLabel("欢迎登录")
        title.setObjectName("title")
        v.addWidget(title)

        tip = QLabel("默认账号：admin / doc001 / pat001    密码：123456")
        tip.setObjectName("tip")
        v.addWidget(tip)

        v.addSpacing(6)

        # 角色选择
        role_label = QLabel("登录身份")
        role_label.setStyleSheet("color:#34495E; font-weight:600;")
        v.addWidget(role_label)

        role_row = QHBoxLayout()
        role_row.setSpacing(10)
        for role_key, role_label_text, _ in ROLE_LIST:
            btn = QToolButton()
            btn.setText(role_label_text)
            btn.setProperty("role-btn", True)
            btn.setProperty("selected", role_key == self.selected_role)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, r=role_key: self._select_role(r))
            btn.setMinimumHeight(38)
            self._role_buttons[role_key] = btn
            role_row.addWidget(btn, 1)
        v.addLayout(role_row)

        v.addSpacing(4)
        v.addWidget(self._field_label("用户名"))
        self.in_user = QLineEdit()
        self.in_user.setPlaceholderText("请输入用户名")
        v.addWidget(self.in_user)

        v.addWidget(self._field_label("密码"))
        self.in_pwd = QLineEdit()
        self.in_pwd.setEchoMode(QLineEdit.Password)
        self.in_pwd.setPlaceholderText("请输入密码")
        self.in_pwd.returnPressed.connect(self._do_login)
        v.addWidget(self.in_pwd)

        v.addSpacing(4)
        btn_login = QPushButton("登 录")
        btn_login.setObjectName("primary")
        btn_login.clicked.connect(self._do_login)
        v.addWidget(btn_login)

        # 注册入口
        bottom = QHBoxLayout()
        bottom.addStretch()
        lbl = QLabel("还没有账号？")
        lbl.setStyleSheet("color:#7F8C8D;")
        bottom.addWidget(lbl)
        btn_reg = QPushButton("立即注册（患者）")
        btn_reg.setObjectName("linklike")
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.clicked.connect(self._open_register)
        bottom.addWidget(btn_reg)
        v.addLayout(bottom)

        self._refresh_role_styles()

    def _field_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("color:#34495E; font-weight:500;")
        return l

    def _select_role(self, role):
        self.selected_role = role
        self._refresh_role_styles()
        # 提示用户名格式
        ph = {"patient": "如 pat001", "doctor": "如 doc001", "admin": "如 admin"}
        self.in_user.setPlaceholderText(f"请输入用户名（{ph.get(role,'')}）")

    def _refresh_role_styles(self):
        for k, b in self._role_buttons.items():
            b.setProperty("selected", k == self.selected_role)
            b.setChecked(k == self.selected_role)
            b.style().unpolish(b); b.style().polish(b)

    def _open_register(self):
        dlg = RegisterDialog(self)
        if dlg.exec_():
            QMessageBox.information(self, "注册成功",
                f"账号「{dlg.created_username}」已创建，请登录。")
            self._select_role("patient")
            self.in_user.setText(dlg.created_username)
            self.in_pwd.setFocus()

    def _do_login(self):
        username = self.in_user.text().strip()
        password = self.in_pwd.text()

        if not is_valid_username(username):
            QMessageBox.warning(self, "校验失败", "用户名仅允许字母、数字、下划线（3-30 位）")
            return
        if not password:
            QMessageBox.warning(self, "校验失败", "请输入密码")
            return

        try:
            user = AccountDAO.authenticate(username, password)
        except Exception as e:
            QMessageBox.critical(self, "数据库错误",
                                 f"无法连接数据库，请检查 src/config.py 中的密码。\n\n错误：{e}")
            return

        if not user:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")
            return

        # 校验角色一致
        if user["role"] != self.selected_role:
            QMessageBox.warning(self, "身份不符",
                f"该账号的实际身份为「{user['role']}」，\n"
                f"请在登录页选择正确的身份。")
            return

        self.on_success(user)
        self.close()
