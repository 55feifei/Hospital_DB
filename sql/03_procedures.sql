-- =====================================================================
-- 医院门诊预约管理系统 — 存储过程与函数
-- 文件：03_procedures.sql
-- 作业要求覆盖：
--   ≥ 2 带参存储过程/函数 → 本文件 3 个
--   ≥ 2 游标存储过程       → 本文件 2 个
-- =====================================================================
USE hospital_db;

-- ----------------------------------------------------------------
-- 1. 带参存储过程 sp_book_appointment
--    功能：预约挂号事务（行锁防超约）
--    参数：IN  患者 ID、排班 ID
--          OUT 预约 ID、错误信息
-- ----------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_appointment;
DELIMITER $$
CREATE PROCEDURE sp_book_appointment(
    IN  p_patient_id  INT,
    IN  p_schedule_id INT,
    OUT p_appt_id     INT,
    OUT p_msg         VARCHAR(200)
)
BEGIN
    DECLARE v_remaining INT;
    DECLARE v_status    VARCHAR(10);
    DECLARE v_next_no   INT;
    DECLARE v_dup       INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_appt_id = NULL;
        SET p_msg     = '预约失败：发生数据库异常';
    END;

    START TRANSACTION;

    -- 行锁锁定排班（防止并发超约）
    SELECT remaining_quota, status
        INTO v_remaining, v_status
        FROM schedule
        WHERE schedule_id = p_schedule_id
        FOR UPDATE;

    IF v_status = '停诊' THEN
        ROLLBACK;
        SET p_appt_id = NULL;
        SET p_msg     = '该排班已停诊';
    ELSEIF v_remaining <= 0 THEN
        ROLLBACK;
        SET p_appt_id = NULL;
        SET p_msg     = '号源已满';
    ELSE
        -- 防止同一患者同一排班重复预约
        SELECT COUNT(*)
            INTO v_dup
            FROM appointment
            WHERE schedule_id = p_schedule_id
              AND patient_id  = p_patient_id
              AND status IN ('已预约','已就诊');

        IF v_dup > 0 THEN
            ROLLBACK;
            SET p_appt_id = NULL;
            SET p_msg     = '您已预约过该排班，请勿重复预约';
        ELSE
            -- 计算下一个排队序号（仅基于"有效"预约：已预约 / 已就诊；
            -- 已取消 / 爽约 的序号已释放为 NULL）
            SELECT IFNULL(MAX(appt_no), 0) + 1
                INTO v_next_no
                FROM appointment
                WHERE schedule_id = p_schedule_id
                  AND status IN ('已预约','已就诊');

            INSERT INTO appointment(patient_id, schedule_id, appt_no, status)
                VALUES (p_patient_id, p_schedule_id, v_next_no, '已预约');

            SET p_appt_id = LAST_INSERT_ID();
            SET p_msg     = CONCAT('预约成功，排队序号 ', v_next_no);
            COMMIT;
        END IF;
    END IF;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 2. 带参存储过程 sp_cancel_appointment
--    功能：取消预约（仅"已预约"可取消，会触发号源恢复触发器）
-- ----------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cancel_appointment;
DELIMITER $$
CREATE PROCEDURE sp_cancel_appointment(
    IN  p_appt_id INT,
    OUT p_msg     VARCHAR(200)
)
BEGIN
    DECLARE v_status VARCHAR(10);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_msg = '取消失败：数据库异常';
    END;

    START TRANSACTION;

    SELECT status INTO v_status
        FROM appointment
        WHERE appt_id = p_appt_id
        FOR UPDATE;

    IF v_status IS NULL THEN
        ROLLBACK;
        SET p_msg = '预约不存在';
    ELSEIF v_status <> '已预约' THEN
        ROLLBACK;
        SET p_msg = CONCAT('当前状态为"', v_status, '"，无法取消');
    ELSE
        UPDATE appointment
            SET status = '已取消',
                cancel_time = NOW(),
                appt_no = NULL          -- 释放排队序号，供后续预约复用
            WHERE appt_id = p_appt_id;

        -- 已支付：自动退款；待支付：保持原状态（无款可退）
        UPDATE payment
            SET status = '已退款',
                pay_time = IFNULL(pay_time, NOW())
            WHERE appt_id = p_appt_id AND status = '已支付';

        SET p_msg = '取消成功';
        COMMIT;
    END IF;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 3. 带参函数 fn_get_doctor_workload
--    功能：返回某医生在某日的"已预约+已就诊"人数
-- ----------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_get_doctor_workload;
DELIMITER $$
CREATE FUNCTION fn_get_doctor_workload(
    p_doctor_id INT,
    p_date      DATE
) RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_count INT DEFAULT 0;

    SELECT COUNT(*) INTO v_count
        FROM appointment a
        JOIN schedule s ON s.schedule_id = a.schedule_id
        WHERE s.doctor_id = p_doctor_id
          AND s.work_date = p_date
          AND a.status IN ('已预约','已就诊');

    RETURN v_count;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 4. 游标存储过程 sp_daily_statistics
