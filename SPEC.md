# Remote MCP CLI Client (FastMCP) 仕様書

## 目的
- リモートMCPに直接接続できないAIエージェントから、CLIを介してワンショットでMCPツールを呼び出せるようにする。
- 1コマンド=1セッションで完結し、標準出力にJSONを返す。

## ゴール
- FastMCPの `Client` を用いてリモートMCPに接続し、`list_tools` と `call_tool` を実行できる。
- 設定は `mcp_servers.json` のみ（CLIでURLやヘッダーは指定しない）。
- 人間向け整形は行わず、標準出力はJSONのみ。

## 非ゴール
- 常駐プロセス/セッション維持
- 複数MCPサーバー同時利用の統合（設定ファイルには複数定義可能だが、CLIは単一サーバーを選択して使う）
- 対話UI/REPL

## CLI仕様
### コマンド
- `list-tools`
  - 指定サーバーのツール一覧取得
- `call-tool`
  - 指定ツールを引数付きで実行
- `init`
  - このリポジトリの内容を指定ディレクトリに展開

### 引数
- 共通
  - `--server <name>`: `mcp_servers.json` のキー名（省略時はエラー）
- `call-tool` 追加
  - `--tool <name>`: 実行するツール名
  - `--args <json>`: ツール引数（JSON文字列、指定なしなら `{}`）
- `init` 追加
  - `<dest>`: 展開先ディレクトリ（省略時は `.`）
  - 展開先は空ディレクトリであること（非空ならエラー）

### 出力(JSON)
- 成功:
  ```json
  {"ok": true, "result": <tool_result_or_tools>}
  ```
- 失敗:
  ```json
  {"ok": false, "error": {"type": "...", "message": "...", "details": "... or {...}"}}
  ```
- 標準出力のみ（stderrは使わない）
- 終了コード: 成功=0 / 失敗=1
- JSONはUTF-8で出力し、非ASCII文字をエスケープしない

### `list-tools` の結果形式
- 返却するツール一覧はJSONシリアライズ可能な辞書配列に正規化する。
- 最低限 `name` を含み、可能なら `description` と `inputSchema` を含める。

### `init` の結果形式
- `result` に以下を含める。
  - `path`: 展開先の絶対パス
  - `gitignore_entry`: 追加推奨の `.gitignore` エントリ
  - `agents_instructions`: AIエージェント指示ファイルに追記するテキスト

## セッション/接続
- 1コマンドにつき `Client` を生成し、完了後にクローズする。
- 1回のCLI実行でセッションを作成して破棄する（ステート保持なし）。

## 設定ファイル仕様（mcp_servers.json）
### 位置
- 設定ファイルのパスは固定で `mcp_servers.json` を参照する。

### 形式
```json
{
  "mcpServers": {
    "deepwiki": {
      "transport": "http",
      "url": "https://mcp.deepwiki.com/mcp"
    }
  }
}
```

### ルール
- ルートキーは `mcpServers` のみ利用。
- サーバー定義には `url` と `transport` を持つ（`transport` 未指定なら `http` を既定）。
- `headers` が必要な場合はサーバー定義に `headers` を追加する。
- `serverUrl` が与えられた場合は `url` に正規化して扱う。

## モジュール構成（予定）
- `rmcp_client/config.py`
  - 設定読み込み、検証、正規化
- `rmcp_client/cli.py`
  - CLI引数解析、`Client` 経由の実行、JSON出力
- `rmcp_client/__init__.py`

## 動作例
```bash
python -m rmcp_client.cli list-tools --server deepwiki
python -m rmcp_client.cli call-tool --server deepwiki --tool ask_question --args '{"repoName":"vercel/ai","question":"目的を要約して"}'
```

## テスト/検証
- 公開MCP(DeepWiki)での疎通確認を行う。
- `list-tools` で `ask_question` 等が取得できること。
- `call-tool` でJSONレスポンスが得られること。
