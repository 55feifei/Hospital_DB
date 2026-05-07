"""数据库连接与全局配置。运行前请按本机情况修改 PASSWORD。"""

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "050124wjr/*",            # ← 改成你本机 MySQL root 密码
    "database": "hospital_db",
    "charset":  "utf8mb4",
    "autocommit": False,
}

# 应用账号（生产推荐使用 hospital_app，权限最小化）
DB_CONFIG_APP = {
    **DB_CONFIG,
    "user":     "hospital_app",
    "password": "App@2026",
}

APP_NAME    = "医院门诊预约管理系统"
APP_VERSION = "1.0.0"
