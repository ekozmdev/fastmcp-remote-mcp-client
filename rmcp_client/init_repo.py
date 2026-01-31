from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from rmcp_client.config import ConfigError

DEFAULT_REPO = "https://github.com/ekozmdev/fastmcp-remote-mcp-client"
DEFAULT_REF = "main"


def build_repo_zip_url(repo_url: str, ref: str) -> str:
    trimmed = repo_url.rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[: -len(".git")]
    return f"{trimmed}/archive/refs/heads/{ref}.zip"


def ensure_empty_dir(dest: Path) -> None:
    if dest.exists():
        if not dest.is_dir():
            raise ConfigError("Destination exists and is not a directory", {"path": str(dest)})
        if any(dest.iterdir()):
            raise ConfigError("Destination directory is not empty", {"path": str(dest)})
    else:
        dest.mkdir(parents=True, exist_ok=True)


def safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            member_path = (dest / member.filename).resolve()
            if not member_path.is_relative_to(dest.resolve()):
                raise ConfigError("Archive contains invalid paths")
            if member.is_dir():
                (dest / member.filename).mkdir(parents=True, exist_ok=True)
            else:
                (dest / member.filename).parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(dest / member.filename, "wb") as dst:
                    shutil.copyfileobj(src, dst)


def download_repo_zip(repo_url: str, ref: str, target: Path) -> None:
    zip_url = build_repo_zip_url(repo_url, ref)
    try:
        with urllib.request.urlopen(zip_url) as resp, open(target, "wb") as dst:
            shutil.copyfileobj(resp, dst)
    except Exception as exc:
        raise ConfigError("Failed to download repository archive", {"url": zip_url}) from exc


def build_agents_instructions() -> str:
    return (
        "リモートMCPはこのCLIを介して呼び出すこと。\n"
        "コマンドは毎回ワンショットで実行し、標準出力のJSONのみを解析する。\n"
        "このCLIは専用リポジトリ内で実行するため、必ずツールのフォルダへ移動してから uv run する。\n\n"
        "使い方:\n"
        "- ツール一覧:\n"
        "  cd <path/to/fastmcp-remote-mcp-client>\n"
        "  uv run python -m rmcp_client.cli list-tools --server <server-name>\n"
        "- ツール呼び出し:\n"
        "  cd <path/to/fastmcp-remote-mcp-client>\n"
        "  uv run python -m rmcp_client.cli call-tool --server <server-name> --tool <tool-name> --args '<json-object>'\n\n"
        "注意:\n"
        "- --server は必須\n"
        "- --args は必ずJSONオブジェクト\n"
        "- エラーも標準出力にJSONで返る\n"
    )


def run_init(dest: Path) -> dict[str, Any]:
    ensure_empty_dir(dest)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "repo.zip"
        extract_path = tmp_path / "extract"
        extract_path.mkdir(parents=True, exist_ok=True)

        download_repo_zip(DEFAULT_REPO, DEFAULT_REF, zip_path)
        safe_extract(zip_path, extract_path)

        roots = [p for p in extract_path.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise ConfigError("Unexpected archive structure")
        root = roots[0]
        for item in root.iterdir():
            shutil.move(str(item), dest / item.name)

    ignore_entry = f"{dest.resolve().name}/"
    return {
        "ok": True,
        "result": {
            "message": "Repository contents were initialized.",
            "path": str(dest.resolve()),
            "gitignore_entry": ignore_entry,
            "agents_instructions": build_agents_instructions(),
            "next_steps": [
                f"Add '{ignore_entry}' to your project's .gitignore",
                "Append 'agents_instructions' to your project's AGENTS.md (or equivalent)",
                f"cd {dest.resolve()}",
                "uv sync",
            ],
        },
    }
