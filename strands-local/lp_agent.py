import os

import boto3
import strands_shell
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel

# TiDB Cloud FS をマウントしたディレクトリ
WORKSPACE = os.path.expanduser(os.environ.get("WORKSPACE", "~/workspace"))

# シェルから見えるのは、マウントしたディレクトリ（/workspace）だけにする
BINDS = [strands_shell.Bind(WORKSPACE, "/workspace", mode="direct")]


def _path(path: str) -> str:
    return "/workspace/" + path.lstrip("/")


@tool
def read_file(path: str) -> str:
    """ワークスペース内のファイルを読みます。path はワークスペースからの相対パスです。"""
    # Shell は作ったスレッドでしか使えないため、呼び出しごとに作る
    shell = strands_shell.Shell(binds=BINDS)
    return shell.read_file(_path(path)).decode("utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """ワークスペース内にファイルを書きます。path はワークスペースからの相対パスです。"""
    shell = strands_shell.Shell(binds=BINDS)
    shell.write_file(_path(path), content.encode("utf-8"))
    return f"wrote {len(content)} chars to {path}"


model = BedrockModel(
    model_id="deepseek.v3.2",
    # AWS のプロファイルは環境変数 AWS_PROFILE で指定する
    boto_session=boto3.Session(region_name="ap-northeast-1"),
    boto_client_config=Config(read_timeout=900),
    max_tokens=16000,
)

agent = Agent(
    model=model,
    tools=[read_file, write_file],
    system_prompt="あなたはWebデザイナーです。ファイルの読み書きには必ずツールを使います。",
)

agent(
    "docs/filesystem-intro.md を読み、その内容をもとに TiDB Cloud Filesystem を紹介する"
    "企業向けの日本語のランディングページを作ってください。"
    "CSSを含めたHTML1ファイルで、外部の画像やスクリプトは使わないでください。"
    "site/index.html に保存してください。"
)
