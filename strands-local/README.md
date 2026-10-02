# strands-local

手元の Mac で動く Strands Agents のエージェントです。
TiDB Cloud FS をマウントしたディレクトリを作業場所にして、ドキュメントから LP を作ります。
ファイルの読み書きは [Strands Shell](https://strandsagents.com/docs/user-guide/shell/) 経由にし、マウントしたディレクトリの外には触れないようにしています。

記事：[Strands AgentsでTiDB Cloud Filesystemを作業場所にする](https://zenn.dev/bohnen/articles/strands-agents-tidb-cloud-fs)

```bash
ti fs mount-file-system --mount-path ~/workspace

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export AWS_PROFILE=<your-profile>
python lp_agent.py

ti fs unmount-file-system --mount-path ~/workspace
```

できた LP は TiDB Cloud FS の `/site/index.html` に保存されます。
