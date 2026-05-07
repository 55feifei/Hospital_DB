"""患者 DAO。"""

from db import Database


class PatientDAO:

    @staticmethod
    def list_all():
        return Database.query("SELECT * FROM patient ORDER BY patient_id")

    @staticmethod
    def get(patient_id: int):
        rows = Database.query("SELECT * FROM patient WHERE patient_id=%s", (patient_id,))
        return rows[0] if rows else None

    @staticmethod
    def find_by_idcard(id_card: str):
        rows = Database.query("SELECT * FROM patient WHERE id_card=%s", (id_card,))
        return rows[0] if rows else None

    @staticmethod
    def create(name, gender, birth_date, id_card, phone, address) -> int:
        return Database.execute(
            "INSERT INTO patient(name, gender, birth_date, id_card, phone, address) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (name, gender, birth_date, id_card, phone, address),
        )

    @staticmethod
    def update(patient_id, name, gender, birth_date, id_card, phone, address) -> int:
        return Database.execute(
            "UPDATE patient SET name=%s, gender=%s, birth_date=%s, "
            "id_card=%s, phone=%s, address=%s WHERE patient_id=%s",
            (name, gender, birth_date, id_card, phone, address, patient_id),
        )

    @staticmethod
    def delete(patient_id: int) -> int:
        return Database.execute("DELETE FROM patient WHERE patient_id=%s", (patient_id,))

    @staticmethod
    def search_by_keyword(keyword: str):
        like = f"%{keyword}%"
        return Database.query(
            "SELECT * FROM patient "
            "WHERE name LIKE %s OR phone LIKE %s OR id_card LIKE %s "
            "ORDER BY patient_id",
            (like, like, like),
        )

    @staticmethod
    def search(keyword: str = "", gender: str = "",
               order_by: str = "patient_id", asc: bool = True):
        """复杂查询：JOIN 预约表统计 appointment_count。"""
        allowed = {
            "patient_id":  "p.patient_id",
            "name":        "p.name",
            "birth_date":  "p.birth_date",
            "appt_count":  "appt_count",
            "created_at":  "p.created_at",
        }
        col = allowed.get(order_by, "p.patient_id")
        direction = "ASC" if asc else "DESC"
        sql = """
            SELECT p.*,
                   (SELECT COUNT(*) FROM appointment a
                    WHERE a.patient_id=p.patient_id) AS appt_count
            FROM patient p
            WHERE 1=1
        """
        args = []
        if keyword:
            sql += (" AND (p.name LIKE %s OR p.phone LIKE %s OR p.id_card LIKE %s "
                    "      OR p.address LIKE %s)")
            like = f"%{keyword}%"
            args += [like, like, like, like]
        if gender:
            sql += " AND p.gender=%s"
            args.append(gender)
        sql += f" ORDER BY {col} {direction}"
        return Database.query(sql, tuple(args))
