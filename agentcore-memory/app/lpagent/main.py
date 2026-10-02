import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
from strands.session import SnapshotSessionManager
from strands_tidb_filesystem import TiDBFilesystemStorage

app = BedrockAgentCoreApp()

# TiDB Cloud FS のトークンを Secrets Manager から読む（ti は環境変数 TI_FS_TOKEN を使う）
secrets = boto3.client("secretsmanager", region_name="ap-northeast-1")
os.environ["TI_FS_TOKEN"] = secrets.get_secret_value(SecretId=os.environ["TI_FS_TOKEN_SECRET_ID"])["SecretString"]

# 会話・メモリは /agents、成果物は /agents/site、元のドキュメントは /docs に置く
storage = TiDBFilesystemStorage(prefix="agents/")
site = storage.namespace("site")
docs = TiDBFilesystemStorage(prefix="docs/", client=storage.client)


@tool
async def read_doc(path: str) -> str:
    """元のドキュメントを読みます。path は docs からの相対パスです（例: filesystem-intro.md）。"""
    data = await docs.read(path)
    return data.decode() if data is not None else f"{path} は見つかりません"


@tool
async def read_file(path: str) -> str:
    """成果物のファイルを読みます。path は site からの相対パスです（例: index.html）。"""
    data = await site.read(path)
    return data.decode() if data is not None else f"{path} は見つかりません"


@tool
async def write_file(path: str, content: str) -> str:
    """成果物のファイルを書きます。path は site からの相対パスです（例: index.html）。"""
    await site.write(path, content.encode())
    return f"wrote {len(content)} chars to {path}"


SYSTEM_PROMPT = """あなたはWebデザイナーです。ファイルの読み書きには必ずツールを使います。
ドキュメント filesystem-intro.md の内容をもとに、TiDB Cloud Filesystem を紹介するランディングページを作ります。
ページはCSSを含めたHTML1ファイルで、外部の画像やスクリプトは使わず、index.html に保存します。
修正を頼まれたときは、index.html を読んでから、指示に合わせて書き直します。"""

model = BedrockModel(
    model_id="deepseek.v3.2",
    region_name="ap-northeast-1",
    boto_client_config=Config(read_timeout=900),
    max_tokens=16000,
)


@app.entrypoint
async def invoke(payload, context):
    # 会話は TiDB Cloud FS から復元されるので、Agent はリクエストごとに作ってよい
    agent = Agent(
        model=model,
        tools=[read_doc, read_file, write_file],
        system_prompt=SYSTEM_PROMPT,
        storage=storage,
        session_manager=SnapshotSessionManager(context.session_id),
    )
    result = await agent.invoke_async(payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
