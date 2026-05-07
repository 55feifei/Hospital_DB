-- 完全清理脚本（开发调试用）
DROP DATABASE IF EXISTS hospital_db;
DROP USER IF EXISTS 'hospital_app'@'localhost';
DROP USER IF EXISTS 'hospital_readonly'@'localhost';
SELECT 'All hospital objects dropped.' AS msg;
