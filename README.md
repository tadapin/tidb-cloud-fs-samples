# TiDB Cloud Filesystem samples

Zenn のブログシリーズ「TiDB Cloud Filesystem」で使ったサンプルコードです。
各ディレクトリの README に、対応する記事と実行手順を書いています。

| ディレクトリ | 内容 | 記事 |
|---|---|---|
| — | `ti` コマンドのインストールと TiDB Cloud FS の基本操作（コードなし） | [tiコマンドではじめるTiDB Cloud Filesystem](https://zenn.dev/bohnen/articles/tidb-cloud-fs-ti-cli-tutorial) |
| [`strands-local/`](strands-local/) | 手元の Mac で動く Strands Agents。マウントした TiDB Cloud FS を作業場所にして LP を作る | [Strands AgentsでTiDB Cloud Filesystemを作業場所にする](https://zenn.dev/bohnen/articles/strands-agents-tidb-cloud-fs) |
| [`agentcore/`](agentcore/) | Amazon Bedrock AgentCore Runtime で動くエージェント。`ti fs` で成果物を TiDB Cloud FS に残す。Streamlit のチャット画面つき | [TiDB Cloud FSでStrands Agents/AgentCoreの成果物を永続化する](https://zenn.dev/bohnen/articles/agentcore-tidb-cloud-fs) |
| [`agentcore-memory/`](agentcore-memory/) | 上と同じ構成で、[strands-tidb-filesystem](https://github.com/tadapin/strands-tidb-filesystem) を使って会話と成果物の両方を TiDB Cloud FS に保存する | [Strands Agentsの会話と成果物をTiDB Cloud Filesystemに保存する](https://zenn.dev/bohnen/articles/strands-tidb-filesystem-memory) |

## 共通の前提

- TiDB Cloud FS のファイルシステムと、設定済みの [`ti` コマンド](https://github.com/tidbcloud/ti-cli)
- `/docs/filesystem-intro.md` に、LP の元になるドキュメントを置いておく

```bash
export TI_FS_FILE_SYSTEM_ID=<file-system-id>
curl -sL https://docs.pingcap.com/tidbcloud-filesystem/filesystem-intro.md | \
  ti fs copy-file --from-stdin --to-remote /docs/filesystem-intro.md
```

- Amazon Bedrock の DeepSeek V3.2（`deepseek.v3.2`）を東京リージョン（`ap-northeast-1`）で使います。AWS のプロファイルは環境変数 `AWS_PROFILE` で指定してください。
