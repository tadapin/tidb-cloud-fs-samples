# agentcore-memory

`agentcore/` と同じ構成で、[strands-tidb-filesystem](https://github.com/tadapin/strands-tidb-filesystem) を使います。会話（`SnapshotSessionManager`）と成果物の両方を TiDB Cloud FS に保存するので、セッションが終わっても、同じセッション ID で会話を続けられます。

記事：[Strands Agentsの会話と成果物をTiDB Cloud Filesystemに保存する](https://zenn.dev/bohnen/articles/strands-tidb-filesystem-memory)

## 構成

- `app/lpagent/`：エージェント（`main.py`）と Dockerfile
- `agentcore/`：AgentCore CLI（`@aws/agentcore`）の設定と CDK プロジェクト
- `ui/app.py`：手元で動かす Streamlit のチャット画面

## デプロイ

1. スコープ付きトークンを作り、Secrets Manager に置きます。

   ```bash
   export TI_FS_FILE_SYSTEM_ID=<file-system-id>
   TOKEN=$(ti fs generate-file-system-scoped-token --ttl 24h \
     --allow /agents:read,list,search,write,delete --allow /docs:read,list \
     --query fs_token --output text)
   aws secretsmanager create-secret --region ap-northeast-1 \
     --name tifsmem/ti-fs-token --secret-string "$TOKEN"
   ```

2. `agentcore/aws-targets.json` と `app/lpagent/secrets-policy.json` の `<aws-account-id>` を、自分のアカウント ID に置き換えます。

3. デプロイします。

   ```bash
   npm install -g @aws/agentcore
   export AWS_PROFILE=<your-profile>
   agentcore deploy -y
   ```

## チャット画面

```bash
pip install streamlit boto3
export TI_FS_FILE_SYSTEM_ID=<file-system-id>
export AGENT_RUNTIME_ARN=<runtime-arn>   # agentcore deploy の出力の RuntimeArn
streamlit run ui/app.py --server.address localhost
```

`--server.address localhost` を付けて、手元の PC からだけ開けるようにしてください。
Streamlit は既定でネットワーク全体に公開され、画面には認証がありません。
同じネットワークの人が、あなたの AWS 認証情報でエージェントを呼び出せてしまいます。

右側のプレビューには、TiDB Cloud FS の `/agents/site/index.html` が表示されます。

## 複数のユーザーで使う場合

会話は `/agents/session/<セッションID>/` に保存され、トークンは `/agents` 全体を読み書きできます。
同じランタイムを複数のユーザーで使う場合は、ユーザーごとに `TiDBFilesystemStorage` の `prefix`（例：`agents/<user-id>/`）とトークンのスコープを分けてください。

## 後片付け

```bash
agentcore remove all -y
agentcore deploy -y
aws logs delete-log-group --log-group-name /aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT
aws secretsmanager delete-secret --secret-id tifsmem/ti-fs-token --force-delete-without-recovery
ti fs list-file-system-tokens --file-system-id <file-system-id> --output text
ti fs delete-file-system-token --file-system-id <file-system-id> --token-id <token-id>
```

`agentcore remove all` は `agentcore/agentcore.json` からランタイムの定義を消します。もう一度デプロイするときは、`git checkout agentcore/agentcore.json` で戻してください。
