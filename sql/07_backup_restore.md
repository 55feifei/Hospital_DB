# 数据库备份与恢复操作手册

本系统采用 MySQL 自带的 `mysqldump` 工具完成逻辑备份与恢复，可满足日常维护、迁移、灾备的需求。

## 一、完整备份

```bash
# 备份整个数据库（含表结构 + 数据 + 触发器 + 存储过程）
mysqldump -u root -p \
          --routines --triggers --events \
          --single-transaction \
          --default-character-set=utf8mb4 \
          hospital_db > hospital_db_backup_$(date +%Y%m%d).sql
```

参数说明：
- `--routines`：包含存储过程与函数
- `--triggers`：包含触发器（默认开启，显式列出便于检查）
- `--events`：包含事件调度
- `--single-transaction`：InnoDB 一致性快照，无需锁表
- `--default-character-set=utf8mb4`：避免中文乱码

## 二、仅备份结构 / 仅备份数据

```bash
# 只导出表结构（schema only）
mysqldump -u root -p --no-data --routines --triggers \
          hospital_db > hospital_db_schema.sql

# 只导出数据（无 DDL）
mysqldump -u root -p --no-create-info --skip-triggers \
          hospital_db > hospital_db_data.sql
```

## 三、恢复

```bash
# 1. 重新创建数据库
mysql -u root -p -e "DROP DATABASE IF EXISTS hospital_db; CREATE DATABASE hospital_db CHARACTER SET utf8mb4;"

# 2. 导入备份文件
mysql -u root -p hospital_db < hospital_db_backup_20260503.sql

# 3. 验证
mysql -u root -p -e "USE hospital_db; SELECT COUNT(*) FROM appointment;"
```

## 四、定时备份建议（生产环境）

Windows 计划任务中调用 `backup.bat`：

```batch
@echo off
set BACKUP_DIR=D:\db_backup
set DATESTR=%date:~0,4%%date:~5,2%%date:~8,2%
mysqldump -u root -p"YourPwd" --routines --triggers --single-transaction ^
          hospital_db > %BACKUP_DIR%\hospital_db_%DATESTR%.sql
forfiles /p %BACKUP_DIR% /s /m *.sql /d -7 /c "cmd /c del @path"
```

通过任务计划程序设置每日凌晨 02:00 执行，并保留最近 7 天备份。

## 五、灾难恢复演练流程

1. 在新机器上安装相同版本的 MySQL
2. 创建空数据库 `CREATE DATABASE hospital_db;`
3. 复制最近一次备份文件到新机器
4. 执行 `mysql -u root -p hospital_db < backup.sql`
5. 重新执行 `06_security.sql` 创建应用账号
6. 修改 `src/config.py` 中的 host 指向新地址
7. 启动应用，跑一遍 `tests/test_appointment.py` 验证
