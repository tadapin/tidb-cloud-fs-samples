import asyncio
import sys
import time

from botocore.config import Config
from strands.memory import ExtractionConfig, ModelExtractor
from strands.models import BedrockModel
from strands.session import SnapshotSessionManager
from strands.vended_memory_stores.file_memory_store import FileMemoryStore
from strands.vended_plugins.context_offloader import ContextOffloader
from strands_harness import create_harness
from strands_tidb_filesystem import TiDBFilesystemStorage

from storage_sandbox import StorageSandbox

model = BedrockModel(
    model_id="zai.glm-5",
    region_name="ap-northeast-1",
    boto_client_config=Config(read_timeout=900),
)

# 会話・記憶・退避したツール結果は /harness の下に置く
storage = TiDBFilesystemStorage(prefix="harness/")
# 成果物は /harness/workspace に置く。エージェントからは "/" に見える
workspace = TiDBFilesystemStorage(prefix="harness/workspace/", client=storage.client)


async def main(session_id: str, prompts: list[str]) -> None:
    # 記憶は /harness/memory/lp-designer/ に保存する。抽出に使うモデルは自分で指定する
    memory_store = FileMemoryStore(
        name="lp-designer",
        storage=storage,
        writable=True,
        extraction=ExtractionConfig(extractor=ModelExtractor(model=model)),
    )
    agent = create_harness(
        model=model,
        storage=storage,
        # 会話は呼び出しごとに1回だけ /harness/session/ に保存する
        session=SnapshotSessionManager(session_id, storage=storage),
        memory={"stores": [memory_store]},
        # ファイル操作は TiDB Cloud FS に向ける。コマンドは実行しないので shell は外す
        sandbox=StorageSandbox(workspace),
        builtin_tools=["read", "write", "edit"],
        # 大きなツール結果の退避先。指定しないと、手元の一時ディレクトリを sandbox 経由で書く
        plugins=[
            ContextOffloader(storage=storage.namespace("offloaded"), max_result_tokens=1_500, preview_tokens=750)
        ],
    )
    # async with を抜けるときに、バックグラウンドの記憶の抽出が終わるのを待つ
    async with agent:
        for prompt in prompts:
            start = time.time()
            result = await agent.invoke_async(prompt)
            print(f"\n=== [{time.time() - start:.1f}s] {prompt}\n{result}\n")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
