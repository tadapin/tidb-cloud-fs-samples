# harness-local

手元で動く [Strands harness](https://strandsagents.com/docs/user-guide/harness/) のエージェントです。
成果物、会話、長期記憶、退避したツール結果を、すべて TiDB Cloud FS の `/harness` の下に保存します。
マウントは使いません。

- `storage_sandbox.py`：ファイル操作を Strands の `Storage` に向ける `Sandbox`。コマンドは実行しない（`pwd` にだけ `/` と答える）
- `lp_agent.py`：`create_harness()` に、`StorageSandbox` と [strands-tidb-filesystem](https://github.com/tadapin/strands-tidb-filesystem) の `TiDBFilesystemStorage` を渡したエージェント

記事：[Strands harnessの作業場所をTiDB Cloud Filesystemにする](https://zenn.dev/bohnen/articles/strands-harness-tidb-cloud-fs)

## 準備

このサンプルは、ドキュメントを `/harness/workspace/docs/` に置きます（リポジトリ共通の前提の `/docs` とは場所が違います）。

```bash
export TI_FS_FILE_SYSTEM_ID=<file-system-id>
ti fs create-directory --path /harness
ti fs create-directory --path /harness/workspace
ti fs create-directory --path /harness/workspace/docs
curl -sL https://docs.pingcap.com/tidbcloud-filesystem/filesystem-intro.md | \
  ti fs copy-file --from-stdin --to-remote /harness/workspace/docs/filesystem-intro.md
```

モデルは Amazon Bedrock の GLM 5（`zai.glm-5`）を東京リージョンで使います。

## 実行

```bash
export AWS_PROFILE=<your-profile>

# 1回目：方針を AGENTS.md に書かせ、LP を作る
uv run lp_agent.py lp-session-001 \
  "当社のブランドカラーは緑で、Webページの文体は「です・ます」調に統一する方針です。この方針を AGENTS.md に書いておいてください。" \
  "Webデザイナーとして、docs/filesystem-intro.md を読み、その内容をもとに TiDB Cloud Filesystem を紹介する企業向けの日本語のランディングページを作ってください。CSSを含めたHTML1ファイルで、外部の画像やスクリプトは使わないでください。site/index.html に保存してください。"

# 2回目：同じセッションで続ける
uv run lp_agent.py lp-session-001 \
  "さっきLPを作ったときに、あなたが説明したページの特徴を一言でまとめてください。そのうえで、ヒーローの見出しを短く印象的なものに変えてください。"

# 3回目：別のセッション。方針は AGENTS.md から引き継がれる
uv run lp_agent.py lp-session-002 \
  "docs/filesystem-intro.md をもとに、TiDB Cloud Filesystem のよくある質問ページを作り、site/faq.html に保存してください。"
```

## 保存先

| パス | 保存するもの |
|---|---|
| `/harness/workspace/` | 成果物と `AGENTS.md`（エージェントからは `/` に見える） |
| `/harness/session/` | 会話 |
| `/harness/memory/lp-designer/` | 長期記憶 |
| `/harness/context/` | コンテキスト管理で会話から外した内容 |
| `/harness/offloaded/` | 大きなツール結果 |

## 後片付け

```bash
ti fs delete-file --path /harness --recursive
```
