from __future__ import annotations

import argparse
from pathlib import Path

from rmcp_client.init_repo import (
    DEFAULT_DEST_NAME,
    format_init_error,
    format_init_summary,
    run_init,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="init")
    parser.add_argument("dest", nargs="?", default=DEFAULT_DEST_NAME)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_init(Path(args.dest))
    except Exception as exc:
        print(format_init_error(exc), end="")
        return 1
    print(format_init_summary(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
