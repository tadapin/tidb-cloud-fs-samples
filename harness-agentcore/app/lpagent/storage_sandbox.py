import posixpath

from strands.sandbox import ExecutionResult, FileInfo, Sandbox
from strands.sandbox.errors import SandboxPathNotFoundError
from strands.storage import Storage


class StorageSandbox(Sandbox):
    """ファイル操作を Storage に向ける Sandbox。コマンドは実行しない。

    エージェントから見える "/" が、Storage の先頭になる。
    """

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    @staticmethod
    def _key(path: str) -> str:
        # "/site/./index.html" と "/site/index.html" を同じキーにする
        return posixpath.normpath("/" + path).lstrip("/")

    async def read_file(self, path, **kwargs):
        data = await self.storage.read(self._key(path))
        if data is None:
            raise SandboxPathNotFoundError(path)
        return data

    async def write_file(self, path, content, **kwargs):
        await self.storage.write(self._key(path), content)

    async def remove_file(self, path, **kwargs):
        await self.storage.delete(self._key(path))

    async def list_files(self, path, **kwargs):
        prefix = self._key(path)
        prefix = f"{prefix}/" if prefix else ""
        entries = {}
        for key in await self.storage.list(prefix):
            name, _, rest = key[len(prefix):].partition("/")
            entries[name] = bool(rest)  # 下にさらにパスが続くならディレクトリ
        return [FileInfo(name=name, is_dir=is_dir) for name, is_dir in sorted(entries.items())]

    async def execute_streaming(self, command, **kwargs):
        # harness は起動時に pwd で作業ディレクトリを調べる。"/" と答え、ほかのコマンドは実行しない
        if command.strip() == "pwd":
            yield ExecutionResult(exit_code=0, stdout="/\n", stderr="")
        else:
            yield ExecutionResult(exit_code=127, stdout="", stderr="commands are not available")

    async def execute_code_streaming(self, code, language, **kwargs):
        yield ExecutionResult(exit_code=127, stdout="", stderr="code execution is not available")
