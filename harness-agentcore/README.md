# harness-agentcore

[`harness-local/`](../harness-local/) の Strands harness のエージェントを、Amazon Bedrock AgentCore Runtime で動かします。
成果物、会話、長期記憶、`AGENTS.md` を TiDB Cloud FS の `/harness` の下に保存するので、セッションが終わって microVM が破棄されても、同じセッション ID で作業を続けられます。
マウントは使いません。

記事：[Strands harnessをAgentCoreで動かし、作業場所をTiDB Cloud Filesystemにする](https://zenn.dev/bohnen/articles/agentcore-strands-harness-tidb-cloud-fs)

## 構成

- `app/lpagent/main.py`：エージェント。`harness-local/lp_agent.py` と同じ `create_harness()` を、リクエストごとに作る
- `app/lpagent/storage_sandbox.py`：`harness-local/` と同じ
- `app/lpagent/Dockerfile`：`ti` コマンドと `git` を追加
- `agentcore/`：AgentCore CLI（`@aws/agentcore`）の設定と CDK プロジェクト

## 準備

ドキュメントを `/harness/workspace/docs/` に置いておきます（[`harness-local/`](../harness-local/) と同じ）。

## デプロイ

1. `/harness` だけを読み書きできるスコープ付きトークンを作り、Secrets Manager に置きます。

   ```bash
   export TI_FS_FILE_SYSTEM_ID=<file-system-id>
   TOKEN=$(ti fs generate-file-system-scoped-token --ttl 24h \
     --allow /harness:read,list,search,write,delete \
     --subject agentcore-harness --query fs_token --output text)
   aws secretsmanager create-secret --region ap-northeast-1 \
     --name tifsharness/ti-fs-token --secret-string "$TOKEN"
   ```

2. `agentcore/aws-targets.json` と `app/lpagent/secrets-policy.json` の `<aws-account-id>` を、自分のアカウント ID に置き換えます。

3. デプロイします。

   ```bash
   npm install -g @aws/agentcore
   export AWS_PROFILE=<your-profile>
   agentcore deploy -y
   ```

## 実行

AgentCore のセッション ID は 33 文字以上です。

```bash
agentcore invoke --session-id lp-session-agentcore-0001-aaaaaaaaaaaa \
  --prompt "当社のブランドカラーは緑で、Webページの文体は「です・ます」調に統一する方針です。この方針を AGENTS.md に書いておいてください。"
agentcore invoke --session-id lp-session-agentcore-0001-aaaaaaaaaaaa \
  --prompt "Webデザイナーとして、docs/filesystem-intro.md を読み、その内容をもとに TiDB Cloud Filesystem を紹介する企業向けの日本語のランディングページを作ってください。CSSを含めたHTML1ファイルで、外部の画像やスクリプトは使わないでください。site/index.html に保存してください。"
```

できた LP は TiDB Cloud FS の `/harness/workspace/site/index.html` に保存されます。

## 後片付け

```bash
agentcore remove all -y
agentcore deploy -y
# Runtime・CodeBuild・Lambda のロググループ（名前にプロジェクト名が入る）
for g in $(aws logs describe-log-groups --region ap-northeast-1 \
    --query "logGroups[?contains(logGroupName, 'tifsharness')].logGroupName" --output text); do
  aws logs delete-log-group --region ap-northeast-1 --log-group-name "$g"
done
aws secretsmanager delete-secret --region ap-northeast-1 \
  --secret-id tifsharness/ti-fs-token --force-delete-without-recovery
ti fs list-file-system-tokens --file-system-id <file-system-id> --output text
ti fs delete-file-system-token --file-system-id <file-system-id> --token-id <token-id>
ti fs delete-file --path /harness --recursive
```
