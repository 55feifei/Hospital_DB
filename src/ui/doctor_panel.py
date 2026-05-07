"""医生面板：按日期/患者关键字/状态搜索预约 → 完成就诊 → 写病历。"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QDialog,
    QFormLayout, QTextEdit, QDialogButtonBox, QComboBox, QFrame
)
from PyQt5.QtCore import QDate, Qt

from dao.appointment_dao import AppointmentDAO
from dao.doctor_dao import DoctorDAO
from dao.record_dao import RecordDAO
from ui.widgets import (
    setup_table, search_field, primary_btn, label, NumericItem, make_status_item,
    DateFilter
)


class DoctorPanel(QWidget):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.doctor_id = user["ref_id"]
        self._build_ui()
        self._load_appts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        d = DoctorDAO.get(self.doctor_id)

        head = QHBoxLayout()
        head.addWidget(label("医生工作台", "h1"))
        info = QLabel(f"{d['name']}（{d['title']}）  |  {d['dept_name']}")
        info.setObjectName("tag")
        head.addWidget(info)
        head.addStretch()
        self.lb_workload = QLabel("当日有效预约：— 人")
        self.lb_workload.setStyleSheet("color:#4F8AC9; font-weight:600; padding:2px 8px;")
        head.addWidget(self.lb_workload)
        layout.addLayout(head)

        # ---- 搜索条 ----
        bar = QHBoxLayout()
        bar.addWidget(QLabel("日期"))
        self.dt = DateFilter(default="today", allow_all=True)
        bar.addWidget(self.dt)

        bar.addWidget(QLabel("关键字"))
        self.in_kw = search_field("患者姓名/电话…")
        self.in_kw.returnPressed.connect(self._load_appts)
        bar.addWidget(self.in_kw, 1)

        bar.addWidget(QLabel("状态"))
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("全部", "")
        for s in ["已预约", "已就诊", "已取消", "爽约"]:
            self.cmb_status.addItem(s, s)
        bar.addWidget(self.cmb_status)

        bar.addWidget(QLabel("排序"))
        self.cmb_order = QComboBox()
        for txt, k in [("序号 ↑", ("appt_no", True)),
                       ("序号 ↓", ("appt_no", False)),
                       ("患者姓名", ("patient_name", True)),
                       ("状态", ("status", True)),
                       ("创建时间 ↓", ("create_time", False))]:
            self.cmb_order.addItem(txt, k)
        bar.addWidget(self.cmb_order)

        b = primary_btn("查询")
        b.clicked.connect(self._load_appts)
        bar.addWidget(b)
        layout.addLayout(bar)

        self.tbl = QTableWidget()
        setup_table(
            self.tbl,
            ["预约ID", "序号", "患者", "性别", "电话", "日期", "时段", "状态"]
        )
        layout.addWidget(self.tbl)

        btns = QHBoxLayout()
        btn_visit = primary_btn("完成就诊（写病历）", "success")
        btn_visit.setMinimumHeight(36)
        btn_visit.clicked.connect(self._do_visit)
        btns.addWidget(btn_visit)

        btn_view = primary_btn("查看 / 编辑病历")
        btn_view.clicked.connect(self._view_record)
        btns.addWidget(btn_view)

        btn_refresh = primary_btn("刷新", "ghost")
        btn_refresh.clicked.connect(self._load_appts)
        btns.addWidget(btn_refresh)
        btns.addStretch()
        layout.addLayout(btns)

        # 联动刷新
        self.dt.changed.connect(self._load_appts)
        self.cmb_status.currentIndexChanged.connect(self._load_appts)
        self.cmb_order.currentIndexChanged.connect(self._load_appts)

    def _load_appts(self):
        d = self.dt.value()           # date 或 None（"全部"）
        order_key, asc = self.cmb_order.currentData()
        rows = AppointmentDAO.search_by_doctor(
            doctor_id=self.doctor_id,
            work_date=d,
            keyword=self.in_kw.text().strip(),
            status=self.cmb_status.currentData() or "",
            order_by=order_key, asc=asc,
        )
        self._use_date = True  # 一次性查询，恢复

        self.tbl.setSortingEnabled(False)
        self.tbl.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl.setItem(r, 0, NumericItem(row["appt_id"]))
            self.tbl.setItem(r, 1, NumericItem(row["appt_no"]))
            self.tbl.setItem(r, 2, QTableWidgetItem(row["patient_name"]))
            self.tbl.setItem(r, 3, QTableWidgetItem(row["patient_gender"]))
            self.tbl.setItem(r, 4, QTableWidgetItem(row["phone"]))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(row["work_date"])))
            self.tbl.setItem(r, 6, make_status_item(row["time_slot"]))
            self.tbl.setItem(r, 7, make_status_item(row["status"]))
        self.tbl.setSortingEnabled(True)

        # 调用函数 fn_get_doctor_workload
        if d:
            n = DoctorDAO.workload_of(self.doctor_id, d)
            self.lb_workload.setText(f"{d} 当日有效预约：{n} 人  |  本次列表 {len(rows)} 条")
        else:
            self.lb_workload.setText(f"本次列表 {len(rows)} 条")

    def _do_visit(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行预约")
            return
        appt_id = int(self.tbl.item(row, 0).text())
        status  = self.tbl.item(row, 7).text()
        if status != "已预约":
            QMessageBox.information(self, "提示", f"当前状态为「{status}」，无需操作")
            return

        dlg = RecordDialog(appt_id, self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                affected = AppointmentDAO.mark_visited(appt_id)
                if affected:
                    QMessageBox.information(self, "成功", "已完成就诊，病历已生成")
                    self._load_appts()
                else:
                    QMessageBox.warning(self, "失败", "未能更新预约状态")
            except Exception as e:
                QMessageBox.critical(self, "数据库错误", str(e))

    def _view_record(self):
        row = self.tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行预约")
            return
        appt_id = int(self.tbl.item(row, 0).text())
        dlg = RecordDialog(appt_id, self, edit_mode=True)
        dlg.exec_()


class RecordDialog(QDialog):
    """病历填写/查看对话框。"""

    def __init__(self, appt_id: int, parent=None, edit_mode: bool = False):
        super().__init__(parent)
        self.appt_id = appt_id
        self.edit_mode = edit_mode
        self.setWindowTitle("病历记录")
        self.resize(560, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        title = QLabel("病历记录")
        title.setStyleSheet("font-size:17px; font-weight:600; color:#1B2A41;")
        root.addWidget(title)
        sub = QLabel(f"预约 #{appt_id}")
        sub.setObjectName("tip")
        root.addWidget(sub)

        line = QFrame(); line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#E2E8F0;")
        root.addWidget(line)

        form = QFormLayout()
        form.setSpacing(8)

        self.in_chief = QTextEdit()
        self.in_diag  = QTextEdit()
        self.in_pres  = QTextEdit()
        self.in_adv   = QTextEdit()
        for w in (self.in_chief, self.in_diag, self.in_pres, self.in_adv):
            w.setFixedHeight(70)

        form.addRow("主诉", self.in_chief)
        form.addRow("诊断", self.in_diag)
        form.addRow("处方", self.in_pres)
        form.addRow("医嘱", self.in_adv)
        root.addLayout(form)

        # 加载已有病历
        rec = RecordDAO.get_by_appt(appt_id)
        self.record_id = rec["record_id"] if rec else None
        if rec:
            self.in_chief.setPlainText(rec.get("chief_complaint") or "")
            self.in_diag.setPlainText(rec.get("diagnosis") or "")
            self.in_pres.setPlainText(rec.get("prescription") or "")
            self.in_adv.setPlainText(rec.get("advice") or "")

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _save(self):
        chief = self.in_chief.toPlainText().strip()
        diag  = self.in_diag.toPlainText().strip()
        pres  = self.in_pres.toPlainText().strip()
        adv   = self.in_adv.toPlainText().strip()

        try:
            if self.record_id:
                RecordDAO.update(self.record_id, chief, diag, pres, adv)
            else:
                RecordDAO.insert_if_not_exists(self.appt_id, chief, diag, pres, adv)
                rec = RecordDAO.get_by_appt(self.appt_id)
                if rec:
                    RecordDAO.update(rec["record_id"], chief, diag, pres, adv)
            QMessageBox.information(self, "成功", "病历已保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))
