-- =====================================================================
-- 医院门诊预约管理系统 — 视图
-- 文件：04_views.sql
-- =====================================================================
USE hospital_db;

-- ----------------------------------------------------------------
-- 视图 1：v_schedule_full —— 排班完整视图
--   用途：患者端选号时一次性看到 科室+医生+排班+剩余号源
-- ----------------------------------------------------------------
DROP VIEW IF EXISTS v_schedule_full;
CREATE VIEW v_schedule_full AS
SELECT
    s.schedule_id,
    s.work_date,
    s.time_slot,
    s.total_quota,
    s.remaining_quota,
    s.status        AS schedule_status,
    d.doctor_id,
    d.name          AS doctor_name,
    d.title,
    d.fee,
    dp.dept_id,
    dp.dept_name
FROM schedule s
JOIN doctor    d  ON d.doctor_id = s.doctor_id
JOIN department dp ON dp.dept_id  = d.dept_id;

-- ----------------------------------------------------------------
-- 视图 2：v_patient_appointments —— 患者预约历史视图
-- ----------------------------------------------------------------
DROP VIEW IF EXISTS v_patient_appointments;
CREATE VIEW v_patient_appointments AS
SELECT
    a.appt_id,
    a.patient_id,
    p.name           AS patient_name,
    a.status,
    a.appt_no,
    a.create_time,
    a.cancel_time,
    a.visit_time,
    s.work_date,
    s.time_slot,
    d.doctor_id,
    d.name           AS doctor_name,
    p.phone,
    dp.dept_id,
    dp.dept_name,
    d.fee,
    pay.status       AS pay_status,
    pay.amount
FROM appointment a
JOIN patient   p   ON p.patient_id  = a.patient_id
JOIN schedule  s   ON s.schedule_id = a.schedule_id
JOIN doctor    d   ON d.doctor_id   = s.doctor_id
JOIN department dp ON dp.dept_id    = d.dept_id
LEFT JOIN payment pay ON pay.appt_id = a.appt_id;

-- ----------------------------------------------------------------
-- 视图 3：v_doctor_workload —— 医生工作量统计视图
-- ----------------------------------------------------------------
DROP VIEW IF EXISTS v_doctor_workload;
CREATE VIEW v_doctor_workload AS
SELECT
    d.doctor_id,
    d.name          AS doctor_name,
    dp.dept_name,
    d.title,
    COUNT(DISTINCT s.schedule_id) AS schedule_count,
    SUM(CASE WHEN a.status='已预约' THEN 1 ELSE 0 END) AS booked_count,
    SUM(CASE WHEN a.status='已就诊' THEN 1 ELSE 0 END) AS visited_count,
    SUM(CASE WHEN a.status='已取消' THEN 1 ELSE 0 END) AS canceled_count,
    SUM(CASE WHEN a.status='爽约'   THEN 1 ELSE 0 END) AS noshow_count
FROM doctor d
JOIN department dp ON dp.dept_id = d.dept_id
LEFT JOIN schedule    s ON s.doctor_id = d.doctor_id
LEFT JOIN appointment a ON a.schedule_id = s.schedule_id
GROUP BY d.doctor_id, d.name, dp.dept_name, d.title;

SELECT '=== views.sql executed successfully ===' AS msg;
SHOW FULL TABLES WHERE Table_type = 'VIEW';
