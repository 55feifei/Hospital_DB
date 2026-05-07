-- =====================================================================
-- 医院门诊预约管理系统 — 数据库安全设置
-- 文件：06_security.sql
-- 说明：创建专用应用账号 hospital_app，遵循最小权限原则
-- =====================================================================

-- 删除可能已存在的账号
DROP USER IF EXISTS 'hospital_app'@'localhost';
DROP USER IF EXISTS 'hospital_readonly'@'localhost';

-- ----------------------------------------------------------------
-- 应用账号：hospital_app
--   仅授予对 hospital_db 的 SELECT/INSERT/UPDATE/DELETE/EXECUTE
--   不授予 DROP / ALTER / GRANT 等危险权限
-- ----------------------------------------------------------------
CREATE USER 'hospital_app'@'localhost' IDENTIFIED BY 'App@2026';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE
    ON hospital_db.*
    TO 'hospital_app'@'localhost';

-- ----------------------------------------------------------------
-- 只读账号：hospital_readonly（用于报表/审计）
-- ----------------------------------------------------------------
CREATE USER 'hospital_readonly'@'localhost' IDENTIFIED BY 'Read@2026';
GRANT SELECT ON hospital_db.* TO 'hospital_readonly'@'localhost';

FLUSH PRIVILEGES;

-- ----------------------------------------------------------------
-- 显示当前账号清单
-- ----------------------------------------------------------------
SELECT '=== security.sql executed ===' AS msg;
SELECT user, host FROM mysql.user
    WHERE user IN ('hospital_app','hospital_readonly');

SHOW GRANTS FOR 'hospital_app'@'localhost';
SHOW GRANTS FOR 'hospital_readonly'@'localhost';
