"""账号表 DAO —— 处理登录、密码、账号 CRUD。"""

from db import Database
from utils import sha256


class AccountDAO:

    @staticmethod
    def authenticate(username: str, password: str):
        """登录校验，成功返回账号字典，否则返回 None。"""
        rows = Database.query(
            "SELECT * FROM user_account WHERE username=%s AND is_active=1",
            (username,),
        )
        if not rows:
            return None
        user = rows[0]
        if user["password_hash"] != sha256(password):
            return None
        Database.execute(
            "UPDATE user_account SET last_login=NOW() WHERE user_id=%s",
            (user["user_id"],),
        )
        return user

    @staticmethod
    def create(username: str, password: str, role: str, ref_id) -> int:
        return Database.execute(
            "INSERT INTO user_account(username, password_hash, role, ref_id) "
            "VALUES (%s, %s, %s, %s)",
            (username, sha256(password), role, ref_id),
        )

    @staticmethod
    def change_password(user_id: int, new_password: str) -> int:
        return Database.execute(
            "UPDATE user_account SET password_hash=%s WHERE user_id=%s",
            (sha256(new_password), user_id),
        )

    @staticmethod
    def list_all():
        return Database.query(
            "SELECT user_id, username, role, ref_id, is_active, created_at, last_login "
            "FROM user_account ORDER BY user_id"
        )

    @staticmethod
    def set_active(user_id: int, active: bool) -> int:
        return Database.execute(
            "UPDATE user_account SET is_active=%s WHERE user_id=%s",
            (1 if active else 0, user_id),
        )

    @staticmethod
    def username_exists(username: str) -> bool:
        return bool(Database.query(
            "SELECT 1 FROM user_account WHERE username=%s", (username,)
        ))

    @staticmethod
    def get_by_doctor(doctor_id: int):
        rows = Database.query(
            "SELECT * FROM user_account WHERE role='doctor' AND ref_id=%s",
            (doctor_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def list_with_owner():
        """复杂查询（多表 LEFT JOIN）：显示账号 + 关联的医生/患者姓名。"""
        return Database.query(
            """
            SELECT u.user_id, u.username, u.role, u.ref_id, u.is_active,
                   u.created_at, u.last_login,
                   COALESCE(d.name, p.name, '') AS owner_name,
                   COALESCE(dp.dept_name, '')   AS owner_dept
            FROM user_account u
            LEFT JOIN doctor     d  ON u.role='doctor'  AND d.doctor_id  = u.ref_id
            LEFT JOIN department dp ON dp.dept_id = d.dept_id
            LEFT JOIN patient    p  ON u.role='patient' AND p.patient_id = u.ref_id
            ORDER BY u.user_id
            """
        )
