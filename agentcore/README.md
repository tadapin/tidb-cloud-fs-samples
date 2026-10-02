# agentcore

AgentCore Runtime で動くエージェントです。マウントせずに `ti fs` コマンドで TiDB Cloud FS を読み書きし、成果物の LP を残します。会話は microVM のメモリにだけあり、セッションが終わると消えます。

記事：[TiDB Cloud FSでStrands Agents/AgentCoreの成果物を永続化する](https://zenn.dev/bohnen/articles/agentcore-tidb-cloud-fs)

## 構成

- `app/lpagent/`：エージェント（`main.py`）と Dockerfile
- `agentcore/`：AgentCore CLI（`@aws/agentcore`）の設定と CDK プロジェクト
- `ui/app.py`：手元で動かす Streamlit のチャット画面

## デプロイ

1. スコープ付きトークンを作り、Secrets Manager に置きます。

   ```bash
   export TI_FS_FILE_SYSTEM_ID=<file-system-id>
   TOKEN=$(ti fs generate-file-system-scoped-token --ttl 24h \
     --allow /docs:read,list --allow /site:read,list,write \
     --query fs_token --output text)
   aws secretsmanager create-secret --region ap-northeast-1 \
     --name tifslp/ti-fs-token --secret-string "$TOKEN"
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
streamlit run ui/app.py
```

右側のプレビューには、TiDB Cloud FS の `/site/index.html` が表示されます。

## 後片付け

```bash
agentcore remove all -y
agentcore deploy -y
aws logs delete-log-group --log-group-name /aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT
aws secretsmanager delete-secret --secret-id tifslp/ti-fs-token --force-delete-without-recovery
ti fs list-file-system-tokens --file-system-id <file-system-id> --output text
ti fs delete-file-system-token --file-system-id <file-system-id> --token-id <token-id>
```

`agentcore remove all` は `agentcore/agentcore.json` からランタイムの定義を消します。もう一度デプロイするときは、`git checkout agentcore/agentcore.json` で戻してください。
