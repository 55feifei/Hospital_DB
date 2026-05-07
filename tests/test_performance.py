"""索引性能基准测试 — 评分点 一-3 / 作业第 5 条
对 3 个二级索引分别进行"删除索引 → 测时 → 重建索引 → 测时"的对比，并打印 EXPLAIN。

注意：本测试会临时修改 schema（drop / create index），运行前确保是开发数据库。
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import Database


def time_query(sql, args=None, repeat=50):
    """返回平均执行时间（毫秒）"""
    Database.query(sql, args)  # 预热
    t0 = time.perf_counter()
    for _ in range(repeat):
        Database.query(sql, args)
    return (time.perf_counter() - t0) * 1000 / repeat


def explain_one(sql):
    plan = Database.query("EXPLAIN " + sql)
    return plan[0]


class TestIndexPerformance(unittest.TestCase):
    """三个二级索引的 EXPLAIN + 执行时间对比"""

    @classmethod
    def setUpClass(cls):
        # 准备：把 appointment 膨胀到 ~3000 行，便于看到差距
        # 直接 INSERT 会触发 quota 校验，因此用 INSERT IGNORE + 预备一个超大 quota 的"虚拟排班"
        n = Database.query("SELECT COUNT(*) AS n FROM appointment")[0]["n"]
        if n < 3000:
            # 找一个排班，把 quota 提到很大，多次 book 后再恢复
            sid = Database.query(
                "SELECT schedule_id FROM schedule WHERE work_date >= CURDATE() LIMIT 1"
            )[0]["schedule_id"]
            Database.execute(
                "UPDATE schedule SET total_quota=10000, remaining_quota=10000 "
                "WHERE schedule_id=%s", (sid,)
            )
            # 直接 INSERT 30 个患者各 100 条 → 触发器会扣减 quota
            for _ in range(30):
                for pid in range(1, 31):
                    try:
                        Database.execute(
                            "INSERT INTO appointment(patient_id, schedule_id, appt_no, status) "
                            "SELECT %s, %s, IFNULL(MAX(appt_no),0)+1, '已预约' "
                            "FROM appointment WHERE schedule_id=%s",
                            (pid, sid, sid)
                        )
                    except Exception:
                        pass

    def test_perf_appt_patient_date(self):
        sql = ("SELECT * FROM appointment "
               "WHERE patient_id=1 AND create_time > '2026-01-01' "
               "ORDER BY create_time DESC LIMIT 50")

        with_plan = explain_one(sql)
        t_w = time_query(sql)

        # 为外键提供替代索引后再删主索引
        Database.execute(
            "ALTER TABLE appointment ADD INDEX idx_fk_patient_tmp(patient_id)"
        )
        Database.execute("ALTER TABLE appointment DROP INDEX idx_appt_patient_date")
        try:
            wo_plan = explain_one(sql)
            t_wo = time_query(sql)

            print(f"\n[idx_appt_patient_date]")
            print(f"  无索引: type={wo_plan.get('type')}, key={wo_plan.get('key')}, "
                  f"rows={wo_plan.get('rows')}, Extra={wo_plan.get('Extra')}")
            print(f"  有索引: type={with_plan.get('type')}, key={with_plan.get('key')}, "
                  f"rows={with_plan.get('rows')}, Extra={with_plan.get('Extra')}")
            print(f"  耗时   = 无索引 {t_wo:.3f} ms  /  有索引 {t_w:.3f} ms")

            self.assertIsNotNone(with_plan.get("key"), "应使用索引")
        finally:
            try:
                Database.execute(
                    "ALTER TABLE appointment ADD INDEX idx_appt_patient_date(patient_id, create_time)"
                )
            except Exception:
                pass
            try:
                Database.execute(
                    "ALTER TABLE appointment DROP INDEX idx_fk_patient_tmp"
                )
            except Exception:
                pass

    def test_perf_schedule_date_remain(self):
        sql = ("SELECT * FROM schedule "
               "WHERE work_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY) "
               "AND remaining_quota > 0")

        with_plan = explain_one(sql)
        t_w = time_query(sql)

        Database.execute("ALTER TABLE schedule DROP INDEX idx_schedule_date_remain")
        try:
            wo_plan = explain_one(sql)
            t_wo = time_query(sql)

            print(f"\n[idx_schedule_date_remain]")
            print(f"  无索引: type={wo_plan.get('type')}, key={wo_plan.get('key')}, "
                  f"rows={wo_plan.get('rows')}")
            print(f"  有索引: type={with_plan.get('type')}, key={with_plan.get('key')}, "
                  f"rows={with_plan.get('rows')}")
            print(f"  耗时   = 无索引 {t_wo:.3f} ms  /  有索引 {t_w:.3f} ms")
        finally:
            Database.execute(
                "ALTER TABLE schedule ADD INDEX idx_schedule_date_remain(work_date, remaining_quota)"
            )

    def test_perf_payment_status_time(self):
        sql = ("SELECT * FROM payment "
               "WHERE status='待支付' "
               "ORDER BY created_at DESC LIMIT 50")

        with_plan = explain_one(sql)
        t_w = time_query(sql)

        Database.execute("ALTER TABLE payment DROP INDEX idx_payment_status_time")
        try:
            wo_plan = explain_one(sql)
            t_wo = time_query(sql)

            print(f"\n[idx_payment_status_time]")
            print(f"  无索引: type={wo_plan.get('type')}, key={wo_plan.get('key')}, "
                  f"rows={wo_plan.get('rows')}")
            print(f"  有索引: type={with_plan.get('type')}, key={with_plan.get('key')}, "
                  f"rows={with_plan.get('rows')}")
            print(f"  耗时   = 无索引 {t_wo:.3f} ms  /  有索引 {t_w:.3f} ms")
        finally:
            Database.execute(
                "ALTER TABLE payment ADD INDEX idx_payment_status_time(status, created_at)"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
