"""预约 DAO。"""

from db import Database


class AppointmentDAO:

    @staticmethod
    def list_by_patient(patient_id: int):
        return Database.query(
            "SELECT * FROM v_patient_appointments "
            "WHERE patient_id=%s ORDER BY create_time DESC",
            (patient_id,),
        )

    @staticmethod
    def list_by_doctor_date(doctor_id: int, work_date):
        return Database.query(
            """
            SELECT a.*, p.name AS patient_name, p.gender AS patient_gender,
                   p.phone, s.work_date, s.time_slot
            FROM appointment a
            JOIN patient   p ON p.patient_id  = a.patient_id
            JOIN schedule  s ON s.schedule_id = a.schedule_id
            WHERE s.doctor_id=%s AND s.work_date=%s
            ORDER BY a.appt_no
            """,
            (doctor_id, work_date),
        )

    @staticmethod
    def list_all():
        return Database.query(
            "SELECT * FROM v_patient_appointments ORDER BY create_time DESC LIMIT 500"
        )

    @staticmethod
    def get(appt_id: int):
        rows = Database.query(
            "SELECT * FROM v_patient_appointments WHERE appt_id=%s",
            (appt_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def mark_visited(appt_id: int) -> int:
        """标记为已就诊（触发器自动建病历）。"""
        return Database.execute(
            "UPDATE appointment SET status='已就诊', visit_time=NOW() "
            "WHERE appt_id=%s AND status='已预约'",
            (appt_id,),
        )

    @staticmethod
    def search(keyword: str = "", status: str = "", dept_id=None,
               start_date=None, end_date=None,
               order_by: str = "create_time", asc: bool = False):
        """管理员预约搜索（基于 v_patient_appointments 视图，已含多表 JOIN）。"""
        allowed = {
            "appt_id":     "appt_id",
            "create_time": "create_time",
            "work_date":   "work_date",
            "patient_name": "patient_name",
            "doctor_name":  "doctor_name",
            "dept_name":    "dept_name",
            "status":       "status",
        }
        col = allowed.get(order_by, "create_time")
        direction = "ASC" if asc else "DESC"
        sql = "SELECT * FROM v_patient_appointments WHERE 1=1"
        args = []
        if keyword:
            sql += (" AND (patient_name LIKE %s OR doctor_name LIKE %s "
                    "OR dept_name LIKE %s OR phone LIKE %s)")
            like = f"%{keyword}%"
            args += [like, like, like, like]
        if status:
            sql += " AND status=%s"; args.append(status)
        if dept_id:
            sql += " AND dept_id=%s"; args.append(dept_id)
        if start_date:
            sql += " AND work_date>=%s"; args.append(start_date)
        if end_date:
            sql += " AND work_date<=%s"; args.append(end_date)
        sql += f" ORDER BY {col} {direction} LIMIT 1000"
        return Database.query(sql, tuple(args))

    @staticmethod
    def search_by_patient(patient_id: int, keyword: str = "", status: str = "",
                          order_by: str = "create_time", asc: bool = False):
        allowed = {
            "create_time": "create_time",
            "work_date":   "work_date",
            "doctor_name": "doctor_name",
            "dept_name":   "dept_name",
            "status":      "status",
        }
        col = allowed.get(order_by, "create_time")
        direction = "ASC" if asc else "DESC"
        sql = "SELECT * FROM v_patient_appointments WHERE patient_id=%s"
        args = [patient_id]
        if keyword:
            sql += " AND (doctor_name LIKE %s OR dept_name LIKE %s)"
            like = f"%{keyword}%"
            args += [like, like]
        if status:
            sql += " AND status=%s"; args.append(status)
        sql += f" ORDER BY {col} {direction}"
        return Database.query(sql, tuple(args))

    @staticmethod
    def search_by_doctor(doctor_id: int, work_date=None, keyword: str = "",
                         status: str = "",
                         order_by: str = "appt_no", asc: bool = True):
        """医生看自己预约的搜索：工作日期 + 患者姓名/电话关键字 + 状态。"""
        allowed = {
            "appt_no":     "a.appt_no",
            "create_time": "a.create_time",
            "patient_name": "p.name",
            "status":      "a.status",
        }
        col = allowed.get(order_by, "a.appt_no")
        direction = "ASC" if asc else "DESC"
        sql = """
            SELECT a.*, p.name AS patient_name, p.gender AS patient_gender,
                   p.phone, s.work_date, s.time_slot
            FROM appointment a
            JOIN patient   p ON p.patient_id  = a.patient_id
            JOIN schedule  s ON s.schedule_id = a.schedule_id
            WHERE s.doctor_id=%s
        """
        args = [doctor_id]
        if work_date:
            sql += " AND s.work_date=%s"; args.append(work_date)
        if keyword:
            sql += " AND (p.name LIKE %s OR p.phone LIKE %s)"
            like = f"%{keyword}%"
            args += [like, like]
        if status:
            sql += " AND a.status=%s"; args.append(status)
        sql += f" ORDER BY {col} {direction}"
        return Database.query(sql, tuple(args))

    @staticmethod
    def busiest_doctor():
        """子查询示例：找出预约数最多的医生。"""
        return Database.query(
            """
            SELECT d.doctor_id, d.name, dp.dept_name, COUNT(*) AS cnt
            FROM appointment a
            JOIN schedule s   ON s.schedule_id=a.schedule_id
            JOIN doctor   d   ON d.doctor_id  =s.doctor_id
            JOIN department dp ON dp.dept_id  =d.dept_id
            WHERE a.status IN ('已预约','已就诊')
            GROUP BY d.doctor_id, d.name, dp.dept_name
            HAVING COUNT(*) = (
                SELECT MAX(c) FROM (
                    SELECT COUNT(*) c
                    FROM appointment a2
                    JOIN schedule s2 ON s2.schedule_id=a2.schedule_id
                    WHERE a2.status IN ('已预约','已就诊')
                    GROUP BY s2.doctor_id
                ) t
            )
            """
        )
