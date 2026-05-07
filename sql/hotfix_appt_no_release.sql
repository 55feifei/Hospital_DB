-- =====================================================================
-- 热修复：取消/爽约后释放 appt_no 排队序号
-- 应用方式：mysql -uroot -p hospital_db < sql/hotfix_appt_no_release.sql
-- =====================================================================
USE hospital_db;

-- 1) appt_no 改为允许 NULL（UNIQUE(schedule_id, appt_no) 在 MySQL 下允许多个 NULL）
ALTER TABLE appointment MODIFY appt_no INT NULL COMMENT '排队序号；取消/爽约后置 NULL 以释放序号';

-- 2) 历史脏数据：把已取消/爽约记录的序号清空，释放给后续预约复用
UPDATE appointment
   SET appt_no = NULL
 WHERE status IN ('已取消','爽约')
   AND appt_no IS NOT NULL;

-- 3) 重建 sp_book_appointment（仅用"有效"预约计算下一个序号）
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
            -- 仅在"有效"预约中取最大值，已取消/爽约不占号
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

-- 4) 重建 sp_cancel_appointment（取消时清空 appt_no）
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
                appt_no = NULL
            WHERE appt_id = p_appt_id;

        UPDATE payment
            SET status = '已退款',
                pay_time = IFNULL(pay_time, NOW())
            WHERE appt_id = p_appt_id AND status = '已支付';

        SET p_msg = '取消成功';
        COMMIT;
    END IF;
END$$
DELIMITER ;

-- 5) 重建 sp_mark_no_show（爽约时清空 appt_no）
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

SELECT '=== hotfix_appt_no_release applied ===' AS msg;
