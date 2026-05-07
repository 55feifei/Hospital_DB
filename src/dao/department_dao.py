"""科室 DAO。"""

from db import Database


class DepartmentDAO:

    @staticmethod
    def list_all():
        return Database.query("SELECT * FROM department ORDER BY dept_id")

    @staticmethod
    def get(dept_id: int):
        rows = Database.query("SELECT * FROM department WHERE dept_id=%s", (dept_id,))
        return rows[0] if rows else None

    @staticmethod
    def create(name: str, description: str, location: str) -> int:
        return Database.execute(
            "INSERT INTO department(dept_name, description, location) VALUES (%s,%s,%s)",
            (name, description, location),
        )

    @staticmethod
    def update(dept_id: int, name: str, description: str, location: str) -> int:
        return Database.execute(
            "UPDATE department SET dept_name=%s, description=%s, location=%s WHERE dept_id=%s",
            (name, description, location, dept_id),
        )

    @staticmethod
    def delete(dept_id: int) -> int:
        return Database.execute("DELETE FROM department WHERE dept_id=%s", (dept_id,))
