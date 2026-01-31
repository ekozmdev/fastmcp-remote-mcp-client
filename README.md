# Remote MCP CLI Client (FastMCP)

リモートMCPに対応していないAIエージェントから、CLI経由でワンショット実行するためのクライアントです。

## セットアップ

### このリポジトリ単体で使う場合

```bash
uv sync
```

### 他の開発フォルダで使う場合（推奨）

1) 開発フォルダにこのリポジトリをクローン  
2) 開発フォルダの `.gitignore` にクローンしたフォルダ名を追加  
3) このリポジトリ内で `uv sync` を実行  

例:
```bash
git clone <this-repo> rmcp-client
echo "rmcp-client/" >> .gitignore
cd rmcp-client
uv sync
```

## 設定ファイル

`mcp_servers.json` をプロジェクトルートに置き、接続先を定義します。

```json
{
  "mcpServers": {
    "deepwiki": {
      "transport": "http",
      "url": "https://mcp.deepwiki.com/mcp"
    },
    "microsoft-learn": {
      "transport": "http",
      "url": "https://learn.microsoft.com/api/mcp"
    },
    "aws-knowledge": {
      "transport": "http",
      "url": "https://knowledge-mcp.global.api.aws"
    },
    "context7": {
      "transport": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

※ Context7 はAPIキーなしでも動作確認していますが、利用制限がある可能性があります。

## 使い方

### ツール一覧

```bash
python -m rmcp_client.cli list-tools --server deepwiki
```

### ツール実行

```bash
python -m rmcp_client.cli call-tool \
  --server deepwiki \
  --tool ask_question \
  --args '{"repoName":"vercel/ai","question":"目的を要約して"}'
```

## 動作確認済み（2026-01-31）

- DeepWiki: `list-tools` / `call-tool`（`ask_question`）
- Microsoft Learn: `list-tools` / `call-tool`（`microsoft_docs_search`）
- AWS Knowledge MCP: `list-tools` / `call-tool`（`aws___search_documentation`）
- Context7: `list-tools` / `call-tool`（`resolve-library-id`, `query-docs`）

## 出力仕様

- 標準出力はJSONのみ。
- 失敗時も標準出力へJSONを返し、終了コードは `1`。
- JSONはUTF-8で出力し、非ASCIIはエスケープしません。

## CLI仕様（抜粋）

- `--server` は必須
- 設定ファイルは `mcp_servers.json` 固定
- `call-tool` の `--args` はJSONオブジェクトのみ

## AIエージェント向けインストラクション（貼り付け用）

以下を、開発で使うAIエージェントのインストラクションファイルに追加してください。

```text
リモートMCPはこのCLIを介して呼び出すこと。
コマンドは毎回ワンショットで実行し、標準出力のJSONのみを解析する。
このCLIは専用リポジトリ内で実行するため、必ずツールのフォルダへ移動してから `uv run` する。

使い方:
- ツール一覧:
  cd <path/to/fastmcp-remote-mcp-client>
  uv run python -m rmcp_client.cli list-tools --server <server-name>
- ツール呼び出し:
  cd <path/to/fastmcp-remote-mcp-client>
  uv run python -m rmcp_client.cli call-tool --server <server-name> --tool <tool-name> --args '<json-object>'

注意:
- --server は必須
- --args は必ずJSONオブジェクト
- エラーも標準出力にJSONで返る
```
