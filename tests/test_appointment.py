"""核心业务路径单元测试（DAO + Service 层）。"""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import Database
from dao.account_dao import AccountDAO
from dao.department_dao import DepartmentDAO
from dao.doctor_dao import DoctorDAO
from dao.patient_dao import PatientDAO
from dao.schedule_dao import ScheduleDAO
from dao.appointment_dao import AppointmentDAO
from service.appointment_service import AppointmentService


class TestAccount(unittest.TestCase):
    def test_login_admin(self):
        u = AccountDAO.authenticate("admin", "123456")
        self.assertIsNotNone(u)
        self.assertEqual(u["role"], "admin")

    def test_login_doctor(self):
        u = AccountDAO.authenticate("doc001", "123456")
        self.assertIsNotNone(u)
        self.assertEqual(u["role"], "doctor")

    def test_login_patient(self):
        u = AccountDAO.authenticate("pat001", "123456")
        self.assertIsNotNone(u)
        self.assertEqual(u["role"], "patient")

    def test_login_wrong_password(self):
        u = AccountDAO.authenticate("admin", "wrong")
        self.assertIsNone(u)

    def test_login_inactive_user(self):
        # 临时禁用账号 → 登录失败 → 恢复
        Database.execute(
            "UPDATE user_account SET is_active=0 WHERE username='pat030'"
        )
        try:
            self.assertIsNone(AccountDAO.authenticate("pat030", "123456"))
        finally:
            Database.execute(
                "UPDATE user_account SET is_active=1 WHERE username='pat030'"
            )


class TestCRUD(unittest.TestCase):
    """基本 CRUD 与约束测试 — 评分点 一-1"""

    def test_dept_list(self):
        rows = DepartmentDAO.list_all()
        self.assertGreaterEqual(len(rows), 5, "≥ 5 张表 + 数据")

    def test_doctor_filter_by_dept(self):
        rows = DoctorDAO.list_by_dept(1)
        self.assertTrue(rows)
        self.assertTrue(all(r["dept_id"] == 1 for r in rows))

    def test_patient_search(self):
        rows = PatientDAO.search_by_keyword("陈")
        self.assertTrue(rows)
        self.assertTrue(any("陈" in r["name"] for r in rows))

    def test_unique_id_card(self):
        """UNIQUE 约束生效 — 重用种子数据中已存在的身份证号"""
        existing = Database.query("SELECT id_card FROM patient LIMIT 1")[0]["id_card"]
        with self.assertRaises(Exception):
            PatientDAO.create("测试", "男", "1990-01-01",
                              existing, "13900000099", "")

    def test_unique_phone(self):
        existing = Database.query("SELECT phone FROM patient LIMIT 1")[0]["phone"]
        with self.assertRaises(Exception):
            PatientDAO.create("测试", "男", "1990-01-01",
                              "110101199003129999", existing, "")

    def test_check_constraint_fee_negative(self):
        """CHECK 约束：fee >= 0"""
        with self.assertRaises(Exception):
            DoctorDAO.create(1, "测试医生", "男", "主治医师", -10.0, "", "在职")


class TestFunction(unittest.TestCase):
    """带参函数测试 — 评分点 一-2"""

    def test_fn_get_doctor_workload(self):
        n = DoctorDAO.workload_of(1, date.today())
        self.assertIsInstance(n, int)
        self.assertGreaterEqual(n, 0)


