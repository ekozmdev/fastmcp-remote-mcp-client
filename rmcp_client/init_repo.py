from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rmcp_client.config import ConfigError

DEFAULT_REPO = "https://github.com/ekozmdev/fastmcp-remote-mcp-client"
DEFAULT_REF = "main"
DEFAULT_DEST_NAME = "fastmcp-remote-mcp-client"
EMBEDDED_GITIGNORE = "**/*\n"
DOWNLOAD_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class InitResult:
    path: Path
    agents_instructions: str
    next_steps: list[str]


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
        with urllib.request.urlopen(
            urllib.request.Request(zip_url, headers={"User-Agent": "rmcp-client/0.1"}),
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        ) as resp, open(target, "wb") as dst:
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


def run_init(dest: Path) -> InitResult:
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

    (dest / ".gitignore").write_text(EMBEDDED_GITIGNORE, encoding="utf-8")
    return InitResult(
        path=dest.resolve(),
        agents_instructions=build_agents_instructions(),
        next_steps=[
            "Append 'agents_instructions' to your project's AGENTS.md (or equivalent)",
            f"cd {dest.resolve()}",
            "uv sync",
        ],
    )


def format_init_summary(result: InitResult) -> str:
    lines = [
        "Repository contents were initialized.",
        f"Path: {result.path}",
        "",
        "The generated folder includes a .gitignore with '**/*',",
        "so you do not need to update your project's .gitignore.",
        "",
        "Add the following to your project's AGENTS.md (or equivalent):",
        "----",
        result.agents_instructions.rstrip(),
        "----",
        "",
        "Next steps:",
    ]
    lines.extend([f"- {step}" for step in result.next_steps])
    return "\n".join(lines) + "\n"


def format_init_error(exc: Exception) -> str:
    if isinstance(exc, ConfigError):
        details = exc.details
        if details:
            return f"Init failed: {exc} ({details})\n"
        return f"Init failed: {exc}\n"
    return f"Init failed: {exc}\n"
