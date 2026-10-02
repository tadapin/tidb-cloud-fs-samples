import os
import subprocess

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

# TiDB Cloud FS のトークンを Secrets Manager から読み、ti コマンドに環境変数で渡す
secrets = boto3.client("secretsmanager", region_name="ap-northeast-1")
os.environ["TI_FS_TOKEN"] = secrets.get_secret_value(SecretId=os.environ["TI_FS_TOKEN_SECRET_ID"])["SecretString"]


def ti(*args: str, stdin: str | None = None) -> str:
    """ti コマンドを実行します。認証には環境変数 TI_FS_TOKEN と TI_REGION_CODE を使います。"""
    r = subprocess.run(["ti", *args], input=stdin, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


@tool
def read_file(path: str) -> str:
    """TiDB Cloud FS のファイルを読みます。path は / から始まるパスです。"""
    return ti("fs", "read-file", "--path", path)


@tool
def write_file(path: str, content: str) -> str:
    """TiDB Cloud FS にファイルを書きます。path は / から始まるパスです。"""
    ti("fs", "copy-file", "--from-stdin", "--to-remote", path, "--overwrite", stdin=content)
    return f"wrote {len(content)} chars to {path}"


model = BedrockModel(
    model_id="deepseek.v3.2",
    region_name="ap-northeast-1",
    boto_client_config=Config(read_timeout=900),
    max_tokens=16000,
)


SYSTEM_PROMPT = """あなたはWebデザイナーです。ファイルの読み書きには必ずツールを使います。
/docs/filesystem-intro.md の内容をもとに、TiDB Cloud Filesystem を紹介するランディングページを作ります。
ページはCSSを含めたHTML1ファイルで、外部の画像やスクリプトは使わず、/site/index.html に保存します。
修正を頼まれたときは、/site/index.html を読んでから、指示に合わせて書き直します。"""

# セッションごとに Agent を持ち、会話を覚えさせる（同じセッションは同じ microVM に届く）
agents: dict[str, Agent] = {}


@app.entrypoint
def invoke(payload, context):
    if context.session_id not in agents:
        agents[context.session_id] = Agent(model=model, tools=[read_file, write_file], system_prompt=SYSTEM_PROMPT)
    result = agents[context.session_id](payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
