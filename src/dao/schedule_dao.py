"""排班 DAO。"""

from db import Database


class ScheduleDAO:

    @staticmethod
    def list_by_doctor(doctor_id: int, start_date=None, end_date=None):
        sql = ("SELECT * FROM schedule WHERE doctor_id=%s ")
        args = [doctor_id]
        if start_date:
            sql += "AND work_date>=%s "
            args.append(start_date)
        if end_date:
            sql += "AND work_date<=%s "
            args.append(end_date)
        sql += "ORDER BY work_date, time_slot"
        return Database.query(sql, tuple(args))

    @staticmethod
    def list_by_dept_date(dept_id: int, work_date):
        return Database.query(
            "SELECT * FROM v_schedule_full "
            "WHERE dept_id=%s AND work_date=%s "
            "ORDER BY doctor_id, time_slot",
            (dept_id, work_date),
        )

    @staticmethod
    def get(schedule_id: int):
        rows = Database.query(
            "SELECT * FROM v_schedule_full WHERE schedule_id=%s",
            (schedule_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def create(doctor_id, work_date, time_slot, total_quota) -> int:
        return Database.execute(
            "INSERT INTO schedule(doctor_id, work_date, time_slot, total_quota, remaining_quota) "
            "VALUES (%s,%s,%s,%s,%s)",
            (doctor_id, work_date, time_slot, total_quota, total_quota),
        )

    @staticmethod
    def set_status(schedule_id: int, status: str) -> int:
        return Database.execute(
            "UPDATE schedule SET status=%s WHERE schedule_id=%s",
            (status, schedule_id),
        )

    @staticmethod
    def delete(schedule_id: int) -> int:
        return Database.execute("DELETE FROM schedule WHERE schedule_id=%s", (schedule_id,))

    @staticmethod
    def list_available(dept_id: int, start_date=None):
        """供患者端选号：仅显示有剩余号源、未停诊的排班。"""
        sql = ("SELECT * FROM v_schedule_full "
               "WHERE dept_id=%s AND remaining_quota>0 AND schedule_status='正常' ")
        args = [dept_id]
        if start_date:
            sql += "AND work_date>=%s "
            args.append(start_date)
        sql += "ORDER BY work_date, time_slot, doctor_id"
        return Database.query(sql, tuple(args))

    @staticmethod
    def search_for_patient(dept_id=None, doctor_keyword: str = "",
                          title: str = "", start_date=None, end_date=None,
                          time_slot: str = "", only_available: bool = True,
                          order_by: str = "work_date", asc: bool = True):
        """患者预约页的复杂搜索 — 支持科室/医生/职称/时段/日期范围。

        基于 v_schedule_full 视图（已 JOIN doctor + department）。
        """
        allowed = {
            "work_date":      "work_date",
            "fee":            "fee",
            "remaining":      "remaining_quota",
            "doctor_name":    "doctor_name",
            "title":          "title",
        }
        col = allowed.get(order_by, "work_date")
        direction = "ASC" if asc else "DESC"

        sql = "SELECT * FROM v_schedule_full WHERE schedule_status='正常'"
        args = []
        if only_available:
            sql += " AND remaining_quota > 0"
        if dept_id:
            sql += " AND dept_id=%s"; args.append(dept_id)
        if doctor_keyword:
            sql += " AND doctor_name LIKE %s"; args.append(f"%{doctor_keyword}%")
        if title:
            sql += " AND title=%s"; args.append(title)
        if start_date:
            sql += " AND work_date>=%s"; args.append(start_date)
        if end_date:
            sql += " AND work_date<=%s"; args.append(end_date)
        if time_slot:
            sql += " AND time_slot=%s"; args.append(time_slot)
        sql += f" ORDER BY {col} {direction}, time_slot ASC"
        return Database.query(sql, tuple(args))

    @staticmethod
    def search_admin(doctor_id=None, dept_id=None, status: str = "",
                     start_date=None, end_date=None,
                     order_by: str = "work_date", asc: bool = True):
        """管理员排班搜索（多表 JOIN）。"""
        allowed = {
            "schedule_id": "s.schedule_id",
            "work_date":   "s.work_date",
            "remaining":   "s.remaining_quota",
            "doctor_name": "d.name",
            "dept_name":   "dp.dept_name",
        }
        col = allowed.get(order_by, "s.work_date")
        direction = "ASC" if asc else "DESC"
        sql = """
            SELECT s.*, d.name AS doctor_name, dp.dept_name, dp.dept_id
            FROM schedule s
            JOIN doctor     d  ON d.doctor_id=s.doctor_id
            JOIN department dp ON dp.dept_id =d.dept_id
            WHERE 1=1
        """
        args = []
        if doctor_id:
            sql += " AND s.doctor_id=%s"; args.append(doctor_id)
        if dept_id:
            sql += " AND d.dept_id=%s"; args.append(dept_id)
        if status:
            sql += " AND s.status=%s"; args.append(status)
        if start_date:
            sql += " AND s.work_date>=%s"; args.append(start_date)
        if end_date:
            sql += " AND s.work_date<=%s"; args.append(end_date)
        sql += f" ORDER BY {col} {direction}"
        return Database.query(sql, tuple(args))
