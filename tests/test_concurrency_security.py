"""并发与安全测试 — 评分点 一-2 / 一-3。

1. 并发预约：双线程同抢最后 1 个号源 → 仅 1 个成功
2. 安全：应用账号 hospital_app 无 DDL 权限
3. 安全：参数化查询防 SQL 注入
"""

import os
import sys
import threading
import unittest

import pymysql

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import Database
from config import DB_CONFIG, DB_CONFIG_APP
from dao.account_dao import AccountDAO


class TestConcurrentBooking(unittest.TestCase):

    def test_two_threads_compete_last_quota(self):
        """两个线程同时抢最后一个号源 — 仅一个成功"""
        # 准备：把某排班 quota 设为 1
        sid = Database.query(
            "SELECT schedule_id FROM schedule "
            "WHERE work_date >= CURDATE() AND status='正常' LIMIT 1"
        )[0]["schedule_id"]
        # 先清掉该排班所有"已预约"以便重置
        Database.execute(
            "UPDATE appointment SET status='已取消', cancel_time=NOW() "
            "WHERE schedule_id=%s AND status='已预约'", (sid,)
        )
        Database.execute(
            "UPDATE schedule SET total_quota=1, remaining_quota=1 WHERE schedule_id=%s",
            (sid,)
        )

        results = []
        def book(pid):
            conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
            try:
                cur = conn.cursor()
                cur.callproc("sp_book_appointment", (pid, sid, 0, ""))
                cur.execute(
                    "SELECT @_sp_book_appointment_2 AS appt_id, @_sp_book_appointment_3 AS msg"
                )
                row = cur.fetchone()
                conn.commit()
                results.append((pid, row["appt_id"], row["msg"]))
            finally:
                conn.close()

        t1 = threading.Thread(target=book, args=(25,))
        t2 = threading.Thread(target=book, args=(26,))
        t1.start(); t2.start()
        t1.join();  t2.join()

        # 期望：仅一个 appt_id 非 None
        success = [r for r in results if r[1] is not None]
        failed  = [r for r in results if r[1] is None]
        self.assertEqual(len(success), 1, f"应仅 1 个成功，实际 = {results}")
        self.assertEqual(len(failed), 1)
        self.assertIn("号源", failed[0][2])

        # 还原
        Database.execute(
            "UPDATE schedule SET total_quota=20 WHERE schedule_id=%s", (sid,)
        )


class TestSecurity(unittest.TestCase):

    def test_app_account_no_ddl(self):
        """hospital_app 账号无 CREATE TABLE 权限"""
        try:
            conn = pymysql.connect(**DB_CONFIG_APP)
        except Exception as e:
            self.skipTest(f"应用账号未创建：{e}")
            return
        try:
            cur = conn.cursor()
            with self.assertRaises(Exception) as ctx:
                cur.execute("CREATE TABLE _test_ddl_x(id INT)")
            self.assertIn("denied", str(ctx.exception).lower())
        finally:
            conn.close()

    def test_app_account_no_drop_database(self):
        try:
            conn = pymysql.connect(**DB_CONFIG_APP)
        except Exception as e:
            self.skipTest(f"应用账号未创建：{e}")
            return
        try:
            cur = conn.cursor()
            with self.assertRaises(Exception):
                cur.execute("DROP DATABASE hospital_db")
        finally:
            conn.close()

    def test_sql_injection_safe(self):
        """参数化查询防注入"""
        # 用注入 payload 作为用户名
        u = AccountDAO.authenticate("admin' OR '1'='1", "anything")
        self.assertIsNone(u, "参数化查询应阻止注入")

    def test_password_hashed(self):
        """密码以哈希存储，不含明文"""
        rows = Database.query("SELECT password_hash FROM user_account WHERE username='admin'")
        self.assertTrue(rows)
        self.assertEqual(len(rows[0]["password_hash"]), 64, "应为 SHA-256 64 位 hex")
        self.assertNotIn("123456", rows[0]["password_hash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
