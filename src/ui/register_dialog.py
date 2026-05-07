"""患者自助注册对话框。

工作流：
1. 校验所有字段格式
2. 检查 username 是否被占用、id_card 是否已存在
3. 事务：先 INSERT patient → 拿到 patient_id → 再 INSERT user_account(role='patient', ref_id=patient_id)
"""

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QDialogButtonBox,
    QMessageBox, QLabel, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt5.QtCore import QDate, Qt

from db import Database
from dao.account_dao import AccountDAO
from dao.patient_dao import PatientDAO
from utils import (
    is_valid_phone, is_valid_id_card, is_valid_username, sha256
)


class RegisterDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.created_username = None
        self.setWindowTitle("注册新账号 — 患者")
        self.setMinimumWidth(440)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("注册患者账号")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#1B2A41;")
        root.addWidget(title)

        tip = QLabel("注册后即可使用该账号登录并预约挂号")
        tip.setStyleSheet("color:#7F8C8D;")
        root.addWidget(tip)

        line = QFrame(); line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#E2E8F0;")
        root.addWidget(line)

        f = QFormLayout()
        f.setSpacing(10)
        f.setLabelAlignment(Qt.AlignRight)

        self.in_user = QLineEdit()
        self.in_user.setPlaceholderText("3-30 位字母/数字/下划线")
        self.in_pwd  = QLineEdit(); self.in_pwd.setEchoMode(QLineEdit.Password)
        self.in_pwd.setPlaceholderText("至少 6 位")
        self.in_pwd2 = QLineEdit(); self.in_pwd2.setEchoMode(QLineEdit.Password)
        self.in_pwd2.setPlaceholderText("再输入一次")

        self.in_name = QLineEdit()
        self.cmb_g = QComboBox(); self.cmb_g.addItems(["男", "女"])
        self.dt_birth = QDateEdit(QDate(1995, 1, 1))
        self.dt_birth.setCalendarPopup(True)
        self.dt_birth.setDisplayFormat("yyyy-MM-dd")
        self.in_idc = QLineEdit(); self.in_idc.setPlaceholderText("18 位身份证号")
        self.in_phone = QLineEdit(); self.in_phone.setPlaceholderText("11 位手机号")
        self.in_addr = QLineEdit(); self.in_addr.setPlaceholderText("可选")

        f.addRow("登录用户名 *", self.in_user)
        f.addRow("登录密码 *",   self.in_pwd)
        f.addRow("确认密码 *",   self.in_pwd2)
        f.addRow("真实姓名 *",   self.in_name)
        f.addRow("性别",        self.cmb_g)
        f.addRow("出生日期",    self.dt_birth)
        f.addRow("身份证号 *",   self.in_idc)
        f.addRow("手机号 *",     self.in_phone)
        f.addRow("地址",        self.in_addr)
        root.addLayout(f)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("注册")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._submit)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _submit(self):
        u  = self.in_user.text().strip()
        p1 = self.in_pwd.text()
        p2 = self.in_pwd2.text()
        nm = self.in_name.text().strip()
        idc = self.in_idc.text().strip()
        ph = self.in_phone.text().strip()

        if not is_valid_username(u):
            QMessageBox.warning(self, "提示", "用户名格式不正确（3-30 位字母/数字/下划线）"); return
        if len(p1) < 6:
            QMessageBox.warning(self, "提示", "密码至少 6 位"); return
        if p1 != p2:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致"); return
        if not nm:
            QMessageBox.warning(self, "提示", "请输入真实姓名"); return
        if not is_valid_id_card(idc):
            QMessageBox.warning(self, "提示", "身份证号格式不正确"); return
        if not is_valid_phone(ph):
            QMessageBox.warning(self, "提示", "手机号格式不正确"); return

        # 检查唯一性
        try:
            if Database.query("SELECT 1 FROM user_account WHERE username=%s", (u,)):
                QMessageBox.warning(self, "用户名已存在", "请换一个用户名"); return
            if PatientDAO.find_by_idcard(idc):
                QMessageBox.warning(self, "身份证已存在", "该身份证已注册，请直接登录或联系管理员"); return
            if Database.query("SELECT 1 FROM patient WHERE phone=%s", (ph,)):
                QMessageBox.warning(self, "手机号已存在", "该手机号已被占用"); return
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e)); return

        gender = self.cmb_g.currentText()
        birth  = self.dt_birth.date().toPyDate()
        addr   = self.in_addr.text().strip() or None

        # 事务：插 patient → 插 user_account
        try:
            with Database.transaction() as (cur, _conn):
                cur.execute(
                    "INSERT INTO patient(name, gender, birth_date, id_card, phone, address) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (nm, gender, birth, idc, ph, addr)
                )
                pid = cur.lastrowid
                cur.execute(
                    "INSERT INTO user_account(username, password_hash, role, ref_id) "
                    "VALUES (%s,%s,'patient',%s)",
                    (u, sha256(p1), pid)
                )
        except Exception as e:
            QMessageBox.critical(self, "注册失败", str(e)); return

        self.created_username = u
        self.accept()
