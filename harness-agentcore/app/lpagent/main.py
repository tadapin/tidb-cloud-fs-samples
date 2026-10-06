import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from botocore.config import Config
from strands.memory import ExtractionConfig, ModelExtractor
from strands.models import BedrockModel
from strands.session import SnapshotSessionManager
from strands.vended_memory_stores.file_memory_store import FileMemoryStore
from strands.vended_plugins.context_offloader import ContextOffloader
from strands_harness import create_harness
from strands_tidb_filesystem import TiDBFilesystemStorage

from storage_sandbox import StorageSandbox

app = BedrockAgentCoreApp()

# TiDB Cloud FS のトークンを Secrets Manager から読む（ti は環境変数 TI_FS_TOKEN を使う）
secrets = boto3.client("secretsmanager", region_name="ap-northeast-1")
os.environ["TI_FS_TOKEN"] = secrets.get_secret_value(SecretId=os.environ["TI_FS_TOKEN_SECRET_ID"])["SecretString"]

model = BedrockModel(
    model_id="zai.glm-5",
    region_name="ap-northeast-1",
    boto_client_config=Config(read_timeout=900),
)

# 会話・記憶・退避したツール結果は /harness の下に置く
storage = TiDBFilesystemStorage(prefix="harness/")
# 成果物は /harness/workspace に置く。エージェントからは "/" に見える
workspace = TiDBFilesystemStorage(prefix="harness/workspace/", client=storage.client)


@app.entrypoint
async def invoke(payload, context):
    # 会話・記憶・成果物は TiDB Cloud FS から読むので、Agent はリクエストごとに作ってよい
    agent = create_harness(
        model=model,
        storage=storage,
        # 会話は AgentCore のセッション ID ごとに /harness/session/ に保存する
        session=SnapshotSessionManager(context.session_id, storage=storage),
        memory={
            "stores": [
                FileMemoryStore(
                    name="lp-designer",
                    storage=storage,
                    writable=True,
                    extraction=ExtractionConfig(extractor=ModelExtractor(model=model)),
                )
            ]
        },
        sandbox=StorageSandbox(workspace),
        builtin_tools=["read", "write", "edit"],
        plugins=[
            ContextOffloader(storage=storage.namespace("offloaded"), max_result_tokens=1_500, preview_tokens=750)
        ],
    )
    # async with を抜けるときに、バックグラウンドの記憶の抽出が終わるのを待つ
    async with agent:
        result = await agent.invoke_async(payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
