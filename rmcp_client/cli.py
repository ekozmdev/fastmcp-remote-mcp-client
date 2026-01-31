from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from fastmcp import Client

from rmcp_client.config import (
    ConfigError,
    build_single_server_config,
    get_server_config,
    load_config,
    normalize_server_config,
)


CONFIG_PATH = Path("mcp_servers.json")


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ConfigError("Invalid arguments", {"message": message})


def parse_args() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--server")

    parser = JsonArgumentParser(prog="rmcp-client", add_help=False, parents=[common])
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-tools", parents=[common], add_help=True)

    call_parser = subparsers.add_parser("call-tool", parents=[common], add_help=True)
    call_parser.add_argument("--tool")
    call_parser.add_argument("--args", default="{}")

    return parser.parse_args()


def parse_json_arg(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError("Invalid JSON for --args", {"error": str(exc)}) from exc
    if not isinstance(parsed, dict):
        raise ConfigError("--args must be a JSON object", {"value_type": type(parsed).__name__})
    return parsed


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except TypeError:
            return value.model_dump()
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return to_jsonable(vars(value))
    return str(value)


def tool_to_dict(tool: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    name = getattr(tool, "name", None)
    if name is not None:
        data["name"] = name
    description = getattr(tool, "description", None)
    if description is not None:
        data["description"] = description

    if hasattr(tool, "inputSchema"):
        data["inputSchema"] = to_jsonable(getattr(tool, "inputSchema"))
    elif hasattr(tool, "input_schema"):
        data["inputSchema"] = to_jsonable(getattr(tool, "input_schema"))
    elif hasattr(tool, "model_dump"):
        try:
            dumped = tool.model_dump()
            if "inputSchema" in dumped:
                data["inputSchema"] = to_jsonable(dumped["inputSchema"])
            elif "input_schema" in dumped:
                data["inputSchema"] = to_jsonable(dumped["input_schema"])
        except Exception:
            pass
    return data


async def run_list_tools(server: str) -> dict[str, Any]:
    config = load_config(CONFIG_PATH)
    server_cfg = normalize_server_config(get_server_config(config, server))
    client_cfg = build_single_server_config(server, server_cfg)
    async with Client(client_cfg) as client:
        tools = await client.list_tools()
    return {"ok": True, "result": [tool_to_dict(tool) for tool in tools]}


async def run_call_tool(
    server: str,
    tool_name: str,
    tool_args: dict[str, Any],
) -> dict[str, Any]:
    config = load_config(CONFIG_PATH)
    server_cfg = normalize_server_config(get_server_config(config, server))
    client_cfg = build_single_server_config(server, server_cfg)
    async with Client(client_cfg) as client:
        result = await client.call_tool(tool_name, tool_args)
    return {"ok": True, "result": to_jsonable(result)}


def print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def make_error_payload(exc: Exception) -> dict[str, Any]:
    err_type = exc.__class__.__name__
    message = str(exc)
    details: str | dict[str, Any]
    if isinstance(exc, ConfigError) and exc.details is not None:
        details = exc.details
    else:
        details = message if message else {}
    if not isinstance(details, (str, dict)):
        details = str(details)
    return {"ok": False, "error": {"type": err_type, "message": message, "details": details}}


def main() -> int:
    try:
        args = parse_args()
        if not args.command:
            raise ConfigError("Command is required", {"allowed": ["list-tools", "call-tool"]})
        if not args.server:
            raise ConfigError("--server is required")

        if args.command == "list-tools":
            payload = asyncio.run(run_list_tools(args.server))
        elif args.command == "call-tool":
            if not args.tool:
                raise ConfigError("--tool is required for call-tool")
            tool_args = parse_json_arg(args.args)
            payload = asyncio.run(run_call_tool(args.server, args.tool, tool_args))
        else:
            raise ConfigError("Unknown command", {"command": args.command})
        print_json(payload)
        return 0
    except Exception as exc:
        print_json(make_error_payload(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
