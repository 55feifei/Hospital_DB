"""管理员面板：科室 / 医生 / 患者 / 排班 / 预约 / 账号 / 统计。

要点：
- 每个 Tab 都有搜索条 + 多种排序方式
- 医生新增/编辑时一并维护登录账号
- 新增"账号管理"Tab — 列出全部账号并支持启用/停用/重置密码
- 列表均启用 QTable 排序（点击列头切换升降序）
"""

from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QDateEdit, QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QDialogButtonBox, QTextEdit, QCheckBox, QFrame, QInputDialog
)
from PyQt5.QtCore import QDate, Qt

from db import Database
from dao.department_dao import DepartmentDAO
from dao.doctor_dao import DoctorDAO
from dao.patient_dao import PatientDAO
from dao.schedule_dao import ScheduleDAO
from dao.appointment_dao import AppointmentDAO
from dao.account_dao import AccountDAO
from service.appointment_service import AppointmentService
from utils import is_valid_phone, is_valid_id_card, is_valid_username, sha256
from ui.widgets import (
    setup_table, fill_table, search_field, primary_btn, label,
    NumericItem, make_status_item, STATUS_COLORS,
    DateRangeFilter, DateFilter
)


TITLE_LIST = ["住院医师", "主治医师", "副主任医师", "主任医师"]
DOC_STATUS = ["在职", "停诊", "离职"]
APPT_STATUS = ["已预约", "已就诊", "已取消", "爽约"]


