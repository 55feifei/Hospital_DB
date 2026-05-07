-- =====================================================================
-- 医院门诊预约管理系统 — 初始化测试数据
-- 文件：05_init_data.sql
-- 说明：5 科室 / 15 医生 / 30 患者 / ~200 排班 / 100+ 预约
--      所有账号默认密码为 "123456"
--      SHA-256("123456") = 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
-- =====================================================================
USE hospital_db;

-- ============== 1. 科室 ==============
INSERT INTO department(dept_name, description, location) VALUES
('内科',     '诊治内科常见病、多发病及疑难杂症', '门诊楼 2 层'),
('外科',     '处理外伤、外科手术、肿瘤切除等',  '门诊楼 3 层'),
('儿科',     '14 岁以下儿童综合诊疗',          '门诊楼 1 层'),
('妇产科',   '妇科疾病诊治与产前检查',          '门诊楼 4 层'),
('眼科',     '眼科疾病检查与治疗',              '门诊楼 5 层');

-- ============== 2. 医生 ==============
INSERT INTO doctor(dept_id, name, gender, title, fee, intro, status) VALUES
(1, '王伟',   '男', '主任医师',   50.00, '从医 30 年，擅长心血管疾病',   '在职'),
(1, '李娜',   '女', '副主任医师', 30.00, '擅长消化系统疾病',             '在职'),
(1, '张磊',   '男', '主治医师',   15.00, '擅长呼吸系统疾病',             '在职'),
(2, '刘芳',   '女', '主任医师',   50.00, '普外科 25 年经验',             '在职'),
(2, '陈强',   '男', '副主任医师', 30.00, '擅长腹腔镜手术',               '在职'),
(2, '杨敏',   '女', '主治医师',   15.00, '擅长创伤外科',                 '在职'),
(3, '赵军',   '男', '主任医师',   50.00, '儿童呼吸道疾病专家',           '在职'),
(3, '黄丽',   '女', '副主任医师', 30.00, '儿童常见病诊疗',               '在职'),
(3, '周涛',   '男', '主治医师',   15.00, '新生儿科',                     '在职'),
(4, '吴婷',   '女', '主任医师',   50.00, '妇科肿瘤',                     '在职'),
(4, '徐静',   '女', '副主任医师', 30.00, '产前检查',                     '在职'),
(4, '孙艳',   '女', '主治医师',   15.00, '月经不调',                     '在职'),
(5, '马辉',   '男', '主任医师',   50.00, '白内障手术专家',               '在职'),
(5, '朱琳',   '女', '副主任医师', 30.00, '近视眼防控',                   '在职'),
(5, '胡阳',   '男', '主治医师',   15.00, '眼底疾病',                     '在职');

-- ============== 3. 患者 ==============
INSERT INTO patient(name, gender, birth_date, id_card, phone, address) VALUES
('陈晨',   '男', '1985-03-12', '110101198503120011', '13800000001', '北京市朝阳区'),
('林峰',   '男', '1990-07-25', '110101199007250012', '13800000002', '北京市海淀区'),
('郭静',   '女', '1992-11-03', '110101199211030013', '13800000003', '北京市西城区'),
('何丽',   '女', '1988-05-19', '110101198805190014', '13800000004', '北京市东城区'),
('钱浩',   '男', '1995-09-08', '110101199509080015', '13800000005', '北京市丰台区'),
('孙磊',   '男', '1980-01-14', '110101198001140016', '13800000006', '北京市石景山区'),
('周琳',   '女', '1993-12-22', '110101199312220017', '13800000007', '北京市通州区'),
('吴桐',   '女', '1987-06-30', '110101198706300018', '13800000008', '北京市顺义区'),
('郑伟',   '男', '1991-04-17', '110101199104170019', '13800000009', '北京市房山区'),
('冯娜',   '女', '1994-08-26', '110101199408260020', '13800000010', '北京市大兴区'),
('蒋宇',   '男', '1989-02-11', '110101198902110021', '13800000011', '北京市昌平区'),
('沈洁',   '女', '1996-10-05', '110101199610050022', '13800000012', '北京市怀柔区'),
('韩雪',   '女', '1983-07-29', '110101198307290023', '13800000013', '北京市平谷区'),
('杨帆',   '男', '1986-12-08', '110101198612080024', '13800000014', '北京市密云区'),
('黄莉',   '女', '1997-03-23', '110101199703230025', '13800000015', '北京市延庆区'),
('梁宇',   '男', '1981-09-14', '110101198109140026', '13800000016', '北京市门头沟区'),
('谢敏',   '女', '1990-11-30', '110101199011300027', '13800000017', '北京市朝阳区'),
('唐磊',   '男', '1984-04-25', '110101198404250028', '13800000018', '北京市海淀区'),
('许丽',   '女', '1995-08-13', '110101199508130029', '13800000019', '北京市西城区'),
('邓刚',   '男', '1988-01-19', '110101198801190030', '13800000020', '北京市东城区'),
('彭静',   '女', '1992-06-04', '110101199206040031', '13800000021', '北京市丰台区'),
('曾杰',   '男', '1986-10-21', '110101198610210032', '13800000022', '北京市石景山区'),
('蔡丽',   '女', '1991-03-08', '110101199103080033', '13800000023', '北京市通州区'),
('魏强',   '男', '1985-12-17', '110101198512170034', '13800000024', '北京市顺义区'),
('袁芳',   '女', '1993-05-26', '110101199305260035', '13800000025', '北京市房山区'),
('卢明',   '男', '1989-08-09', '110101198908090036', '13800000026', '北京市大兴区'),
('范洁',   '女', '1996-02-14', '110101199602140037', '13800000027', '北京市昌平区'),
('丁勇',   '男', '1982-07-23', '110101198207230038', '13800000028', '北京市怀柔区'),
('夏雪',   '女', '1994-11-30', '110101199411300039', '13800000029', '北京市平谷区'),
('章浩',   '男', '1987-04-15', '110101198704150040', '13800000030', '北京市密云区');

