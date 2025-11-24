"""
最简单的单测：直接 python 运行即可。

用一个临时 SQLite 数据库文件，创建测试表，插入若干行，
然后调用 delete_rows 并检查删除行数与剩余行数。
"""

import os
import sqlite3
import tempfile

from delete_tool import DeleteError, DeleteParams, delete_rows

def setup_test_db() -> str:
    """创建一个临时 SQLite 数据库，并初始化测试表与数据，返回路径。"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="sqlite_mcp_test_")
    os.close(fd)

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    cur.executemany(
        "INSERT INTO todos (title, done) VALUES (?, ?);",
        [
            ("task 1", 0),
            ("task 2", 1),
            ("task 3", 1),
        ],
    )
    conn.commit()
    conn.close()
    return path


def test_delete_with_filters() -> None:
    db_path = setup_test_db()
    try:
        params = DeleteParams(
            db_path=db_path,
            table="todos",
            filters={"done": 1},
            allow_full_table=False,
        )
        result = delete_rows(params)
        assert result.deleted_count == 2, f"期望删除 2 行，实际为 {result.deleted_count}"

        # 再检查数据库中剩余行数
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM todos;")
        remaining = cur.fetchone()[0]
        conn.close()
        assert remaining == 1, f"期望剩余 1 行，实际为 {remaining}"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_forbid_full_table_without_flag() -> None:
    db_path = setup_test_db()
    try:
        params = DeleteParams(
            db_path=db_path,
            table="todos",
            filters={},
            allow_full_table=False,
        )
        try:
            delete_rows(params)
            raise AssertionError("应当抛出 DeleteError(FORBIDDEN_FULL_TABLE_DELETE)，但未抛出。")
        except DeleteError as e:
            assert e.code == "FORBIDDEN_FULL_TABLE_DELETE"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_allow_full_table_delete() -> None:
    db_path = setup_test_db()
    try:
        params = DeleteParams(
            db_path=db_path,
            table="todos",
            filters=None,
            allow_full_table=True,
        )
        result = delete_rows(params)
        assert result.deleted_count == 3, f"期望删除 3 行，实际为 {result.deleted_count}"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    # 简单“手写测试 runner”
    test_delete_with_filters()
    test_forbid_full_table_without_flag()
    test_allow_full_table_delete()
    print("所有 delete_rows 测试通过。")