class AdminPanel(QWidget):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(label("管理员控制台", "h1"))
        tag = QLabel(self.user['username'])
        tag.setObjectName("tag")
        head.addWidget(tag)
        head.addStretch()
        layout.addLayout(head)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._tab_dept()
        self._tab_doctor()
        self._tab_patient()
        self._tab_schedule()
        self._tab_appointment()
        self._tab_account()
        self._tab_stats()

    # ============================== 科室 ==============================
    def _tab_dept(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("关键字"))
        self.in_dept_kw = search_field("科室名称/描述/位置…")
        self.in_dept_kw.textChanged.connect(self._dept_load)
        bar.addWidget(self.in_dept_kw, 1)
        bar.addStretch()
        for lt, fn in [("新增", self._dept_add), ("修改", self._dept_edit),
                       ("删除", self._dept_del), ("刷新", self._dept_load)]:
            b = primary_btn(lt, "ghost" if lt in ("修改", "刷新") else "")
            if lt == "删除": b.setProperty("kind", "danger")
            elif lt == "新增": b.setProperty("kind", "success")
            b.clicked.connect(fn)
            bar.addWidget(b)
        v.addLayout(bar)

        self.tbl_dept = QTableWidget()
        setup_table(self.tbl_dept, ["ID", "科室名", "描述", "位置", "医生数"])
        v.addWidget(self.tbl_dept)
        self.tabs.addTab(w, "科室")
        self._dept_load()

    def _dept_load(self):
        kw = self.in_dept_kw.text().strip().lower()
        # 复杂查询：LEFT JOIN 子查询统计医生数
        rows = Database.query("""
            SELECT dp.dept_id, dp.dept_name, dp.description, dp.location,
                   (SELECT COUNT(*) FROM doctor d WHERE d.dept_id=dp.dept_id) AS doctor_count
            FROM department dp ORDER BY dp.dept_id
        """)
        if kw:
            rows = [r for r in rows if kw in (str(r.get("dept_name") or "")
                    + (r.get("description") or "") + (r.get("location") or "")).lower()]

        self.tbl_dept.setSortingEnabled(False)
        self.tbl_dept.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_dept.setItem(r, 0, NumericItem(row["dept_id"]))
            self.tbl_dept.setItem(r, 1, QTableWidgetItem(str(row["dept_name"] or "")))
            self.tbl_dept.setItem(r, 2, QTableWidgetItem(str(row.get("description") or "")))
            self.tbl_dept.setItem(r, 3, QTableWidgetItem(str(row.get("location") or "")))
            self.tbl_dept.setItem(r, 4, NumericItem(row["doctor_count"]))
        self.tbl_dept.setSortingEnabled(True)

    def _dept_add(self):
        dlg = DeptDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                DepartmentDAO.create(*dlg.get_values())
                self._dept_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _dept_edit(self):
        r = self.tbl_dept.currentRow()
        if r < 0: return
        did = int(self.tbl_dept.item(r, 0).text())
        cur = DepartmentDAO.get(did)
        dlg = DeptDialog(self, cur)
        if dlg.exec_() == QDialog.Accepted:
            try:
                DepartmentDAO.update(did, *dlg.get_values())
                self._dept_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _dept_del(self):
        r = self.tbl_dept.currentRow()
        if r < 0: return
        did = int(self.tbl_dept.item(r, 0).text())
        if QMessageBox.question(self, "确认", "删除该科室？") != QMessageBox.Yes: return
        try:
            DepartmentDAO.delete(did)
            self._dept_load()
        except Exception as e:
            QMessageBox.warning(self, "无法删除", f"该科室可能尚有医生引用：\n{e}")

    # ============================== 医生 ==============================
    def _tab_doctor(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QGridLayout()
        bar.setHorizontalSpacing(8)

        bar.addWidget(QLabel("关键字"), 0, 0)
        self.in_doc_kw = search_field("姓名/科室/简介…")
        self.in_doc_kw.textChanged.connect(self._doc_load)
        bar.addWidget(self.in_doc_kw, 0, 1)

        bar.addWidget(QLabel("科室"), 0, 2)
        self.cmb_doc_dept = QComboBox()
        self.cmb_doc_dept.addItem("全部", None)
        for d in DepartmentDAO.list_all():
            self.cmb_doc_dept.addItem(d["dept_name"], d["dept_id"])
        self.cmb_doc_dept.currentIndexChanged.connect(self._doc_load)
        bar.addWidget(self.cmb_doc_dept, 0, 3)

        bar.addWidget(QLabel("职称"), 0, 4)
        self.cmb_doc_title = QComboBox()
        self.cmb_doc_title.addItem("全部", "")
        for t in TITLE_LIST: self.cmb_doc_title.addItem(t, t)
        self.cmb_doc_title.currentIndexChanged.connect(self._doc_load)
        bar.addWidget(self.cmb_doc_title, 0, 5)

        bar.addWidget(QLabel("状态"), 0, 6)
        self.cmb_doc_status = QComboBox()
        self.cmb_doc_status.addItem("全部", "")
        for s in DOC_STATUS: self.cmb_doc_status.addItem(s, s)
        self.cmb_doc_status.currentIndexChanged.connect(self._doc_load)
        bar.addWidget(self.cmb_doc_status, 0, 7)

        bar.addWidget(QLabel("排序"), 1, 0)
        self.cmb_doc_order = QComboBox()
        for txt, k in [("ID ↑", ("doctor_id", True)),
                       ("姓名", ("name", True)),
                       ("科室", ("dept_name", True)),
                       ("职称", ("title", True)),
                       ("挂号费 ↑", ("fee", True)),
                       ("挂号费 ↓", ("fee", False)),
                       ("预约数 ↓", ("appt_count", False))]:
            self.cmb_doc_order.addItem(txt, k)
        self.cmb_doc_order.currentIndexChanged.connect(self._doc_load)
        bar.addWidget(self.cmb_doc_order, 1, 1)

        op = QHBoxLayout()
        op.addStretch()
        for lt, fn, kind in [("新增（含账号）", self._doc_add, "success"),
                             ("修改", self._doc_edit, "ghost"),
                             ("删除", self._doc_del, "danger"),
                             ("重置账号密码", self._doc_reset_pwd, "warn")]:
            b = primary_btn(lt, kind)
            b.clicked.connect(fn)
            op.addWidget(b)
        wrap = QWidget(); wrap.setLayout(op)
        bar.addWidget(wrap, 1, 2, 1, 6)
        v.addLayout(bar)

        self.tbl_doc = QTableWidget()
        setup_table(
            self.tbl_doc,
            ["ID", "姓名", "性别", "科室", "职称", "挂号费", "状态", "登录账号", "预约数"]
        )
        v.addWidget(self.tbl_doc)
        self.tabs.addTab(w, "医生")
        self._doc_load()

    def _doc_load(self):
        order_key, asc = self.cmb_doc_order.currentData()
        rows = DoctorDAO.search(
            keyword=self.in_doc_kw.text().strip(),
            dept_id=self.cmb_doc_dept.currentData(),
            status=self.cmb_doc_status.currentData() or "",
            title=self.cmb_doc_title.currentData() or "",
            order_by=order_key, asc=asc,
        )
        # 一次性查所有医生账号
        accounts = {a["ref_id"]: a for a in Database.query(
            "SELECT * FROM user_account WHERE role='doctor'"
        )}
        self.tbl_doc.setSortingEnabled(False)
        self.tbl_doc.setRowCount(len(rows))
        for r, row in enumerate(rows):
            acc = accounts.get(row["doctor_id"])
            acc_disp = (acc["username"] + ("" if acc["is_active"] else "（停用）")) if acc else "—"
            self.tbl_doc.setItem(r, 0, NumericItem(row["doctor_id"]))
            self.tbl_doc.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.tbl_doc.setItem(r, 2, QTableWidgetItem(row["gender"]))
            self.tbl_doc.setItem(r, 3, QTableWidgetItem(row["dept_name"]))
            self.tbl_doc.setItem(r, 4, QTableWidgetItem(row["title"]))
            self.tbl_doc.setItem(r, 5, NumericItem(float(row["fee"]), f"¥{row['fee']}"))
            self.tbl_doc.setItem(r, 6, make_status_item(row["status"]))
            self.tbl_doc.setItem(r, 7, QTableWidgetItem(acc_disp))
            self.tbl_doc.setItem(r, 8, NumericItem(row.get("appt_count") or 0))
        self.tbl_doc.setSortingEnabled(True)

    def _doc_add(self):
        dlg = DoctorDialog(self, with_account=True)
        if dlg.exec_() == QDialog.Accepted:
            vals = dlg.get_values()
            acc = dlg.get_account_values()
            try:
                with Database.transaction() as (cur, _):
                    cur.execute(
                        "INSERT INTO doctor(dept_id, name, gender, title, fee, intro, status) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        vals
                    )
                    did = cur.lastrowid
                    cur.execute(
                        "INSERT INTO user_account(username, password_hash, role, ref_id) "
                        "VALUES (%s,%s,'doctor',%s)",
                        (acc["username"], sha256(acc["password"]), did)
                    )
                self._doc_load()
                QMessageBox.information(self, "成功",
                    f"已创建医生「{vals[1]}」并分配账号「{acc['username']}」")
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _doc_edit(self):
        r = self.tbl_doc.currentRow()
        if r < 0: return
        did = int(self.tbl_doc.item(r, 0).text())
        cur = DoctorDAO.get(did)
        dlg = DoctorDialog(self, cur)
        if dlg.exec_() == QDialog.Accepted:
            try:
                DoctorDAO.update(did, *dlg.get_values())
                self._doc_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _doc_del(self):
        r = self.tbl_doc.currentRow()
        if r < 0: return
        did = int(self.tbl_doc.item(r, 0).text())
        if QMessageBox.question(self, "确认",
                "删除该医生及其登录账号？") != QMessageBox.Yes: return
        try:
            with Database.transaction() as (cur, _):
                cur.execute("DELETE FROM user_account WHERE role='doctor' AND ref_id=%s", (did,))
                cur.execute("DELETE FROM doctor WHERE doctor_id=%s", (did,))
            self._doc_load()
        except Exception as e:
            QMessageBox.warning(self, "无法删除", f"触发器/外键阻止：\n{e}")

    def _doc_reset_pwd(self):
        r = self.tbl_doc.currentRow()
        if r < 0:
            QMessageBox.information(self, "提示", "请选中一行医生"); return
        did = int(self.tbl_doc.item(r, 0).text())
        acc = AccountDAO.get_by_doctor(did)
        if not acc:
            QMessageBox.warning(self, "提示", "该医生暂无登录账号，请先编辑或新增"); return
        new_pwd, ok = QInputDialog.getText(self, "重置密码",
            f"为账号「{acc['username']}」设置新密码：", QLineEdit.Password)
        if not ok:
            return
        if len(new_pwd) < 6:
            QMessageBox.warning(self, "提示", "密码至少 6 位"); return
        AccountDAO.change_password(acc["user_id"], new_pwd)
        QMessageBox.information(self, "成功", "密码已重置")

    # ============================== 患者 ==============================
    def _tab_patient(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("关键字"))
        self.in_pkw = search_field("姓名/手机/身份证/地址…")
        self.in_pkw.textChanged.connect(self._pat_load)
        bar.addWidget(self.in_pkw, 1)

        bar.addWidget(QLabel("性别"))
        self.cmb_p_gender = QComboBox()
        self.cmb_p_gender.addItem("全部", "")
        self.cmb_p_gender.addItem("男", "男")
        self.cmb_p_gender.addItem("女", "女")
        self.cmb_p_gender.currentIndexChanged.connect(self._pat_load)
        bar.addWidget(self.cmb_p_gender)

        bar.addWidget(QLabel("排序"))
        self.cmb_p_order = QComboBox()
        for txt, k in [("ID ↑", ("patient_id", True)),
                       ("姓名", ("name", True)),
                       ("出生日期", ("birth_date", True)),
                       ("预约数 ↓", ("appt_count", False)),
                       ("注册时间 ↓", ("created_at", False))]:
            self.cmb_p_order.addItem(txt, k)
        self.cmb_p_order.currentIndexChanged.connect(self._pat_load)
        bar.addWidget(self.cmb_p_order)
        bar.addStretch()
        for lt, fn, kind in [("修改", self._pat_edit, "ghost"),
                             ("删除", self._pat_del, "danger")]:
            b = primary_btn(lt, kind); b.clicked.connect(fn); bar.addWidget(b)
        v.addLayout(bar)

        self.tbl_pat = QTableWidget()
        setup_table(
            self.tbl_pat,
            ["ID", "姓名", "性别", "出生", "身份证", "电话", "地址", "预约数"]
        )
        v.addWidget(self.tbl_pat)
        self.tabs.addTab(w, "患者")
        self._pat_load()

    def _pat_load(self):
        order_key, asc = self.cmb_p_order.currentData()
        rows = PatientDAO.search(
            keyword=self.in_pkw.text().strip(),
            gender=self.cmb_p_gender.currentData() or "",
            order_by=order_key, asc=asc,
        )
        self.tbl_pat.setSortingEnabled(False)
        self.tbl_pat.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_pat.setItem(r, 0, NumericItem(row["patient_id"]))
            self.tbl_pat.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.tbl_pat.setItem(r, 2, QTableWidgetItem(row["gender"]))
            self.tbl_pat.setItem(r, 3, QTableWidgetItem(str(row.get("birth_date") or "")))
            self.tbl_pat.setItem(r, 4, QTableWidgetItem(row["id_card"]))
            self.tbl_pat.setItem(r, 5, QTableWidgetItem(row["phone"]))
            self.tbl_pat.setItem(r, 6, QTableWidgetItem(str(row.get("address") or "")))
            self.tbl_pat.setItem(r, 7, NumericItem(row.get("appt_count") or 0))
        self.tbl_pat.setSortingEnabled(True)

    def _pat_add(self):
        dlg = PatientDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                PatientDAO.create(*dlg.get_values())
                self._pat_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _pat_edit(self):
        r = self.tbl_pat.currentRow()
        if r < 0: return
        pid = int(self.tbl_pat.item(r, 0).text())
        cur = PatientDAO.get(pid)
        dlg = PatientDialog(self, cur)
        if dlg.exec_() == QDialog.Accepted:
            try:
                PatientDAO.update(pid, *dlg.get_values())
                self._pat_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _pat_del(self):
        r = self.tbl_pat.currentRow()
        if r < 0: return
        pid = int(self.tbl_pat.item(r, 0).text())
        if QMessageBox.question(self, "确认", "删除该患者？") != QMessageBox.Yes: return
        try:
            with Database.transaction() as (cur, _):
                cur.execute("DELETE FROM user_account WHERE role='patient' AND ref_id=%s", (pid,))
                cur.execute("DELETE FROM patient WHERE patient_id=%s", (pid,))
            self._pat_load()
        except Exception as e:
            QMessageBox.warning(self, "无法删除", str(e))

    # ============================== 排班 ==============================
    def _tab_schedule(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QGridLayout()
        bar.setHorizontalSpacing(8)

        bar.addWidget(QLabel("科室"), 0, 0)
        self.cmb_sch_dept = QComboBox()
        self.cmb_sch_dept.addItem("全部", None)
        for d in DepartmentDAO.list_all():
            self.cmb_sch_dept.addItem(d["dept_name"], d["dept_id"])
        self.cmb_sch_dept.currentIndexChanged.connect(self._sch_reload_doctors)
        bar.addWidget(self.cmb_sch_dept, 0, 1)

        bar.addWidget(QLabel("医生"), 0, 2)
        self.cmb_sch_doc = QComboBox()
        self.cmb_sch_doc.currentIndexChanged.connect(self._sch_load)
        bar.addWidget(self.cmb_sch_doc, 0, 3)

        bar.addWidget(QLabel("状态"), 0, 4)
        self.cmb_sch_status = QComboBox()
        self.cmb_sch_status.addItem("全部", "")
        self.cmb_sch_status.addItem("正常", "正常")
        self.cmb_sch_status.addItem("停诊", "停诊")
        self.cmb_sch_status.currentIndexChanged.connect(self._sch_load)
        bar.addWidget(self.cmb_sch_status, 0, 5)

        bar.addWidget(QLabel("日期"), 1, 0)
        self.dt_sch_range = DateRangeFilter(default="month")
        self.dt_sch_range.changed.connect(self._sch_load)
        bar.addWidget(self.dt_sch_range, 1, 1, 1, 3)

        bar.addWidget(QLabel("排序"), 1, 4)
        self.cmb_sch_order = QComboBox()
        for txt, k in [("日期 ↑", ("work_date", True)),
                       ("日期 ↓", ("work_date", False)),
                       ("剩余号源 ↓", ("remaining", False)),
                       ("医生", ("doctor_name", True))]:
            self.cmb_sch_order.addItem(txt, k)
        self.cmb_sch_order.currentIndexChanged.connect(self._sch_load)
        bar.addWidget(self.cmb_sch_order, 1, 5)

        op = QHBoxLayout()
        op.addStretch()
        for lt, fn, kind in [("查询", self._sch_load, ""),
                             ("新增排班", self._sch_add, "success"),
                             ("停诊/恢复", self._sch_toggle, "warn"),
                             ("删除", self._sch_del, "danger")]:
            b = primary_btn(lt, kind); b.clicked.connect(fn); op.addWidget(b)
        wrap2 = QWidget(); wrap2.setLayout(op)
        bar.addWidget(wrap2, 0, 6, 2, 1)
        v.addLayout(bar)

        self.tbl_sch = QTableWidget()
        setup_table(
            self.tbl_sch,
            ["ID", "日期", "时段", "医生", "科室", "总号源", "剩余", "状态"]
        )
        v.addWidget(self.tbl_sch)
        self.tabs.addTab(w, "排班")
        self._sch_reload_doctors()

    def _sch_reload_doctors(self):
        self.cmb_sch_doc.blockSignals(True)
        self.cmb_sch_doc.clear()
        self.cmb_sch_doc.addItem("全部医生", None)
        dept_id = self.cmb_sch_dept.currentData()
        docs = DoctorDAO.list_by_dept(dept_id) if dept_id else DoctorDAO.list_all()
        for d in docs:
            self.cmb_sch_doc.addItem(f"{d['name']}（{d['dept_name']}）", d["doctor_id"])
        self.cmb_sch_doc.blockSignals(False)
        self._sch_load()

    def _sch_load(self):
        order_key, asc = self.cmb_sch_order.currentData()
        rows = ScheduleDAO.search_admin(
            doctor_id=self.cmb_sch_doc.currentData(),
            dept_id=self.cmb_sch_dept.currentData(),
            status=self.cmb_sch_status.currentData() or "",
            start_date=self.dt_sch_range.start_date(),
            end_date=self.dt_sch_range.end_date(),
            order_by=order_key, asc=asc,
        )
        self.tbl_sch.setSortingEnabled(False)
        self.tbl_sch.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_sch.setItem(r, 0, NumericItem(row["schedule_id"]))
            self.tbl_sch.setItem(r, 1, QTableWidgetItem(str(row["work_date"])))
            self.tbl_sch.setItem(r, 2, make_status_item(row["time_slot"]))
            self.tbl_sch.setItem(r, 3, QTableWidgetItem(row["doctor_name"]))
            self.tbl_sch.setItem(r, 4, QTableWidgetItem(row["dept_name"]))
            self.tbl_sch.setItem(r, 5, NumericItem(row["total_quota"]))
            self.tbl_sch.setItem(r, 6, NumericItem(row["remaining_quota"]))
            self.tbl_sch.setItem(r, 7, make_status_item(row["status"]))
        self.tbl_sch.setSortingEnabled(True)

    def _sch_add(self):
        did = self.cmb_sch_doc.currentData()
        if not did:
            QMessageBox.information(self, "提示", "请先在筛选区选定一个具体的医生再新增排班"); return
        dlg = ScheduleDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                d, slot, quota = dlg.get_values()
                ScheduleDAO.create(did, d, slot, quota)
                self._sch_load()
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _sch_toggle(self):
        r = self.tbl_sch.currentRow()
        if r < 0: return
        sid = int(self.tbl_sch.item(r, 0).text())
        cur = self.tbl_sch.item(r, 7).text()
        new = "停诊" if cur == "正常" else "正常"
        ScheduleDAO.set_status(sid, new); self._sch_load()

    def _sch_del(self):
        r = self.tbl_sch.currentRow()
        if r < 0: return
        sid = int(self.tbl_sch.item(r, 0).text())
        if QMessageBox.question(self, "确认", "删除该排班？") != QMessageBox.Yes: return
        try:
            ScheduleDAO.delete(sid); self._sch_load()
        except Exception as e:
            QMessageBox.warning(self, "无法删除", str(e))

    # ============================ 全部预约 ============================
    def _tab_appointment(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QGridLayout()
        bar.setHorizontalSpacing(8)

        bar.addWidget(QLabel("关键字"), 0, 0)
        self.in_appt_kw = search_field("患者/医生/科室/电话…")
        self.in_appt_kw.returnPressed.connect(self._appt_load)
        bar.addWidget(self.in_appt_kw, 0, 1)

        bar.addWidget(QLabel("状态"), 0, 2)
        self.cmb_appt_status = QComboBox()
        self.cmb_appt_status.addItem("全部", "")
        for s in APPT_STATUS: self.cmb_appt_status.addItem(s, s)
        bar.addWidget(self.cmb_appt_status, 0, 3)

        bar.addWidget(QLabel("科室"), 0, 4)
        self.cmb_appt_dept = QComboBox()
        self.cmb_appt_dept.addItem("全部", None)
        for d in DepartmentDAO.list_all():
            self.cmb_appt_dept.addItem(d["dept_name"], d["dept_id"])
        bar.addWidget(self.cmb_appt_dept, 0, 5)

        bar.addWidget(QLabel("日期"), 1, 0)
        self.dt_appt_range = DateRangeFilter(default="month")
        self.dt_appt_range.changed.connect(self._appt_load)
        bar.addWidget(self.dt_appt_range, 1, 1, 1, 3)

        bar.addWidget(QLabel("排序"), 1, 4)
        self.cmb_appt_order = QComboBox()
        for txt, k in [("创建时间 ↓", ("create_time", False)),
                       ("创建时间 ↑", ("create_time", True)),
                       ("就诊日期 ↓", ("work_date", False)),
                       ("患者", ("patient_name", True)),
                       ("医生", ("doctor_name", True)),
                       ("状态", ("status", True))]:
            self.cmb_appt_order.addItem(txt, k)
        bar.addWidget(self.cmb_appt_order, 1, 5)

        op = QHBoxLayout(); op.addStretch()
        b = primary_btn("查询"); b.clicked.connect(self._appt_load); op.addWidget(b)
        b2 = primary_btn("刷新", "ghost"); b2.clicked.connect(self._appt_load); op.addWidget(b2)
        wrap2 = QWidget(); wrap2.setLayout(op)
        bar.addWidget(wrap2, 0, 6, 2, 1)
        v.addLayout(bar)

        # 联动刷新：下拉/日期改动后自动查询（关键字仍走回车/查询按钮）
        self.cmb_appt_status.currentIndexChanged.connect(self._appt_load)
        self.cmb_appt_dept.currentIndexChanged.connect(self._appt_load)
        self.cmb_appt_order.currentIndexChanged.connect(self._appt_load)

        self.tbl_appt = QTableWidget()
        setup_table(
            self.tbl_appt,
            ["预约ID", "患者", "科室", "医生", "日期", "时段", "状态", "缴费", "金额", "创建时间"]
        )
        v.addWidget(self.tbl_appt)
        self.lb_appt_count = QLabel("共 0 条")
        self.lb_appt_count.setObjectName("tip")
        v.addWidget(self.lb_appt_count)
        self.tabs.addTab(w, "全部预约")
        self._appt_load()

    def _appt_load(self):
        order_key, asc = self.cmb_appt_order.currentData()
        rows = AppointmentDAO.search(
            keyword=self.in_appt_kw.text().strip(),
            status=self.cmb_appt_status.currentData() or "",
            dept_id=self.cmb_appt_dept.currentData(),
            start_date=self.dt_appt_range.start_date(),
            end_date=self.dt_appt_range.end_date(),
            order_by=order_key, asc=asc,
        )
        self.tbl_appt.setSortingEnabled(False)
        self.tbl_appt.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_appt.setItem(r, 0, NumericItem(row["appt_id"]))
            self.tbl_appt.setItem(r, 1, QTableWidgetItem(row["patient_name"]))
            self.tbl_appt.setItem(r, 2, QTableWidgetItem(row["dept_name"]))
            self.tbl_appt.setItem(r, 3, QTableWidgetItem(row["doctor_name"]))
            self.tbl_appt.setItem(r, 4, QTableWidgetItem(str(row["work_date"])))
            self.tbl_appt.setItem(r, 5, make_status_item(row["time_slot"]))
            self.tbl_appt.setItem(r, 6, make_status_item(row["status"]))
            self.tbl_appt.setItem(r, 7, make_status_item(row.get("pay_status") or "-"))
            amt = row.get("amount")
            self.tbl_appt.setItem(r, 8, NumericItem(amt or 0, f"¥{amt}" if amt else "-"))
            self.tbl_appt.setItem(r, 9, QTableWidgetItem(str(row.get("create_time") or "")))
        self.tbl_appt.setSortingEnabled(True)
        self.lb_appt_count.setText(f"共 {len(rows)} 条 (上限 1000)")

    # ============================== 账号管理 ==============================
    def _tab_account(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("关键字"))
        self.in_acc_kw = search_field("用户名/关联人姓名…")
        self.in_acc_kw.textChanged.connect(self._acc_render)
        bar.addWidget(self.in_acc_kw, 1)

        bar.addWidget(QLabel("角色"))
        self.cmb_acc_role = QComboBox()
        self.cmb_acc_role.addItem("全部", "")
        for r in ["admin", "doctor", "patient"]:
            self.cmb_acc_role.addItem(r, r)
        self.cmb_acc_role.currentIndexChanged.connect(self._acc_render)
        bar.addWidget(self.cmb_acc_role)

        bar.addWidget(QLabel("状态"))
        self.cmb_acc_active = QComboBox()
        self.cmb_acc_active.addItem("全部", None)
        self.cmb_acc_active.addItem("启用", 1)
        self.cmb_acc_active.addItem("停用", 0)
        self.cmb_acc_active.currentIndexChanged.connect(self._acc_render)
        bar.addWidget(self.cmb_acc_active)
        bar.addStretch()
        for lt, fn, kind in [("启用 / 停用", self._acc_toggle, "warn"),
                             ("重置密码", self._acc_reset_pwd, "ghost"),
                             ("刷新", self._acc_load, "ghost")]:
            b = primary_btn(lt, kind); b.clicked.connect(fn); bar.addWidget(b)
        v.addLayout(bar)

        self.tbl_acc = QTableWidget()
        setup_table(
            self.tbl_acc,
            ["用户ID", "用户名", "角色", "关联人", "所属科室", "状态", "创建时间", "上次登录"]
        )
        v.addWidget(self.tbl_acc)
        self.tabs.addTab(w, "账号")
        self._acc_load()

    def _acc_load(self):
        self._all_accounts = AccountDAO.list_with_owner()
        self._acc_render()

    def _acc_render(self):
        kw = self.in_acc_kw.text().strip().lower()
        role = self.cmb_acc_role.currentData() or ""
        active = self.cmb_acc_active.currentData()
        rows = list(self._all_accounts)
        if kw:
            rows = [r for r in rows
                    if kw in (r.get("username") or "").lower()
                    or kw in (r.get("owner_name") or "").lower()]
        if role:
            rows = [r for r in rows if r["role"] == role]
        if active is not None:
            rows = [r for r in rows if int(r["is_active"]) == active]

        self.tbl_acc.setSortingEnabled(False)
        self.tbl_acc.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_acc.setItem(r, 0, NumericItem(row["user_id"]))
            self.tbl_acc.setItem(r, 1, QTableWidgetItem(row["username"]))
            self.tbl_acc.setItem(r, 2, make_status_item(row["role"]))
            self.tbl_acc.setItem(r, 3, QTableWidgetItem(row.get("owner_name") or "—"))
            self.tbl_acc.setItem(r, 4, QTableWidgetItem(row.get("owner_dept") or "—"))
            status_text = "启用" if row["is_active"] else "停用"
            self.tbl_acc.setItem(r, 5, make_status_item(status_text))
            self.tbl_acc.setItem(r, 6, QTableWidgetItem(str(row.get("created_at") or "")))
            self.tbl_acc.setItem(r, 7, QTableWidgetItem(str(row.get("last_login") or "—")))
        self.tbl_acc.setSortingEnabled(True)

    def _acc_toggle(self):
        r = self.tbl_acc.currentRow()
        if r < 0: return
        uid = int(self.tbl_acc.item(r, 0).text())
        is_active = self.tbl_acc.item(r, 5).text() == "启用"
        AccountDAO.set_active(uid, not is_active)
        self._acc_load()

    def _acc_reset_pwd(self):
        r = self.tbl_acc.currentRow()
        if r < 0: return
        uid = int(self.tbl_acc.item(r, 0).text())
        username = self.tbl_acc.item(r, 1).text()
        new_pwd, ok = QInputDialog.getText(self, "重置密码",
            f"为账号「{username}」设置新密码（≥6 位）：", QLineEdit.Password)
        if not ok: return
        if len(new_pwd) < 6:
            QMessageBox.warning(self, "提示", "密码至少 6 位"); return
        AccountDAO.change_password(uid, new_pwd)
        QMessageBox.information(self, "成功", "密码已重置")

    # ============================== 统计 ==============================
    def _tab_stats(self):
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(QLabel("统计日期"))
        self.dt_stat = DateFilter(default="today", allow_all=False)
        row.addWidget(self.dt_stat)
        b1 = primary_btn("生成日报")
        b1.clicked.connect(self._do_stat); row.addWidget(b1)
        b2 = primary_btn("标记爽约", "warn")
        b2.clicked.connect(self._do_no_show); row.addWidget(b2)
        row.addStretch()
        v.addLayout(row)

        v.addWidget(label("当日科室统计", "h2"))
        self.tbl_stat = QTableWidget()
        setup_table(self.tbl_stat,
                    ["科室ID", "科室", "预约数", "已就诊", "收入"])
        v.addWidget(self.tbl_stat)

        v.addWidget(label("医生工作量统计", "h2"))
        wbar = QHBoxLayout()
        wbar.addWidget(QLabel("筛选"))
        self.in_wl_kw = search_field("姓名/科室…")
        self.in_wl_kw.textChanged.connect(self._render_workload)
        wbar.addWidget(self.in_wl_kw, 1)
        wbar.addWidget(QLabel("排序"))
        self.cmb_wl_order = QComboBox()
        for txt, k in [("已就诊 ↓", ("visited_count", False)),
                       ("已预约 ↓", ("booked_count", False)),
                       ("排班数 ↓", ("schedule_count", False)),
                       ("姓名", ("doctor_name", True))]:
            self.cmb_wl_order.addItem(txt, k)
        self.cmb_wl_order.currentIndexChanged.connect(self._render_workload)
        wbar.addWidget(self.cmb_wl_order)
        b3 = primary_btn("刷新", "ghost"); b3.clicked.connect(self._load_workload)
        wbar.addWidget(b3)
        v.addLayout(wbar)

        self.tbl_workload = QTableWidget()
        setup_table(self.tbl_workload,
            ["医生ID", "姓名", "科室", "职称", "排班数", "已预约", "已就诊", "爽约"])
        v.addWidget(self.tbl_workload)

        v.addWidget(label("最忙医生", "h2"))
        self.lb_busy = QLabel()
        self.lb_busy.setStyleSheet("color:#C0392B; font-weight:600;")
        v.addWidget(self.lb_busy)

        self.tabs.addTab(w, "统计")
        self._load_workload()
        self._show_busy()

    def _do_stat(self):
        d = self.dt_stat.value()
        try:
            rows = AppointmentService.daily_statistics(str(d))
            self.tbl_stat.setSortingEnabled(False)
            self.tbl_stat.setRowCount(len(rows))
            for r, row in enumerate(rows):
                self.tbl_stat.setItem(r, 0, NumericItem(row["dept_id"]))
                self.tbl_stat.setItem(r, 1, QTableWidgetItem(row["dept_name"]))
                self.tbl_stat.setItem(r, 2, NumericItem(row["book_count"]))
                self.tbl_stat.setItem(r, 3, NumericItem(row["visit_count"]))
                self.tbl_stat.setItem(r, 4, NumericItem(float(row["income"]),
                                                        f"¥{row['income']}"))
            self.tbl_stat.setSortingEnabled(True)
            QMessageBox.information(self, "完成",
                f"已通过游标存储过程统计，共 {len(rows)} 个科室")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _do_no_show(self):
        d = self.dt_stat.value()
        if QMessageBox.question(self, "确认",
                f"将把 {d} 之前仍处于「已预约」的记录标记为「爽约」，确认？") != QMessageBox.Yes:
            return
        try:
            ret = AppointmentService.mark_no_show(str(d))
            QMessageBox.information(self, "完成", f"游标过程处理 {ret['affected']} 条记录")
            self._appt_load()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _load_workload(self):
        self._all_workload = DoctorDAO.workload_view()
        self._render_workload()

    def _render_workload(self):
        kw = self.in_wl_kw.text().strip().lower()
        order_key, asc = self.cmb_wl_order.currentData()
        rows = list(self._all_workload)
        if kw:
            rows = [r for r in rows
                    if kw in (r.get("doctor_name") or "").lower()
                    or kw in (r.get("dept_name") or "").lower()]
        rows.sort(key=lambda r: r.get(order_key) or 0, reverse=not asc)

        self.tbl_workload.setSortingEnabled(False)
        self.tbl_workload.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_workload.setItem(r, 0, NumericItem(row["doctor_id"]))
            self.tbl_workload.setItem(r, 1, QTableWidgetItem(row["doctor_name"]))
            self.tbl_workload.setItem(r, 2, QTableWidgetItem(row["dept_name"]))
            self.tbl_workload.setItem(r, 3, QTableWidgetItem(row["title"]))
            self.tbl_workload.setItem(r, 4, NumericItem(row.get("schedule_count") or 0))
            self.tbl_workload.setItem(r, 5, NumericItem(row.get("booked_count") or 0))
            self.tbl_workload.setItem(r, 6, NumericItem(row.get("visited_count") or 0))
            self.tbl_workload.setItem(r, 7, NumericItem(row.get("noshow_count") or 0))
        self.tbl_workload.setSortingEnabled(True)

    def _show_busy(self):
        rows = AppointmentDAO.busiest_doctor()
        if rows:
            txt = "  |  ".join([f"{r['name']}（{r['dept_name']}）{r['cnt']} 次"
                                 for r in rows])
            self.lb_busy.setText(txt)


# ============================================================
# 对话框
# ============================================================
class DeptDialog(QDialog):
    def __init__(self, parent, cur=None):
        super().__init__(parent)
        self.setWindowTitle("科室")
        self.setMinimumWidth(380)
        f = QFormLayout(self)
        f.setSpacing(8)
        self.in_name = QLineEdit(cur.get("dept_name") if cur else "")
        self.in_desc = QLineEdit(cur.get("description") if cur else "")
        self.in_loc  = QLineEdit(cur.get("location") if cur else "")
        f.addRow("名称", self.in_name)
        f.addRow("描述", self.in_desc)
        f.addRow("位置", self.in_loc)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        f.addWidget(b)

    def get_values(self):
        return (self.in_name.text().strip(),
                self.in_desc.text().strip(),
                self.in_loc.text().strip())


class DoctorDialog(QDialog):
    def __init__(self, parent, cur=None, with_account: bool = False):
        super().__init__(parent)
        self.setWindowTitle("新增医生（同时创建登录账号）" if with_account else "编辑医生")
        self.setMinimumWidth(440)
        self.with_account = with_account
        f = QFormLayout(self); f.setSpacing(8)

        self.cmb_dept = QComboBox()
        for d in DepartmentDAO.list_all():
            self.cmb_dept.addItem(d["dept_name"], d["dept_id"])

        self.in_name = QLineEdit()
        self.cmb_g = QComboBox(); self.cmb_g.addItems(["男", "女"])
        self.cmb_t = QComboBox(); self.cmb_t.addItems(TITLE_LIST)
        self.sp_fee = QDoubleSpinBox(); self.sp_fee.setRange(0, 9999); self.sp_fee.setValue(15)
        self.sp_fee.setPrefix("¥ ")
        self.in_intro = QTextEdit(); self.in_intro.setFixedHeight(60)
        self.cmb_s = QComboBox(); self.cmb_s.addItems(DOC_STATUS)

        if cur:
            idx = self.cmb_dept.findData(cur["dept_id"])
            self.cmb_dept.setCurrentIndex(idx if idx >= 0 else 0)
            self.in_name.setText(cur["name"])
            self.cmb_g.setCurrentText(cur["gender"])
            self.cmb_t.setCurrentText(cur["title"])
            self.sp_fee.setValue(float(cur["fee"]))
            self.in_intro.setPlainText(cur.get("intro") or "")
            self.cmb_s.setCurrentText(cur["status"])

        f.addRow("科室",   self.cmb_dept)
        f.addRow("姓名",   self.in_name)
        f.addRow("性别",   self.cmb_g)
        f.addRow("职称",   self.cmb_t)
        f.addRow("挂号费", self.sp_fee)
        f.addRow("简介",   self.in_intro)
        f.addRow("状态",   self.cmb_s)

        if with_account:
            sep = QFrame(); sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color:#E2E8F0;")
            f.addRow(sep)
            tip = QLabel("登录账号信息（医生用此账号登录）")
            tip.setStyleSheet("color:#4F8AC9; font-weight:600;")
            f.addRow(tip)
            self.in_user = QLineEdit(); self.in_user.setPlaceholderText("如 doc010")
            self.in_pwd  = QLineEdit(); self.in_pwd.setEchoMode(QLineEdit.Password)
            self.in_pwd.setPlaceholderText("≥6 位")
            self.in_pwd2 = QLineEdit(); self.in_pwd2.setEchoMode(QLineEdit.Password)
            self.in_pwd2.setPlaceholderText("再输入一次")
            f.addRow("登录用户名", self.in_user)
            f.addRow("登录密码",   self.in_pwd)
            f.addRow("确认密码",   self.in_pwd2)

        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self._ok); b.rejected.connect(self.reject)
        f.addWidget(b)

    def _ok(self):
        if not self.in_name.text().strip():
            QMessageBox.warning(self, "提示", "请输入姓名"); return
        if self.with_account:
            u = self.in_user.text().strip()
            p1 = self.in_pwd.text(); p2 = self.in_pwd2.text()
            if not is_valid_username(u):
                QMessageBox.warning(self, "提示", "用户名格式不正确"); return
            if AccountDAO.username_exists(u):
                QMessageBox.warning(self, "提示", "用户名已存在"); return
            if len(p1) < 6:
                QMessageBox.warning(self, "提示", "密码至少 6 位"); return
            if p1 != p2:
                QMessageBox.warning(self, "提示", "两次密码不一致"); return
        self.accept()

    def get_values(self):
        return (self.cmb_dept.currentData(),
                self.in_name.text().strip(),
                self.cmb_g.currentText(),
                self.cmb_t.currentText(),
                self.sp_fee.value(),
                self.in_intro.toPlainText().strip(),
                self.cmb_s.currentText())

    def get_account_values(self):
        return {"username": self.in_user.text().strip(),
                "password": self.in_pwd.text()}


class PatientDialog(QDialog):
    def __init__(self, parent, cur=None):
        super().__init__(parent)
        self.setWindowTitle("患者")
        self.setMinimumWidth(420)
        f = QFormLayout(self); f.setSpacing(8)
        self.in_name = QLineEdit()
        self.cmb_g = QComboBox(); self.cmb_g.addItems(["男", "女"])
        self.dt_birth = QDateEdit(QDate(1990, 1, 1)); self.dt_birth.setCalendarPopup(True)
        self.in_idc = QLineEdit()
        self.in_phone = QLineEdit()
        self.in_addr = QLineEdit()
        if cur:
            self.in_name.setText(cur["name"])
            self.cmb_g.setCurrentText(cur["gender"])
            if cur.get("birth_date"):
                self.dt_birth.setDate(QDate(cur["birth_date"].year,
                                            cur["birth_date"].month,
                                            cur["birth_date"].day))
            self.in_idc.setText(cur["id_card"])
            self.in_phone.setText(cur["phone"])
            self.in_addr.setText(cur.get("address") or "")
        f.addRow("姓名", self.in_name)
        f.addRow("性别", self.cmb_g)
        f.addRow("出生", self.dt_birth)
        f.addRow("身份证", self.in_idc)
        f.addRow("电话", self.in_phone)
        f.addRow("地址", self.in_addr)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self._ok); b.rejected.connect(self.reject)
        f.addWidget(b)

    def _ok(self):
        if not self.in_name.text().strip():
            QMessageBox.warning(self, "提示", "请输入姓名"); return
        if not is_valid_id_card(self.in_idc.text().strip()):
            QMessageBox.warning(self, "提示", "身份证号格式不正确"); return
        if not is_valid_phone(self.in_phone.text().strip()):
            QMessageBox.warning(self, "提示", "手机号格式不正确"); return
        self.accept()

    def get_values(self):
        return (self.in_name.text().strip(),
                self.cmb_g.currentText(),
                self.dt_birth.date().toPyDate(),
                self.in_idc.text().strip(),
                self.in_phone.text().strip(),
                self.in_addr.text().strip())


class ScheduleDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("新增排班")
        self.setMinimumWidth(360)
        f = QFormLayout(self); f.setSpacing(8)
        self.dt = QDateEdit(QDate.currentDate()); self.dt.setCalendarPopup(True)
        self.cmb_slot = QComboBox(); self.cmb_slot.addItems(["上午", "下午"])
        self.sp_quota = QSpinBox(); self.sp_quota.setRange(1, 100); self.sp_quota.setValue(20)
        f.addRow("日期", self.dt)
        f.addRow("时段", self.cmb_slot)
        f.addRow("总号源", self.sp_quota)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        f.addWidget(b)

    def get_values(self):
        return (self.dt.date().toPyDate(),
                self.cmb_slot.currentText(),
                self.sp_quota.value())