--    功能：用游标遍历当日全部预约，按科室聚合人数与金额
--    输出：临时结果集（科室名 / 预约数 / 已就诊数 / 收入）
-- ----------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_daily_statistics;
DELIMITER $$
CREATE PROCEDURE sp_daily_statistics(
    IN p_date DATE
)
BEGIN
    -- 游标遍历变量
    DECLARE v_done       INT DEFAULT 0;
    DECLARE v_dept_id    INT;
    DECLARE v_dept_name  VARCHAR(50);
    DECLARE v_book_cnt   INT;
    DECLARE v_visit_cnt  INT;
    DECLARE v_income     DECIMAL(12,2);

    -- 游标：取出当日有预约的科室列表
    DECLARE cur_dept CURSOR FOR
        SELECT DISTINCT d.dept_id, dp.dept_name
            FROM appointment a
            JOIN schedule  s  ON s.schedule_id = a.schedule_id
            JOIN doctor    d  ON d.doctor_id   = s.doctor_id
            JOIN department dp ON dp.dept_id    = d.dept_id
            WHERE s.work_date = p_date
            ORDER BY d.dept_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    -- 临时表存放统计结果
    DROP TEMPORARY TABLE IF EXISTS tmp_daily_stat;
    CREATE TEMPORARY TABLE tmp_daily_stat (
        dept_id    INT,
        dept_name  VARCHAR(50),
        book_count INT,
        visit_count INT,
        income     DECIMAL(12,2)
    );

    OPEN cur_dept;
    read_loop: LOOP
        FETCH cur_dept INTO v_dept_id, v_dept_name;
        IF v_done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT COUNT(*) INTO v_book_cnt
            FROM appointment a
            JOIN schedule  s ON s.schedule_id = a.schedule_id
            JOIN doctor    d ON d.doctor_id   = s.doctor_id
            WHERE s.work_date = p_date
              AND d.dept_id   = v_dept_id;

        SELECT COUNT(*) INTO v_visit_cnt
            FROM appointment a
            JOIN schedule  s ON s.schedule_id = a.schedule_id
            JOIN doctor    d ON d.doctor_id   = s.doctor_id
            WHERE s.work_date = p_date
              AND d.dept_id   = v_dept_id
              AND a.status    = '已就诊';

        SELECT IFNULL(SUM(p.amount), 0) INTO v_income
            FROM appointment a
            JOIN schedule  s ON s.schedule_id = a.schedule_id
            JOIN doctor    d ON d.doctor_id   = s.doctor_id
            JOIN payment   p ON p.appt_id     = a.appt_id
            WHERE s.work_date = p_date
              AND d.dept_id   = v_dept_id
              AND p.status    = '已支付';

        INSERT INTO tmp_daily_stat
            VALUES (v_dept_id, v_dept_name, v_book_cnt, v_visit_cnt, v_income);
    END LOOP;
    CLOSE cur_dept;

    -- 返回结果集
    SELECT * FROM tmp_daily_stat ORDER BY book_count DESC;
    DROP TEMPORARY TABLE IF EXISTS tmp_daily_stat;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 5. 游标存储过程 sp_mark_no_show
--    功能：用游标遍历"指定日期之前仍处于已预约状态"的记录
--          逐条更新为"爽约"并写入 remark
--    输出：影响行数
-- ----------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_mark_no_show;
DELIMITER $$
CREATE PROCEDURE sp_mark_no_show(
    IN  p_before_date DATE,
    OUT p_affected   INT
)
BEGIN
    DECLARE v_done    INT DEFAULT 0;
    DECLARE v_appt_id INT;
    DECLARE v_count   INT DEFAULT 0;

    DECLARE cur_appt CURSOR FOR
        SELECT a.appt_id
            FROM appointment a
            JOIN schedule    s ON s.schedule_id = a.schedule_id
            WHERE a.status     = '已预约'
              AND s.work_date  < p_before_date;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    OPEN cur_appt;
    loop_appt: LOOP
        FETCH cur_appt INTO v_appt_id;
        IF v_done = 1 THEN
            LEAVE loop_appt;
        END IF;

        UPDATE appointment
            SET status = '爽约',
                appt_no = NULL,
                remark = CONCAT(IFNULL(remark,''),' [系统自动标记爽约]')
            WHERE appt_id = v_appt_id;

        SET v_count = v_count + 1;
    END LOOP;
    CLOSE cur_appt;

    SET p_affected = v_count;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
SELECT '=== procedures.sql executed successfully ===' AS msg;
SHOW PROCEDURE STATUS WHERE Db = 'hospital_db';
SHOW FUNCTION  STATUS WHERE Db = 'hospital_db';
