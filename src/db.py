"""数据库连接封装：单例、上下文管理器、事务支持。"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from config import DB_CONFIG


class Database:
    """轻量级连接管理器（按需建连，调用方负责关闭）。"""

    @staticmethod
    def connect():
        return pymysql.connect(**DB_CONFIG, cursorclass=DictCursor)

    @staticmethod
    @contextmanager
    def cursor(commit: bool = False):
        """普通查询上下文：with Database.cursor() as cur: ..."""
        conn = Database.connect()
        try:
            cur = conn.cursor()
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    @contextmanager
    def transaction():
        """事务上下文：异常自动回滚，正常退出自动提交。"""
        conn = Database.connect()
        try:
            cur = conn.cursor()
            yield cur, conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def query(sql: str, args=None):
        with Database.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    @staticmethod
    def execute(sql: str, args=None) -> int:
        """返回受影响行数。"""
        with Database.cursor(commit=True) as cur:
            return cur.execute(sql, args)

    @staticmethod
    def call_proc(proc_name: str, args: tuple = ()):
        """调用存储过程，返回 (输出参数列表, 结果集列表)。"""
        conn = Database.connect()
        try:
            cur = conn.cursor()
            cur.callproc(proc_name, args)
            result_sets = []
            while True:
                rows = cur.fetchall()
                if rows:
                    result_sets.append(rows)
                if not cur.nextset():
                    break

            # 取出 OUT 参数
            placeholders = ",".join(f"@_{proc_name}_{i}" for i in range(len(args)))
            out_params = []
            if placeholders:
                cur.execute(f"SELECT {placeholders}")
                row = cur.fetchone()
                if row:
                    out_params = list(row.values())
            conn.commit()
            return out_params, result_sets
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
