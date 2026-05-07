"""病历 DAO。"""

from db import Database


class RecordDAO:

    @staticmethod
    def get_by_appt(appt_id: int):
        rows = Database.query(
            "SELECT * FROM medical_record WHERE appt_id=%s", (appt_id,)
        )
        return rows[0] if rows else None

    @staticmethod
    def list_by_patient(patient_id: int):
        return Database.query(
            """
            SELECT mr.*, a.patient_id, d.name AS doctor_name, dp.dept_name
            FROM medical_record mr
            JOIN appointment a   ON a.appt_id     = mr.appt_id
            JOIN schedule    s   ON s.schedule_id = a.schedule_id
            JOIN doctor      d   ON d.doctor_id   = s.doctor_id
            JOIN department  dp  ON dp.dept_id    = d.dept_id
            WHERE a.patient_id=%s
            ORDER BY mr.visit_time DESC
            """,
            (patient_id,),
        )

    @staticmethod
    def update(record_id, chief, diagnosis, prescription, advice) -> int:
        return Database.execute(
            "UPDATE medical_record SET chief_complaint=%s, diagnosis=%s, "
            "prescription=%s, advice=%s WHERE record_id=%s",
            (chief, diagnosis, prescription, advice, record_id),
        )

    @staticmethod
    def insert_if_not_exists(appt_id, chief, diagnosis, prescription, advice) -> int:
        return Database.execute(
            "INSERT IGNORE INTO medical_record(appt_id, chief_complaint, diagnosis, "
            "prescription, advice) VALUES (%s,%s,%s,%s,%s)",
            (appt_id, chief, diagnosis, prescription, advice),
        )
