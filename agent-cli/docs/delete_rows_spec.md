## delete_rows 方法说明（最简版）

### 功能概述

`delete_rows` 方法用于从指定的 SQLite 数据库文件中的某个表删除记录。  
仅支持 **简单等值过滤条件**，不支持大于、小于、IN 等复杂表达式。

### 入参（逻辑）

- `db_path`（字符串，必填）
  - SQLite 数据库文件的路径（推荐绝对路径）。
- `table`（字符串，必填）
  - 要删除记录的表名。
- `filters`（对象，可选）
  - 结构：`{ 列名: 值 }`
  - 表示多个等值条件的 AND 组合，例如：
    - `{ "status": "done", "user_id": 123 }`
    - 等价于 SQL：`WHERE "status" = ? AND "user_id" = ?`
- `allow_full_table`（布尔，可选，默认 `false`）
  - 当 `filters` 为空或未提供时：
    - 若 `allow_full_table = true`，允许执行整表删除（`DELETE FROM table;`）。
    - 否则会拒绝执行并返回错误。

### 入参 JSON Schema（示意）

```json
{
  "type": "object",
  "title": "delete_rows_params",
  "description": "Parameters for deleting rows from a SQLite table.",
  "properties": {
    "db_path": {
      "type": "string",
      "description": "Absolute path to the SQLite database file."
    },
    "table": {
      "type": "string",
      "description": "Name of the table to delete rows from."
    },
    "filters": {
      "type": "object",
      "description": "Simple equality filters in AND relation, mapping column name to exact value. If omitted or empty, full table delete requires allow_full_table = true.",
      "additionalProperties": {
        "description": "Value to be matched by equality. Only scalar JSON types are recommended (string, number, boolean, null)."
      }
    },
    "allow_full_table": {
      "type": "boolean",
      "description": "If true, allows deleting all rows when filters is omitted or empty.",
      "default": false
    }
  },
  "required": ["db_path", "table"],
  "additionalProperties": false
}
```

### 返回值

成功时返回对象：

- `deleted_count`（整数）
  - 实际删除的行数。
- `table`（字符串）
  - 执行删除操作的表名（回显）。
- `db_path`（字符串）
  - 使用的数据库路径（回显）。

返回示例：

```json
{
  "deleted_count": 3,
  "table": "todos",
  "db_path": "/path/to/todo.db"
}
```

### 错误语义（逻辑）

实现内部会抛出带错误码的异常，常见错误包括：

- `DB_NOT_FOUND`：数据库文件不存在或不可访问。
- `TABLE_NOT_FOUND`：指定的表不存在。
- `FORBIDDEN_FULL_TABLE_DELETE`：未提供过滤条件且未显式允许整表删除。
- `INVALID_FILTERS`：filters 类型错误或包含非法列名。
- `SQL_EXECUTION_ERROR`：底层 SQL 执行失败，例如锁表等。


