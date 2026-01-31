from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    def __init__(self, message: str, details: str | dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError("Config file not found", {"path": str(path)})
    if not path.is_file():
        raise ConfigError("Config path is not a file", {"path": str(path)})
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError("Failed to read config file", {"error": str(exc)}) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError("Invalid JSON in config file", {"error": str(exc)}) from exc
    if not isinstance(data, dict):
        raise ConfigError("Config root must be an object")
    if "mcpServers" not in data:
        raise ConfigError("Config missing 'mcpServers' key")
    if not isinstance(data["mcpServers"], dict):
        raise ConfigError("'mcpServers' must be an object")
    return data


def get_server_config(config: dict[str, Any], server_name: str | None) -> dict[str, Any]:
    if not server_name:
        raise ConfigError("--server is required")
    servers = config.get("mcpServers", {})
    if server_name not in servers:
        raise ConfigError(
            "Server not found in config",
            {"server": server_name, "available": sorted(servers.keys())},
        )
    server_cfg = servers[server_name]
    if not isinstance(server_cfg, dict):
        raise ConfigError("Server config must be an object", {"server": server_name})
    return server_cfg


def normalize_server_config(server_cfg: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(server_cfg)
    if "url" not in normalized and "serverUrl" in normalized:
        normalized["url"] = normalized["serverUrl"]
    if "transport" not in normalized:
        normalized["transport"] = "http"
    if "url" not in normalized:
        raise ConfigError("Server config missing 'url'")
    headers = normalized.get("headers")
    if headers is not None and not isinstance(headers, dict):
        raise ConfigError("'headers' must be an object")
    return normalized


def build_single_server_config(server_name: str, server_cfg: dict[str, Any]) -> dict[str, Any]:
    return {"mcpServers": {server_name: server_cfg}}