class TestProcedureBook(unittest.TestCase):
    """带参存储过程：sp_book_appointment / sp_cancel_appointment — 评分点 一-2"""

    def test_book_and_cancel_full_cycle(self):
        # 找一个剩余号源 > 0 的排班
        rows = Database.query(
            "SELECT s.schedule_id, s.remaining_quota FROM schedule s "
            "WHERE s.remaining_quota > 0 AND s.status='正常' "
            "AND NOT EXISTS ("
            "   SELECT 1 FROM appointment a "
            "   WHERE a.schedule_id=s.schedule_id AND a.patient_id=15 AND a.status IN ('已预约','已就诊')"
            ") LIMIT 1"
        )
        self.assertTrue(rows, "需要至少 1 个 patient 15 未预约的可用排班")
        sid = rows[0]["schedule_id"]
        before = rows[0]["remaining_quota"]

        # 1) 预约
        ret = AppointmentService.book(patient_id=15, schedule_id=sid)
        self.assertIsNotNone(ret["appt_id"], f"预约应成功: {ret}")
        self.assertIn("成功", ret["msg"])
        appt_id = ret["appt_id"]

        # 2) 触发器自动减号源
        after = Database.query(
            "SELECT remaining_quota FROM schedule WHERE schedule_id=%s", (sid,)
        )[0]["remaining_quota"]
        self.assertEqual(after, before - 1, "触发器 trg_appt_after_insert 应令 remaining-1")

        # 3) 触发器自动建支付单
        pay = Database.query(
            "SELECT * FROM payment WHERE appt_id=%s", (appt_id,)
        )
        self.assertTrue(pay, "触发器应自动创建缴费单")
        self.assertEqual(pay[0]["status"], "待支付")

        # 4) 取消
        ret2 = AppointmentService.cancel(appt_id)
        self.assertIn("成功", ret2["msg"])

        # 5) 触发器恢复号源
        restored = Database.query(
            "SELECT remaining_quota FROM schedule WHERE schedule_id=%s", (sid,)
        )[0]["remaining_quota"]
        self.assertEqual(restored, before, "取消后号源应恢复")

        # 6) 触发器把支付单改为已退款
        pay2 = Database.query(
            "SELECT * FROM payment WHERE appt_id=%s", (appt_id,)
        )
        self.assertEqual(pay2[0]["status"], "已退款")

    def test_book_duplicate_rejected(self):
        """同一患者重复预约被拒"""
        # 先建一个新预约
        rows = Database.query(
            "SELECT s.schedule_id FROM schedule s "
            "WHERE s.remaining_quota > 0 AND s.status='正常' "
            "AND NOT EXISTS ("
            "   SELECT 1 FROM appointment a "
            "   WHERE a.schedule_id=s.schedule_id AND a.patient_id=20 AND a.status IN ('已预约','已就诊')"
            ") LIMIT 1"
        )
        if not rows:
            self.skipTest("无可用排班")
        sid = rows[0]["schedule_id"]
        ret1 = AppointmentService.book(20, sid)
        self.assertIsNotNone(ret1["appt_id"])
        # 再次预约同一排班
        ret2 = AppointmentService.book(20, sid)
        self.assertIsNone(ret2["appt_id"])
        self.assertIn("重复", ret2["msg"])
        # 清理
        AppointmentService.cancel(ret1["appt_id"])

    def test_cancel_visited_rejected(self):
        """已就诊预约不能取消（状态机校验）"""
        rows = Database.query(
            "SELECT appt_id FROM appointment WHERE status='已就诊' LIMIT 1"
        )
        if not rows:
            self.skipTest("无已就诊预约")
        ret = AppointmentService.cancel(rows[0]["appt_id"])
        self.assertNotIn("成功", ret["msg"])


class TestProcedureCursor(unittest.TestCase):
    """游标存储过程 — 评分点 一-2 / 作业第 4 条"""

    def test_daily_statistics(self):
        rows = AppointmentService.daily_statistics(str(date.today()))
        self.assertIsInstance(rows, list)
        # 字段齐全
        if rows:
            self.assertIn("dept_id", rows[0])
            self.assertIn("book_count", rows[0])
            self.assertIn("income", rows[0])

    def test_mark_no_show(self):
        # 找一条过去日期的"已预约"作为测试样本
        Database.execute(
            "INSERT INTO patient(name,gender,birth_date,id_card,phone,address) "
            "VALUES ('测试爽约', '男', '1990-01-01', '110101199001019999', '13900099001', '北京')"
        )
        pid = Database.query("SELECT patient_id FROM patient WHERE id_card='110101199001019999'")[0]["patient_id"]

        # 找一个过去日期排班（init data 准备了 -2 / -1 天）
        sched = Database.query(
            "SELECT schedule_id FROM schedule WHERE work_date < CURDATE() AND remaining_quota>0 LIMIT 1"
        )
        if sched:
            sid = sched[0]["schedule_id"]
            ret = AppointmentService.book(pid, sid)
            if ret["appt_id"]:
                # 调用爽约过程
                stat = AppointmentService.mark_no_show(str(date.today()))
                self.assertGreaterEqual(stat["affected"], 1)
                # 验证状态
                row = Database.query(
                    "SELECT status FROM appointment WHERE appt_id=%s", (ret["appt_id"],)
                )[0]
                self.assertEqual(row["status"], "爽约")
        # 清理测试患者：先删除其预约（如有）再删除患者
        Database.execute("DELETE FROM payment WHERE appt_id IN (SELECT appt_id FROM appointment WHERE patient_id=%s)", (pid,))
        Database.execute("DELETE FROM appointment WHERE patient_id=%s", (pid,))
        Database.execute("DELETE FROM patient WHERE patient_id=%s", (pid,))


class TestTriggers(unittest.TestCase):
    """触发器存在性与功能验证 — 评分点 一-2"""

    def test_triggers_exist(self):
        rows = Database.query("SHOW TRIGGERS")
        names = {r["Trigger"] for r in rows}
        for required in ["trg_appt_quota_check", "trg_appt_after_insert",
                         "trg_appt_after_update", "trg_doctor_before_delete"]:
            self.assertIn(required, names, f"缺少触发器 {required}")

    def test_doctor_delete_blocked(self):
        """trg_doctor_before_delete：医生有未完成预约时不能删除"""
        # 找一个有"已预约"的医生
        rows = Database.query(
            "SELECT DISTINCT s.doctor_id FROM schedule s "
            "JOIN appointment a ON a.schedule_id=s.schedule_id "
            "WHERE a.status='已预约' LIMIT 1"
        )
        if not rows:
            self.skipTest("无未完成预约")
        with self.assertRaises(Exception) as ctx:
            DoctorDAO.delete(rows[0]["doctor_id"])
        self.assertIn("未完成预约", str(ctx.exception))

    def test_quota_overbook_blocked(self):
        """trg_appt_quota_check：剩余 0 时禁止预约"""
        # 临时把某排班 remaining 设为 0
        Database.execute("UPDATE schedule SET remaining_quota=0 WHERE schedule_id=270")
        ret = AppointmentService.book(10, 270)
        self.assertIsNone(ret["appt_id"])
        self.assertIn("号源", ret["msg"])
        # 还原
        Database.execute(
            "UPDATE schedule SET remaining_quota = total_quota - "
            "(SELECT COUNT(*) FROM appointment WHERE schedule_id=270 AND status IN ('已预约','已就诊')) "
            "WHERE schedule_id=270"
        )


