-- =====================================================================
-- 医院门诊预约管理系统 — 数据库 DDL
-- 文件：01_schema.sql
-- 说明：建库、建表、约束、二级索引
-- 作业要求覆盖：≥5 张表 + 参照关系 + ≥2 二级索引
-- =====================================================================

DROP DATABASE IF EXISTS hospital_db;
CREATE DATABASE hospital_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE hospital_db;

-- ----------------------------------------------------------------
-- 表 1：科室 department
-- ----------------------------------------------------------------
CREATE TABLE department (
    dept_id      INT AUTO_INCREMENT PRIMARY KEY,
    dept_name    VARCHAR(50)  NOT NULL UNIQUE COMMENT '科室名称',
    description  VARCHAR(255) DEFAULT NULL    COMMENT '科室描述',
    location     VARCHAR(50)  DEFAULT NULL    COMMENT '所在楼层',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='科室信息表';

-- ----------------------------------------------------------------
-- 表 2：医生 doctor
-- ----------------------------------------------------------------
CREATE TABLE doctor (
    doctor_id    INT AUTO_INCREMENT PRIMARY KEY,
    dept_id      INT          NOT NULL,
    name         VARCHAR(30)  NOT NULL          COMMENT '姓名',
    gender       ENUM('男','女') NOT NULL DEFAULT '男',
    title        ENUM('住院医师','主治医师','副主任医师','主任医师') NOT NULL DEFAULT '主治医师',
    fee          DECIMAL(8,2) NOT NULL DEFAULT 0 COMMENT '挂号费',
    intro        VARCHAR(500) DEFAULT NULL       COMMENT '医生简介',
    status       ENUM('在职','停诊','离职') NOT NULL DEFAULT '在职',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_doctor_dept
        FOREIGN KEY (dept_id) REFERENCES department(dept_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_doctor_fee CHECK (fee >= 0)
) ENGINE=InnoDB COMMENT='医生信息表';

-- ----------------------------------------------------------------
-- 表 3：患者 patient
-- ----------------------------------------------------------------
CREATE TABLE patient (
    patient_id   INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(30)  NOT NULL,
    gender       ENUM('男','女') NOT NULL DEFAULT '男',
    birth_date   DATE         DEFAULT NULL,
    id_card      CHAR(18)     NOT NULL UNIQUE  COMMENT '身份证号',
    phone        VARCHAR(20)  NOT NULL UNIQUE  COMMENT '手机号',
    address      VARCHAR(200) DEFAULT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_patient_idcard CHECK (CHAR_LENGTH(id_card) = 18)
) ENGINE=InnoDB COMMENT='患者信息表';

-- ----------------------------------------------------------------
-- 表 4：账号 user_account（统一登录入口）
-- ----------------------------------------------------------------
CREATE TABLE user_account (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(30)  NOT NULL UNIQUE,
    password_hash  CHAR(64)     NOT NULL              COMMENT 'SHA-256 哈希',
    role           ENUM('admin','doctor','patient') NOT NULL,
    ref_id         INT          DEFAULT NULL          COMMENT '医生/患者主键(admin 为 NULL)',
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login     DATETIME     DEFAULT NULL
) ENGINE=InnoDB COMMENT='登录账号表';

-- ----------------------------------------------------------------
-- 表 5：排班 schedule
-- ----------------------------------------------------------------
CREATE TABLE schedule (
    schedule_id      INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id        INT     NOT NULL,
    work_date        DATE    NOT NULL,
    time_slot        ENUM('上午','下午') NOT NULL,
    total_quota      INT     NOT NULL DEFAULT 20  COMMENT '总号源',
    remaining_quota  INT     NOT NULL DEFAULT 20  COMMENT '剩余号源',
    status           ENUM('正常','停诊') NOT NULL DEFAULT '正常',
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schedule_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_schedule UNIQUE (doctor_id, work_date, time_slot),
    CONSTRAINT chk_schedule_quota CHECK (remaining_quota >= 0
                                         AND remaining_quota <= total_quota)
) ENGINE=InnoDB COMMENT='医生排班表';

-- ----------------------------------------------------------------
-- 表 6：预约 appointment
-- ----------------------------------------------------------------
CREATE TABLE appointment (
    appt_id        INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT     NOT NULL,
    schedule_id    INT     NOT NULL,
    appt_no        INT     DEFAULT NULL          COMMENT '排队序号；取消/爽约后置 NULL 以释放序号',
    status         ENUM('已预约','已就诊','已取消','爽约') NOT NULL DEFAULT '已预约',
    create_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancel_time    DATETIME DEFAULT NULL,
    visit_time     DATETIME DEFAULT NULL,
    remark         VARCHAR(255) DEFAULT NULL,
    CONSTRAINT fk_appt_patient
        FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appt_schedule
        FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_appt UNIQUE (schedule_id, appt_no)
) ENGINE=InnoDB COMMENT='预约挂号表';

-- ----------------------------------------------------------------
-- 表 7：病历 medical_record
-- ----------------------------------------------------------------
CREATE TABLE medical_record (
    record_id     INT AUTO_INCREMENT PRIMARY KEY,
    appt_id       INT      NOT NULL UNIQUE,
    chief_complaint VARCHAR(500) DEFAULT NULL  COMMENT '主诉',
    diagnosis     VARCHAR(500) DEFAULT NULL    COMMENT '诊断',
    prescription  VARCHAR(1000) DEFAULT NULL   COMMENT '处方',
    advice        VARCHAR(500) DEFAULT NULL    COMMENT '医嘱',
    visit_time    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_record_appt
        FOREIGN KEY (appt_id) REFERENCES appointment(appt_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB COMMENT='就诊病历表';

-- ----------------------------------------------------------------
-- 表 8：缴费 payment
-- ----------------------------------------------------------------
CREATE TABLE payment (
    payment_id    INT AUTO_INCREMENT PRIMARY KEY,
    appt_id       INT      NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    pay_method    ENUM('现金','微信','支付宝','银行卡','医保') NOT NULL DEFAULT '微信',
    status        ENUM('待支付','已支付','已退款') NOT NULL DEFAULT '待支付',
    pay_time      DATETIME DEFAULT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payment_appt
        FOREIGN KEY (appt_id) REFERENCES appointment(appt_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0)
) ENGINE=InnoDB COMMENT='缴费记录表';

-- ----------------------------------------------------------------
-- 二级索引（≥ 2，本系统建立 3 个）
-- 性能分析详见 docs/02_数据库设计文档.md
--
-- 注意：选择"非外键列开头"的复合索引，避免与外键自动索引冗余、
--      并确保索引可被 DROP/CREATE 用于性能基准测试（外键所需索引不可删）。
-- ----------------------------------------------------------------
-- 索引 1：加速"患者预约历史"查询
--   场景：WHERE patient_id=? ORDER BY create_time DESC
--   说明：patient_id 是外键，但 (patient_id, create_time) 复合索引仍可作为外键索引使用
CREATE INDEX idx_appt_patient_date
    ON appointment(patient_id, create_time);

-- 索引 2：加速"按日期筛选可用排班"查询（患者选号高频路径）
--   场景：WHERE work_date BETWEEN ? AND ? AND remaining_quota>0
--   说明：work_date / remaining_quota 都不是外键，可自由 DROP/CREATE 做性能对比
CREATE INDEX idx_schedule_date_remain
    ON schedule(work_date, remaining_quota);

-- 索引 3：加速"待支付订单"查询（管理员端高频路径）
--   场景：WHERE status='待支付' ORDER BY created_at DESC
--   说明：status / created_at 都不是外键，可自由 DROP/CREATE 做性能对比
CREATE INDEX idx_payment_status_time
    ON payment(status, created_at);

-- 索引 4：加速账号登录查询（WHERE username=?）— UNIQUE 已自动建立，此处不再创建

-- ----------------------------------------------------------------
-- 完成
-- ----------------------------------------------------------------
SELECT '=== schema.sql executed successfully ===' AS msg;
SHOW TABLES;
