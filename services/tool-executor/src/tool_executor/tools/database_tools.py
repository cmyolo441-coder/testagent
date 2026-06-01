"""Database Tools — Database operations"""
import sqlite3
import json
import time
import os
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path


@dataclass
class DBResult:
    success: bool
    data: Any = None
    error: str = ""
    operation: str = ""
    rows_affected: int = 0
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "operation": self.operation,
            "rows_affected": self.rows_affected,
            "execution_time_ms": self.execution_time_ms,
        }


class DatabaseTools:
    """Database operations for SQLite databases."""

    BLOCKED_PATHS = ["/etc", "/usr", "/var", "/proc", "/sys"]

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self):
        if self.db_path != ":memory:":
            path = Path(self.db_path)
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row

    def query(self, sql: str, params: tuple = ()) -> DBResult:
        start = time.time()
        try:
            if not self._connection:
                self._connect()

            cursor = self._connection.execute(sql, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"columns": columns, "rows": data, "row_count": len(data)},
                operation="query",
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return DBResult(
                success=False,
                error=str(e),
                operation="query",
                execution_time_ms=duration,
            )

    def insert(self, table: str, data: dict) -> DBResult:
        start = time.time()
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            cursor = self._connection.execute(sql, tuple(data.values()))
            self._connection.commit()

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"lastrowid": cursor.lastrowid, "rows_affected": cursor.rowcount},
                operation="insert",
                rows_affected=cursor.rowcount,
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._connection.rollback()
            return DBResult(
                success=False,
                error=str(e),
                operation="insert",
                execution_time_ms=duration,
            )

    def update(self, table: str, data: dict, where: str,
               where_params: tuple = ()) -> DBResult:
        start = time.time()
        try:
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

            cursor = self._connection.execute(sql, tuple(data.values()) + where_params)
            self._connection.commit()

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"rows_affected": cursor.rowcount},
                operation="update",
                rows_affected=cursor.rowcount,
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._connection.rollback()
            return DBResult(
                success=False,
                error=str(e),
                operation="update",
                execution_time_ms=duration,
            )

    def delete(self, table: str, where: str,
               where_params: tuple = ()) -> DBResult:
        start = time.time()
        try:
            sql = f"DELETE FROM {table} WHERE {where}"
            cursor = self._connection.execute(sql, where_params)
            self._connection.commit()

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"rows_affected": cursor.rowcount},
                operation="delete",
                rows_affected=cursor.rowcount,
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._connection.rollback()
            return DBResult(
                success=False,
                error=str(e),
                operation="delete",
                execution_time_ms=duration,
            )

    def execute(self, sql: str, params: tuple = ()) -> DBResult:
        start = time.time()
        try:
            cursor = self._connection.execute(sql, params)
            self._connection.commit()

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"rows_affected": cursor.rowcount},
                operation="execute",
                rows_affected=cursor.rowcount,
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            self._connection.rollback()
            return DBResult(
                success=False,
                error=str(e),
                operation="execute",
                execution_time_ms=duration,
            )

    def create_table(self, table_name: str, columns: dict[str, str]) -> DBResult:
        cols = ", ".join([f"{name} {dtype}" for name, dtype in columns.items()])
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
        return self.execute(sql)

    def list_tables(self) -> DBResult:
        return self.query("SELECT name FROM sqlite_master WHERE type='table'")

    def table_info(self, table_name: str) -> DBResult:
        return self.query(f"PRAGMA table_info({table_name})")

    def backup(self, backup_path: str) -> DBResult:
        start = time.time()
        try:
            backup_conn = sqlite3.connect(backup_path)
            self._connection.backup(backup_conn)
            backup_conn.close()

            duration = (time.time() - start) * 1000
            return DBResult(
                success=True,
                data={"backup_path": backup_path},
                operation="backup",
                execution_time_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return DBResult(
                success=False,
                error=str(e),
                operation="backup",
                execution_time_ms=duration,
            )

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        self.close()
