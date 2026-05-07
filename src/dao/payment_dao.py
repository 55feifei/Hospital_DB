"""缴费 DAO。"""

from db import Database


class PaymentDAO:

    @staticmethod
    def get_by_appt(appt_id: int):
        rows = Database.query(
            "SELECT * FROM payment WHERE appt_id=%s ORDER BY payment_id DESC",
            (appt_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def pay(payment_id: int, pay_method: str) -> int:
        return Database.execute(
            "UPDATE payment SET status='已支付', pay_method=%s, pay_time=NOW() "
            "WHERE payment_id=%s AND status='待支付'",
            (pay_method, payment_id),
        )

    @staticmethod
    def list_pending():
        return Database.query(
            """
            SELECT p.*, a.patient_id, pt.name AS patient_name, d.name AS doctor_name
            FROM payment p
            JOIN appointment a ON a.appt_id    = p.appt_id
            JOIN patient    pt ON pt.patient_id= a.patient_id
            JOIN schedule    s ON s.schedule_id= a.schedule_id
            JOIN doctor      d ON d.doctor_id  = s.doctor_id
            WHERE p.status='待支付'
            ORDER BY p.created_at DESC
            """
        )