-- ============== 4. 账号 ==============
-- 管理员
INSERT INTO user_account(username, password_hash, role, ref_id) VALUES
('admin',  '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'admin',   NULL);

-- 医生账号 doc001 ~ doc015
INSERT INTO user_account(username, password_hash, role, ref_id) VALUES
('doc001', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 1),
('doc002', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 2),
('doc003', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 3),
('doc004', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 4),
('doc005', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 5),
('doc006', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 6),
('doc007', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 7),
('doc008', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 8),
('doc009', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 9),
('doc010', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 10),
('doc011', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 11),
('doc012', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 12),
('doc013', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 13),
('doc014', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 14),
('doc015', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', 15);

-- 患者账号 pat001 ~ pat030
INSERT INTO user_account(username, password_hash, role, ref_id) VALUES
('pat001', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 1),
('pat002', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 2),
('pat003', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 3),
('pat004', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 4),
('pat005', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 5),
('pat006', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 6),
('pat007', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 7),
('pat008', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 8),
('pat009', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 9),
('pat010', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 10),
('pat011', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 11),
('pat012', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 12),
('pat013', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 13),
('pat014', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 14),
('pat015', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 15),
('pat016', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 16),
('pat017', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 17),
('pat018', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 18),
('pat019', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 19),
('pat020', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 20),
('pat021', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 21),
('pat022', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 22),
('pat023', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 23),
('pat024', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 24),
('pat025', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 25),
('pat026', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 26),
('pat027', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 27),
('pat028', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 28),
('pat029', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 29),
('pat030', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'patient', 30);

-- ============== 5. 排班（未来 7 天每位医生上下午各一次）==============
-- 用存储过程批量生成
DROP PROCEDURE IF EXISTS sp_init_schedule;
DELIMITER $$
CREATE PROCEDURE sp_init_schedule()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE d INT DEFAULT 0;
    WHILE d < 15 DO
        SET i = -2;  -- 包含过去 2 天用于演示爽约清理
        WHILE i < 7 DO
            INSERT INTO schedule(doctor_id, work_date, time_slot, total_quota, remaining_quota)
                VALUES (d+1, DATE_ADD(CURDATE(), INTERVAL i DAY), '上午', 20, 20),
                       (d+1, DATE_ADD(CURDATE(), INTERVAL i DAY), '下午', 15, 15);
            SET i = i + 1;
        END WHILE;
        SET d = d + 1;
    END WHILE;
END$$
DELIMITER ;

CALL sp_init_schedule();
DROP PROCEDURE sp_init_schedule;

-- ============== 6. 预约（构造 100+ 条多样化数据）==============
DROP PROCEDURE IF EXISTS sp_init_appointment;
DELIMITER $$
CREATE PROCEDURE sp_init_appointment()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE v_pid INT;
    DECLARE v_sid INT;
    DECLARE v_appt INT;
    DECLARE v_msg VARCHAR(200);
    DECLARE v_total INT;

    SELECT COUNT(*) INTO v_total FROM schedule;

    WHILE i < 120 DO
        SET v_pid = (i % 30) + 1;        -- 30 个患者循环
        SET v_sid = (i % v_total) + 1;   -- 排班循环
        CALL sp_book_appointment(v_pid, v_sid, v_appt, v_msg);
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL sp_init_appointment();
DROP PROCEDURE sp_init_appointment;

-- ============== 7. 模拟"已就诊" / "已取消"状态 ==============
-- 把过去日期 + 部分今日预约更新为已就诊（触发病历自动生成）
UPDATE appointment a
JOIN schedule s ON s.schedule_id = a.schedule_id
SET a.status = '已就诊', a.visit_time = NOW()
WHERE s.work_date < CURDATE() AND a.appt_id % 3 = 0 AND a.status='已预约';

-- 部分预约取消（触发号源恢复）
UPDATE appointment a
SET a.status = '已取消', a.cancel_time = NOW()
WHERE a.appt_id % 13 = 0 AND a.status='已预约';

-- 部分支付完成
UPDATE payment SET status='已支付', pay_time=NOW()
WHERE appt_id IN (SELECT appt_id FROM appointment WHERE status='已就诊');

-- 完善已就诊病历内容
UPDATE medical_record SET
    chief_complaint='发热三天伴咳嗽',
    diagnosis='上呼吸道感染',
    prescription='对乙酰氨基酚 500mg tid; 多饮水',
    advice='清淡饮食，注意休息，三日后复诊'
WHERE record_id % 2 = 0;

UPDATE medical_record SET
    chief_complaint='间歇性头痛一周',
    diagnosis='偏头痛',
    prescription='布洛芬 400mg q8h; 必要时',
    advice='保持规律作息，避免咖啡因'
WHERE record_id % 2 = 1;

-- ============== 8. 验证数据量 ==============
SELECT '=== init data executed ===' AS msg;
SELECT
    (SELECT COUNT(*) FROM department)     AS depts,
    (SELECT COUNT(*) FROM doctor)         AS doctors,
    (SELECT COUNT(*) FROM patient)        AS patients,
    (SELECT COUNT(*) FROM user_account)   AS accounts,
    (SELECT COUNT(*) FROM schedule)       AS schedules,
    (SELECT COUNT(*) FROM appointment)    AS appointments,
    (SELECT COUNT(*) FROM medical_record) AS records,
    (SELECT COUNT(*) FROM payment)        AS payments;
