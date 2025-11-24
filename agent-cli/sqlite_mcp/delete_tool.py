import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DeleteParams:
    """delete_rows 的入参模型。"""

    db_path: str
    table: str
    filters: Optional[Dict[str, Any]] = None
    allow_full_table: bool = False


@dataclass
class DeleteResult:
    """delete_rows 的返回模型。"""

    deleted_count: int
    table: str
    db_path: str


class DeleteError(Exception):
    """统一的删除操作异常，包含错误码与消息。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def delete_rows(params: DeleteParams) -> DeleteResult:
    """
    执行 SQLite 删除操作的核心逻辑。

    仅支持简单等值过滤条件，filters 为 {列名: 值}，多个条件按 AND 组合。
    若 filters 为空或缺省，则必须显式 allow_full_table=True 才允许整表删除。
    """
    db_path = params.db_path
    table = params.table
    filters = params.filters or {}
    allow_full_table = params.allow_full_table

    if not db_path or not table:
        raise DeleteError(
            "INVALID_INPUT",
            "缺少必要参数：db_path 或 table。",
        )

    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        raise DeleteError(
            "DB_NOT_FOUND",
            f"数据库文件不存在或不可访问：{db_path}",
        )

    # 安全保护：默认不允许整表删除
    if (not filters) and not allow_full_table:
        raise DeleteError(
            "FORBIDDEN_FULL_TABLE_DELETE",
            "未提供删除条件，且未显式允许整表删除（allow_full_table = true）。",
        )

    # 校验 filters 类型
    if filters is not None and not isinstance(filters, dict):
        raise DeleteError(
            "INVALID_FILTERS",
            "filters 必须是一个对象（字典），表示列名到值的映射。",
        )

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        )
        if cursor.fetchone() is None:
            raise DeleteError(
                "TABLE_NOT_FOUND",
                f"表不存在：{table}",
            )

        # 构建 SQL 语句
        sql = f"DELETE FROM \"{table}\""
        values: tuple[Any, ...] = ()

        if filters:
            # 简单等值 AND 条件
            conditions = []
            values_list = []
            for col, value in filters.items():
                # 列名简单保护：不允许包含危险字符
                if not isinstance(col, str) or any(c in col for c in "\"';"):
                    raise DeleteError(
                        "INVALID_FILTERS",
                        f"非法列名：{col!r}",
                    )
                conditions.append(f"\"{col}\" = ?")
                values_list.append(value)
            sql += " WHERE " + " AND ".join(conditions)
            values = tuple(values_list)

        cursor.execute(sql, values)
        deleted_count = cursor.rowcount if cursor.rowcount is not None else 0
        conn.commit()

        return DeleteResult(
            deleted_count=deleted_count,
            table=table,
            db_path=db_path,
        )
    except DeleteError:
        # 直接向上抛，交给上层统一处理
        raise
    except sqlite3.Error as e:  # pragma: no cover - 具体错误信息依赖运行环境
        raise DeleteError(
            "SQL_EXECUTION_ERROR",
            f"执行删除操作失败：{e}",
        ) from e
    finally:
        if conn is not None:
            conn.close()