class TestViewsAndComplexQuery(unittest.TestCase):
    """视图 + 复杂查询（多表连接、子查询） — 评分点 一-2"""

    def test_view_schedule_full(self):
        rows = Database.query(
            "SELECT * FROM v_schedule_full WHERE remaining_quota>0 LIMIT 5"
        )
        self.assertTrue(rows)
        self.assertIn("dept_name", rows[0])
        self.assertIn("doctor_name", rows[0])

    def test_view_doctor_workload(self):
        rows = Database.query("SELECT * FROM v_doctor_workload")
        self.assertEqual(len(rows), 15)

    def test_view_patient_appointments(self):
        rows = Database.query(
            "SELECT * FROM v_patient_appointments WHERE patient_id=1 LIMIT 5"
        )
        self.assertIsInstance(rows, list)

    def test_subquery_busiest_doctor(self):
        """子查询找最忙医生"""
        rows = AppointmentDAO.busiest_doctor()
        self.assertTrue(rows)
        self.assertIn("cnt", rows[0])

    def test_multitable_join(self):
        """多表连接"""
        rows = Database.query(
            """
            SELECT a.appt_id, p.name, d.name AS doc, dp.dept_name, s.work_date
            FROM appointment a
            JOIN patient    p  ON p.patient_id  = a.patient_id
            JOIN schedule   s  ON s.schedule_id = a.schedule_id
            JOIN doctor     d  ON d.doctor_id   = s.doctor_id
            JOIN department dp ON dp.dept_id    = d.dept_id
            LIMIT 5
            """
        )
        self.assertTrue(rows)
        for k in ("name", "doc", "dept_name"):
            self.assertIn(k, rows[0])


class TestIndexes(unittest.TestCase):
    """索引存在性与 EXPLAIN 性能 — 评分点 一-3 / 作业第 5 条"""

    def test_indexes_exist(self):
        idx_appt = Database.query("SHOW INDEX FROM appointment")
        names = {r["Key_name"] for r in idx_appt}
        self.assertIn("idx_appt_patient_date", names)

        idx_sched = Database.query("SHOW INDEX FROM schedule")
        names = {r["Key_name"] for r in idx_sched}
        self.assertIn("idx_schedule_date_remain", names)

        idx_pay = Database.query("SHOW INDEX FROM payment")
        names = {r["Key_name"] for r in idx_pay}
        self.assertIn("idx_payment_status_time", names)

    def test_explain_uses_index(self):
        rows = Database.query(
            "EXPLAIN SELECT * FROM appointment "
            "WHERE patient_id=1 AND create_time > '2026-01-01'"
        )
        # 期望使用了 idx_appt_patient_date 索引
        keys = [r.get("key") for r in rows]
        self.assertTrue(any(k and "idx_appt_patient_date" in k for k in keys),
                        f"期望使用 idx_appt_patient_date，实际 keys = {keys}")


class TestSchemaIntegrity(unittest.TestCase):
    """表/触发器/过程/视图 元数据完整性"""

    def test_table_count(self):
        rows = Database.query(
            "SELECT COUNT(*) AS n FROM information_schema.tables "
            "WHERE table_schema='hospital_db' AND table_type='BASE TABLE'"
        )
        self.assertEqual(rows[0]["n"], 8, "应有 8 张基表")

    def test_procedure_count(self):
        rows = Database.query(
            "SELECT COUNT(*) AS n FROM information_schema.routines "
            "WHERE routine_schema='hospital_db' AND routine_type='PROCEDURE'"
        )
        self.assertGreaterEqual(rows[0]["n"], 4)

    def test_function_count(self):
        rows = Database.query(
            "SELECT COUNT(*) AS n FROM information_schema.routines "
            "WHERE routine_schema='hospital_db' AND routine_type='FUNCTION'"
        )
        self.assertGreaterEqual(rows[0]["n"], 1)

    def test_view_count(self):
        rows = Database.query(
            "SELECT COUNT(*) AS n FROM information_schema.views "
            "WHERE table_schema='hospital_db'"
        )
        self.assertGreaterEqual(rows[0]["n"], 3)


class TestForeignKey(unittest.TestCase):
    """外键级联拒绝（参照完整性）"""

    def test_fk_reject_orphan_doctor(self):
        with self.assertRaises(Exception):
            DoctorDAO.create(99999, "测试", "男", "主治医师", 15, "", "在职")

    def test_fk_reject_delete_dept_with_doctor(self):
        with self.assertRaises(Exception):
            DepartmentDAO.delete(1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
