# AGENTS.md

## 依存パッケージ管理（uv）

### 目的
uv を用いて Python プロジェクトの依存パッケージを追加・更新・削除し、必要に応じて requirements ファイルをエクスポートできるようにする。

### 手順
1. 依存パッケージを追加する。

```powershell
# バージョン上限なしで追加
uv add django djangorestframework

# バージョン範囲を指定して追加
uv add "openai>=1.0.0,<2.0.0" "numpy==2.2.6"

# 開発用パッケージ
uv add --group dev ruff pytest
```

2. 不要になった依存パッケージを削除する。

```powershell
uv remove djangorestframework
uv remove --group dev pytest
```

3. 記載範囲内で依存パッケージをアップデートする。

```powershell
uv sync --upgrade
uv sync --upgrade-package <パッケージ名>
uv add "<パッケージ名>=x.y.z"
```

4. requirements 形式で依存関係をエクスポートする。

```powershell
# 本番用のみ
uv export --no-dev --format requirements.txt --output-file requirements.txt

# 開発用を含める
uv export --format requirements.txt --output-file requirements_with_dev.txt
```

### 注意点
- `uv add` / `uv remove` で `pyproject.toml` が自動更新されるため、差分を確認してからコミットする。
- グループ名の表記ゆれに注意する。
- 依存操作はプロジェクトルートで実行する（手動で仮想環境を有効化する必要はない）。
- 詳細は公式リファレンスを参照する。

