# 医院门诊预约管理系统

数据库课程大作业 — 基于 Python + MySQL 实现的医院门诊预约管理系统。

## 技术栈

- **数据库**：MySQL 8.0+ (InnoDB)
- **后端**：Python 3.9+ / PyMySQL
- **界面**：PyQt5 桌面 GUI
- **架构**：三层（DAO / Service / UI）

## 目录结构

```
.
├── docs/        需求分析、数据库设计、系统设计、测试报告、操作手册
├── sql/         建库 / 触发器 / 存储过程 / 视图 / 种子数据 / 权限 / 备份
├── src/         Python 源码（dao / service / ui / main.py）
├── tests/       单元测试
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库（默认 root 账号，按提示输密码）
mysql -u root -p < sql/01_schema.sql
mysql -u root -p < sql/02_triggers.sql
mysql -u root -p < sql/03_procedures.sql
mysql -u root -p < sql/04_views.sql
mysql -u root -p < sql/05_init_data.sql
mysql -u root -p < sql/06_security.sql

# 3. 修改 src/config.py 中的数据库密码

# 4. 启动 GUI
python src/main.py
```

## 默认账号

| 角色   | 用户名     | 密码    |
|--------|-----------|---------|
| 管理员 | admin     | 123456  |
| 医生   | doc001    | 123456  |
| 患者   | pat001    | 123456  |

## 文档

- [需求分析文档](docs/01_需求分析文档.md)
- [数据库设计文档](docs/02_数据库设计文档.md)
- [系统设计说明书](docs/03_系统设计说明书.md)
- [测试报告](docs/04_测试报告.md)
- [操作手册](docs/05_操作手册.md)

## 评分点速查

| 作业要求               | 落实位置                                     |
|-----------------------|----------------------------------------------|
| ≥ 5 张表 + 参照关系   | `sql/01_schema.sql`（8 张表，多级外键）       |
| ≥ 3 个触发器          | `sql/02_triggers.sql`（4 个触发器）           |
| ≥ 2 个带参存储过程    | `sql/03_procedures.sql`（3 个）               |
| ≥ 2 个游标存储过程    | `sql/03_procedures.sql`（2 个）               |
| ≥ 2 个二级索引        | `sql/01_schema.sql`（3 个，附性能分析）       |
| 规范化（≥ 3NF）       | `docs/02_数据库设计文档.md`                   |
| GUI                   | `src/ui/`                                    |
| 安全 / 备份           | `sql/06_security.sql`、`sql/07_backup_restore.md` |
