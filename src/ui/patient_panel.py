"""患者面板：浏览科室 → 选医生排班 → 预约 / 取消 / 缴费 / 查看病历。

新增：
- 排班搜索（科室 / 医生关键字 / 职称 / 时段 / 日期范围 / 排序方式）
- 预约历史按状态/关键字搜索 + 可排序
- 病历搜索（按医生/科室/诊断关键字）
"""

from datetime import date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QTabWidget, QTextEdit, QFrame
)
from PyQt5.QtCore import QDate, Qt

from dao.department_dao import DepartmentDAO
from dao.schedule_dao import ScheduleDAO
from dao.appointment_dao import AppointmentDAO
from dao.payment_dao import PaymentDAO
from dao.record_dao import RecordDAO
from service.appointment_service import AppointmentService
from ui.widgets import (
    setup_table, fill_table, search_field, primary_btn, label,
    NumericItem, make_status_item, DateRangeFilter
)


class PatientPanel(QWidget):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.patient_id = user["ref_id"]
        self._build_ui()
        self._load_depts()
        self._load_my_appts()
        self._load_my_records()

    # --------------- UI 构建 ---------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.addWidget(label(f"患者工作台", "h1"))
        tag = QLabel(self.user['username'])
        tag.setObjectName("tag")
        head.addWidget(tag)
        head.addStretch()
        layout.addLayout(head)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._tab_book()
        self._tab_my_appts()
        self._tab_my_records()

    # ============= Tab 1: 预约挂号 =============
    def _tab_book(self):
        tab = QWidget(); v = QVBoxLayout(tab); v.setSpacing(10)

        # ---- 搜索条 ----
        bar = QGridLayout()
        bar.setHorizontalSpacing(8); bar.setVerticalSpacing(6)

        bar.addWidget(QLabel("科室"), 0, 0)
        self.cmb_dept = QComboBox()
        self.cmb_dept.currentIndexChanged.connect(self._load_schedules)
        bar.addWidget(self.cmb_dept, 0, 1)

        bar.addWidget(QLabel("医生关键字"), 0, 2)
        self.in_doc_kw = search_field("姓名/简介…")
        self.in_doc_kw.returnPressed.connect(self._load_schedules)
        bar.addWidget(self.in_doc_kw, 0, 3)

        bar.addWidget(QLabel("职称"), 0, 4)
        self.cmb_title = QComboBox()
        self.cmb_title.addItem("全部", "")
        for t in ["住院医师", "主治医师", "副主任医师", "主任医师"]:
            self.cmb_title.addItem(t, t)
        bar.addWidget(self.cmb_title, 0, 5)

        bar.addWidget(QLabel("时段"), 1, 0)
        self.cmb_slot = QComboBox()
        self.cmb_slot.addItem("全部", ""); self.cmb_slot.addItem("上午", "上午"); self.cmb_slot.addItem("下午", "下午")
        bar.addWidget(self.cmb_slot, 1, 1)

        bar.addWidget(QLabel("日期"), 1, 2)
        self.dt_range = DateRangeFilter(default="month")
        self.dt_range.changed.connect(self._load_schedules)
        bar.addWidget(self.dt_range, 1, 3)

        bar.addWidget(QLabel("排序"), 1, 4)
        self.cmb_order = QComboBox()
        for label_text, key in [
            ("日期 ↑", ("work_date", True)),
            ("日期 ↓", ("work_date", False)),
            ("挂号费 ↑", ("fee", True)),
            ("挂号费 ↓", ("fee", False)),
            ("剩余号源 ↓", ("remaining", False)),
            ("医生姓名", ("doctor_name", True)),
            ("职称", ("title", True)),
        ]:
            self.cmb_order.addItem(label_text, key)
        bar.addWidget(self.cmb_order, 1, 5)

        btn_row = QHBoxLayout()
        btn_search = primary_btn("查询")
        btn_search.clicked.connect(self._load_schedules)
        btn_reset = primary_btn("重置", "ghost")
        btn_reset.clicked.connect(self._reset_schedule_filter)
        btn_row.addStretch(); btn_row.addWidget(btn_reset); btn_row.addWidget(btn_search)
        bar.addLayout(btn_row, 0, 6, 2, 1)

        v.addLayout(bar)

        self.tbl_schedule = QTableWidget()
        setup_table(
            self.tbl_schedule,
            ["排班ID", "日期", "时段", "科室", "医生", "职称", "挂号费", "剩余/总号源"]
        )
        v.addWidget(self.tbl_schedule)

        bottom = QHBoxLayout()
        self.lb_count = QLabel("共 0 条")
        self.lb_count.setObjectName("tip")
        bottom.addWidget(self.lb_count)
        bottom.addStretch()
        btn_book = primary_btn("预约选中排班", "success")
        btn_book.setMinimumHeight(36)
        btn_book.clicked.connect(self._do_book)
        bottom.addWidget(btn_book)
        v.addLayout(bottom)

        self.tabs.addTab(tab, "预约挂号")

    def _reset_schedule_filter(self):
        self.in_doc_kw.clear()
        self.cmb_title.setCurrentIndex(0)
        self.cmb_slot.setCurrentIndex(0)
        self.dt_range.cmb.setCurrentIndex(2)   # 重置为"本月"
        self.cmb_order.setCurrentIndex(0)
        self._load_schedules()

    # ============= Tab 2: 我的预约 =============
    def _tab_my_appts(self):
        tab = QWidget(); v = QVBoxLayout(tab); v.setSpacing(10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("关键字"))
        self.in_appt_kw = search_field("医生/科室…")
        self.in_appt_kw.returnPressed.connect(self._load_my_appts)
        bar.addWidget(self.in_appt_kw, 1)

        bar.addWidget(QLabel("状态"))
        self.cmb_appt_status = QComboBox()
        self.cmb_appt_status.addItem("全部", "")
        for s in ["已预约", "已就诊", "已取消", "爽约"]:
            self.cmb_appt_status.addItem(s, s)
        bar.addWidget(self.cmb_appt_status)

        bar.addWidget(QLabel("排序"))
        self.cmb_appt_order = QComboBox()
        for txt, k in [("创建时间 ↓", ("create_time", False)),
                       ("创建时间 ↑", ("create_time", True)),
                       ("就诊日期 ↓", ("work_date", False)),
                       ("就诊日期 ↑", ("work_date", True)),
                       ("状态", ("status", True))]:
            self.cmb_appt_order.addItem(txt, k)
        bar.addWidget(self.cmb_appt_order)

        b = primary_btn("查询")
        b.clicked.connect(self._load_my_appts)
        bar.addWidget(b)
        v.addLayout(bar)

        self.tbl_appt = QTableWidget()
        setup_table(
            self.tbl_appt,
            ["预约ID", "日期", "时段", "科室", "医生", "序号", "状态", "缴费", "金额"]
        )
        v.addWidget(self.tbl_appt)

        btn_row = QHBoxLayout()
        btn_cancel = primary_btn("取消选中预约", "danger")
        btn_cancel.clicked.connect(self._do_cancel)
        btn_pay = primary_btn("缴费", "warn")
        btn_pay.clicked.connect(self._do_pay)
        btn_refresh = primary_btn("刷新", "ghost")
        btn_refresh.clicked.connect(self._load_my_appts)
        btn_row.addWidget(btn_cancel); btn_row.addWidget(btn_pay)
        btn_row.addStretch(); btn_row.addWidget(btn_refresh)
        v.addLayout(btn_row)
        self.tabs.addTab(tab, "我的预约")

    # ============= Tab 3: 就诊记录 =============
    def _tab_my_records(self):
        tab = QWidget(); v = QVBoxLayout(tab); v.setSpacing(10)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("关键字"))
        self.in_rec_kw = search_field("医生/科室/诊断…")
        self.in_rec_kw.textChanged.connect(self._render_records)
        bar.addWidget(self.in_rec_kw, 1)

        bar.addWidget(QLabel("排序"))
        self.cmb_rec_order = QComboBox()
        self.cmb_rec_order.addItem("就诊时间 ↓", ("visit_time", False))
        self.cmb_rec_order.addItem("就诊时间 ↑", ("visit_time", True))
        self.cmb_rec_order.addItem("科室", ("dept_name", True))
        self.cmb_rec_order.currentIndexChanged.connect(self._render_records)
        bar.addWidget(self.cmb_rec_order)
        b = primary_btn("刷新", "ghost")
        b.clicked.connect(self._load_my_records)
        bar.addWidget(b)
        v.addLayout(bar)

        self.tbl_record = QTableWidget()
        setup_table(
            self.tbl_record,
            ["病历ID", "就诊时间", "科室", "医生", "主诉", "诊断", "处方"]
        )
        v.addWidget(self.tbl_record)
        self.tabs.addTab(tab, "就诊记录")

    # --------------- 数据加载 ---------------
    def _load_depts(self):
        self.cmb_dept.blockSignals(True)
        self.cmb_dept.clear()
        self.cmb_dept.addItem("全部科室", None)
        for d in DepartmentDAO.list_all():
            self.cmb_dept.addItem(d["dept_name"], d["dept_id"])
        self.cmb_dept.setCurrentIndex(1 if self.cmb_dept.count() > 1 else 0)
        self.cmb_dept.blockSignals(False)
        self._load_schedules()

    def _load_schedules(self):
        order_key, asc = self.cmb_order.currentData()
        rows = ScheduleDAO.search_for_patient(
            dept_id=self.cmb_dept.currentData(),
            doctor_keyword=self.in_doc_kw.text().strip(),
            title=self.cmb_title.currentData() or "",
            start_date=self.dt_range.start_date(),
            end_date=self.dt_range.end_date(),
            time_slot=self.cmb_slot.currentData() or "",
            only_available=True,
            order_by=order_key, asc=asc,
        )
        self.tbl_schedule.setSortingEnabled(False)
        self.tbl_schedule.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_schedule.setItem(r, 0, NumericItem(row["schedule_id"]))
            self.tbl_schedule.setItem(r, 1, QTableWidgetItem(str(row["work_date"])))
            self.tbl_schedule.setItem(r, 2, make_status_item(row["time_slot"]))
            self.tbl_schedule.setItem(r, 3, QTableWidgetItem(row.get("dept_name", "")))
            self.tbl_schedule.setItem(r, 4, QTableWidgetItem(row["doctor_name"]))
            self.tbl_schedule.setItem(r, 5, QTableWidgetItem(row["title"]))
            self.tbl_schedule.setItem(r, 6, NumericItem(row["fee"], f'¥{row["fee"]}'))
            self.tbl_schedule.setItem(
                r, 7,
                NumericItem(row["remaining_quota"],
                            f'{row["remaining_quota"]}/{row["total_quota"]}')
            )
        self.tbl_schedule.setSortingEnabled(True)
        self.lb_count.setText(f"共 {len(rows)} 条排班")

    def _load_my_appts(self):
        order_key, asc = self.cmb_appt_order.currentData()
        rows = AppointmentDAO.search_by_patient(
            patient_id=self.patient_id,
            keyword=self.in_appt_kw.text().strip(),
            status=self.cmb_appt_status.currentData() or "",
            order_by=order_key, asc=asc,
        )
        self.tbl_appt.setSortingEnabled(False)
        self.tbl_appt.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_appt.setItem(r, 0, NumericItem(row["appt_id"]))
            self.tbl_appt.setItem(r, 1, QTableWidgetItem(str(row["work_date"])))
            self.tbl_appt.setItem(r, 2, make_status_item(row["time_slot"]))
            self.tbl_appt.setItem(r, 3, QTableWidgetItem(row["dept_name"]))
            self.tbl_appt.setItem(r, 4, QTableWidgetItem(row["doctor_name"]))
            self.tbl_appt.setItem(r, 5, NumericItem(row["appt_no"]))
            self.tbl_appt.setItem(r, 6, make_status_item(row["status"]))
            self.tbl_appt.setItem(r, 7, make_status_item(row.get("pay_status") or "-"))
            amt = row.get("amount")
            self.tbl_appt.setItem(r, 8, NumericItem(amt or 0, f"¥{amt}" if amt else "-"))
        self.tbl_appt.setSortingEnabled(True)

    def _load_my_records(self):
        self._all_records = RecordDAO.list_by_patient(self.patient_id)
        self._render_records()

    def _render_records(self):
        kw = self.in_rec_kw.text().strip().lower()
        order_key, asc = self.cmb_rec_order.currentData()
        rows = list(self._all_records)
        if kw:
            def hit(r):
                return any(kw in str(r.get(k) or "").lower()
                           for k in ("doctor_name", "dept_name", "diagnosis",
                                     "chief_complaint", "prescription"))
            rows = [r for r in rows if hit(r)]
        rows.sort(key=lambda r: r.get(order_key) or "", reverse=not asc)

        self.tbl_record.setSortingEnabled(False)
        self.tbl_record.setRowCount(len(rows))
        for r, row in enumerate(rows):
            cells = [row["record_id"], str(row["visit_time"]), row["dept_name"],
                     row["doctor_name"], row.get("chief_complaint") or "",
                     row.get("diagnosis") or "", row.get("prescription") or ""]
            for c, val in enumerate(cells):
                item = NumericItem(val) if c == 0 else QTableWidgetItem(str(val))
                self.tbl_record.setItem(r, c, item)
        self.tbl_record.setSortingEnabled(True)

    # --------------- 操作 ---------------
    def _do_book(self):
        row = self.tbl_schedule.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行排班")
            return
        sid = int(self.tbl_schedule.item(row, 0).text())
        try:
            ret = AppointmentService.book(self.patient_id, sid)
            if ret["appt_id"]:
                QMessageBox.information(self, "成功", ret["msg"])
                self._load_schedules()
                self._load_my_appts()
            else:
                QMessageBox.warning(self, "预约未完成", ret["msg"])
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))

    def _do_cancel(self):
        row = self.tbl_appt.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行预约")
            return
        appt_id = int(self.tbl_appt.item(row, 0).text())
        ans = QMessageBox.question(self, "确认", "确定取消该预约吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans != QMessageBox.Yes:
            return
        try:
            ret = AppointmentService.cancel(appt_id)
            QMessageBox.information(self, "操作结果", ret["msg"])
            self._load_my_appts()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _do_pay(self):
        row = self.tbl_appt.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行预约")
            return
        # 拦截：已取消 / 爽约 / 已就诊 不允许缴费
        appt_status = self.tbl_appt.item(row, 6).text()
        if appt_status in ("已取消", "爽约"):
            QMessageBox.warning(self, "无法缴费",
                f"该预约状态为「{appt_status}」，不允许缴费。")
            return
        appt_id = int(self.tbl_appt.item(row, 0).text())
        pay = PaymentDAO.get_by_appt(appt_id)
        if not pay:
            QMessageBox.warning(self, "提示", "未找到缴费单")
            return
        if pay["status"] != "待支付":
            QMessageBox.information(self, "提示", f"缴费状态为：{pay['status']}")
            return
        affected = PaymentDAO.pay(pay["payment_id"], "微信")
        if affected:
            QMessageBox.information(self, "成功", "缴费成功")
            self._load_my_appts()
        else:
            QMessageBox.warning(self, "失败", "缴费失败")
