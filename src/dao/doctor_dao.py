"""医生 DAO。"""

from db import Database


class DoctorDAO:

    @staticmethod
    def list_all():
        return Database.query(
            "SELECT d.*, dp.dept_name "
            "FROM doctor d JOIN department dp ON dp.dept_id=d.dept_id "
            "ORDER BY d.doctor_id"
        )

    @staticmethod
    def search(keyword: str = "", dept_id=None, status: str = "", title: str = "",
               order_by: str = "doctor_id", asc: bool = True):
        """复杂查询：科室连接 + 子查询统计预约数。

        order_by ∈ {doctor_id, name, dept_name, fee, appt_count}
        """
        allowed_order = {
            "doctor_id":  "d.doctor_id",
            "name":       "d.name",
            "dept_name":  "dp.dept_name",
            "fee":        "d.fee",
            "appt_count": "appt_count",
            "title":      "d.title",
        }
        col = allowed_order.get(order_by, "d.doctor_id")
        direction = "ASC" if asc else "DESC"

        sql = """
            SELECT d.*, dp.dept_name,
                   (SELECT COUNT(*) FROM appointment a
                    JOIN schedule s ON s.schedule_id=a.schedule_id
                    WHERE s.doctor_id=d.doctor_id
                      AND a.status IN ('已预约','已就诊')) AS appt_count
            FROM doctor d
            JOIN department dp ON dp.dept_id=d.dept_id
            WHERE 1=1
        """
        args = []
        if keyword:
            sql += " AND (d.name LIKE %s OR dp.dept_name LIKE %s OR d.intro LIKE %s)"
            like = f"%{keyword}%"
            args += [like, like, like]
        if dept_id:
            sql += " AND d.dept_id=%s"
            args.append(dept_id)
        if status:
            sql += " AND d.status=%s"
            args.append(status)
        if title:
            sql += " AND d.title=%s"
            args.append(title)
        sql += f" ORDER BY {col} {direction}"
        return Database.query(sql, tuple(args))

    @staticmethod
    def list_by_dept(dept_id: int):
        return Database.query(
            "SELECT d.*, dp.dept_name "
            "FROM doctor d JOIN department dp ON dp.dept_id=d.dept_id "
            "WHERE d.dept_id=%s AND d.status='在职' "
            "ORDER BY d.doctor_id",
            (dept_id,),
        )

    @staticmethod
    def get(doctor_id: int):
        rows = Database.query(
            "SELECT d.*, dp.dept_name "
            "FROM doctor d JOIN department dp ON dp.dept_id=d.dept_id "
            "WHERE d.doctor_id=%s",
            (doctor_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def create(dept_id, name, gender, title, fee, intro, status="在职") -> int:
        return Database.execute(
            "INSERT INTO doctor(dept_id, name, gender, title, fee, intro, status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (dept_id, name, gender, title, fee, intro, status),
        )

    @staticmethod
    def update(doctor_id, dept_id, name, gender, title, fee, intro, status) -> int:
        return Database.execute(
            "UPDATE doctor SET dept_id=%s, name=%s, gender=%s, title=%s, fee=%s, "
            "intro=%s, status=%s WHERE doctor_id=%s",
            (dept_id, name, gender, title, fee, intro, status, doctor_id),
        )

    @staticmethod
    def delete(doctor_id: int) -> int:
        return Database.execute("DELETE FROM doctor WHERE doctor_id=%s", (doctor_id,))

    @staticmethod
    def workload_view():
        """利用 v_doctor_workload 视图统计医生工作量。"""
        return Database.query(
            "SELECT * FROM v_doctor_workload ORDER BY visited_count DESC"
        )

    @staticmethod
    def workload_of(doctor_id: int, work_date):
        """调用函数 fn_get_doctor_workload。"""
        rows = Database.query(
            "SELECT fn_get_doctor_workload(%s, %s) AS cnt",
            (doctor_id, work_date),
        )
        return rows[0]["cnt"] if rows else 0
