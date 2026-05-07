"""预约业务编排：调用存储过程实现完整事务。

注意：PyMySQL.callproc 把所有参数（IN+OUT）都映射到 @_proc_n 形式的会话变量，
       因此 Database.call_proc 返回的 out 数组按"IN 在前 OUT 在后"的原始顺序排列。
"""

from db import Database


class AppointmentService:

    @staticmethod
    def book(patient_id: int, schedule_id: int):
        """sp_book_appointment(IN patient_id, IN schedule_id, OUT appt_id, OUT msg)"""
        out, _ = Database.call_proc(
            "sp_book_appointment", (patient_id, schedule_id, 0, "")
        )
        # out = [patient_id, schedule_id, appt_id, msg]
        return {"appt_id": out[2], "msg": out[3]}

    @staticmethod
    def cancel(appt_id: int):
        """sp_cancel_appointment(IN appt_id, OUT msg)"""
        out, _ = Database.call_proc("sp_cancel_appointment", (appt_id, ""))
        # out = [appt_id, msg]
        return {"msg": out[1]}

    @staticmethod
    def daily_statistics(date_str: str):
        """sp_daily_statistics(IN p_date) — 仅有 IN 参数，结果通过结果集返回。"""
        _, result_sets = Database.call_proc("sp_daily_statistics", (date_str,))
        return result_sets[0] if result_sets else []

    @staticmethod
    def mark_no_show(before_date: str):
        """sp_mark_no_show(IN before_date, OUT affected)"""
        out, _ = Database.call_proc("sp_mark_no_show", (before_date, 0))
        # out = [before_date, affected]
        return {"affected": out[1]}
