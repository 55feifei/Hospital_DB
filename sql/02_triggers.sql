-- =====================================================================
-- 医院门诊预约管理系统 — 触发器
-- 文件：02_triggers.sql
-- 作业要求覆盖：≥ 3 个触发器（本文件实现 4 个）
-- =====================================================================
USE hospital_db;

-- ----------------------------------------------------------------
-- 触发器 1：trg_appt_quota_check（BEFORE INSERT）
--   作用：插入预约前校验排班是否还有号源 / 是否停诊
--         若号源已满或停诊则抛出错误（防超约）
-- ----------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_appt_quota_check;
DELIMITER $$
CREATE TRIGGER trg_appt_quota_check
BEFORE INSERT ON appointment
FOR EACH ROW
BEGIN
    DECLARE v_remaining INT;
    DECLARE v_status    VARCHAR(10);

    SELECT remaining_quota, status
        INTO v_remaining, v_status
        FROM schedule
        WHERE schedule_id = NEW.schedule_id;

    IF v_status = '停诊' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '该排班已停诊，无法预约';
    END IF;

    IF v_remaining <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '号源已满，无法预约';
    END IF;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 触发器 2：trg_appt_after_insert（AFTER INSERT）
--   作用：预约成功后排班剩余号源 -1，并自动生成待支付的缴费单
-- ----------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_appt_after_insert;
DELIMITER $$
CREATE TRIGGER trg_appt_after_insert
AFTER INSERT ON appointment
FOR EACH ROW
BEGIN
    DECLARE v_fee DECIMAL(8,2);

    UPDATE schedule
        SET remaining_quota = remaining_quota - 1
        WHERE schedule_id = NEW.schedule_id;

    SELECT d.fee INTO v_fee
        FROM schedule s
        JOIN doctor   d ON d.doctor_id = s.doctor_id
        WHERE s.schedule_id = NEW.schedule_id;

    INSERT INTO payment(appt_id, amount, pay_method, status)
        VALUES (NEW.appt_id, v_fee, '微信', '待支付');
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 触发器 3：trg_appt_after_update（AFTER UPDATE）
--   作用：①预约状态变为"已取消"或"爽约"时恢复号源
--         ②预约状态变为"已就诊"时自动建立病历
-- ----------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_appt_after_update;
DELIMITER $$
CREATE TRIGGER trg_appt_after_update
AFTER UPDATE ON appointment
FOR EACH ROW
BEGIN
    -- 恢复号源（仅在状态由"已预约"变为"已取消"时）
    IF OLD.status = '已预约' AND NEW.status = '已取消' THEN
        UPDATE schedule
            SET remaining_quota = remaining_quota + 1
            WHERE schedule_id = NEW.schedule_id;
    END IF;

    -- 自动建立病历（仅在状态变为"已就诊"且尚无病历时）
    IF OLD.status <> '已就诊' AND NEW.status = '已就诊' THEN
        INSERT IGNORE INTO medical_record(appt_id, chief_complaint, diagnosis, visit_time)
            VALUES (NEW.appt_id, '(待补充)', '(待补充)', NOW());
    END IF;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
-- 触发器 4：trg_doctor_before_delete（BEFORE DELETE）
--   作用：医生删除前若存在未完成预约则阻止删除
-- ----------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_doctor_before_delete;
DELIMITER $$
CREATE TRIGGER trg_doctor_before_delete
BEFORE DELETE ON doctor
FOR EACH ROW
BEGIN
    DECLARE v_pending INT;

    SELECT COUNT(*)
        INTO v_pending
        FROM appointment a
        JOIN schedule s ON s.schedule_id = a.schedule_id
        WHERE s.doctor_id = OLD.doctor_id
          AND a.status = '已预约';

    IF v_pending > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '该医生存在未完成预约，禁止删除';
    END IF;
END$$
DELIMITER ;

-- ----------------------------------------------------------------
SELECT '=== triggers.sql executed successfully ===' AS msg;
SHOW TRIGGERS;
