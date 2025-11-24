"""
基于 mcp Python SDK 的 SQLite 删除工具服务器。

当前仅暴露一个 MCP 工具方法：delete_rows。

说明：使用 `list_tools` / `call_tool` 注册工具，
并通过 stdio_server + Server.run 启动。
"""

import asyncio
import json
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .delete_tool import DeleteError, DeleteParams, delete_rows


server = Server("sqlite-delete-tool")


DELETE_ROWS_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "title": "delete_rows_params",
    "description": "Parameters for deleting rows from a SQLite table.",
    "properties": {
        "db_path": {
            "type": "string",
            "description": "Absolute path to the SQLite database file.",
        },
        "table": {
            "type": "string",
            "description": "Name of the table to delete rows from.",
        },
        "filters": {
            "type": "object",
            "description": (
                "Simple equality filters in AND relation, mapping column name "
                "to exact value. If omitted or empty, full table delete "
                "requires allow_full_table = true."
            ),
            "additionalProperties": {
                "description": (
                    "Value to be matched by equality. Recommended to be simple "
                    "JSON scalar types (string, number, boolean, null)."
                )
            },
        },
        "allow_full_table": {
            "type": "boolean",
            "description": (
                "If true, allows deleting all rows when filters is omitted or empty."
            ),
            "default": False,
        },
    },
    "required": ["db_path", "table"],
    "additionalProperties": False,
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    """
    向 MCP 客户端声明本服务提供的工具列表。
    当前仅有一个 delete_rows。
    """
    return [
        Tool(
            name="delete_rows",
            description="从指定 SQLite 数据库的某个表中删除符合简单等值条件的行。",
            inputSchema=DELETE_ROWS_INPUT_SCHEMA,
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    MCP 工具调用入口：根据 name 分发到对应实现，并返回内容列表。
    这里统一返回一个 TextContent，内容为 JSON 字符串。
    """
    if name != "delete_rows":
        # 当前仅支持 delete_rows 一个工具
        raise RuntimeError(f"UNKNOWN_TOOL: {name}")

    try:
        delete_params = DeleteParams(
            db_path=arguments.get("db_path", ""),
            table=arguments.get("table", ""),
            filters=arguments.get("filters"),
            allow_full_table=bool(arguments.get("allow_full_table", False)),
        )

        result = delete_rows(delete_params)
        payload = {
            "deleted_count": result.deleted_count,
            "table": result.table,
            "db_path": result.db_path,
        }
        # MCP 协议要求返回 Content 列表，这里用一个文本内容承载 JSON。
        return [
            TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False),
            )
        ]
    except DeleteError as e:
        # 这里直接抛出带 code 的 RuntimeError，交给 MCP 框架封装。
        raise RuntimeError(f"{e.code}: {e.message}") from e


async def main() -> None:
    """
    通过 stdio 启动 MCP 服务器。
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

