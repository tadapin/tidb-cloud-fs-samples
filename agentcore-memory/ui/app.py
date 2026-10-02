import base64
import json
import os
import subprocess
import uuid

import boto3
import streamlit as st
from botocore.config import Config

RUNTIME_ARN = os.environ["AGENT_RUNTIME_ARN"]
client = boto3.client("bedrock-agentcore", region_name="ap-northeast-1", config=Config(read_timeout=900))

st.set_page_config(page_title="LP エージェント", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# AgentCore のセッション ID（33文字以上）。同じ ID を入れれば、別の日でも会話を再開できる
with st.sidebar:
    session_id = st.text_input("セッション ID", value=st.session_state.setdefault("default_id", str(uuid.uuid4())))


def ask_agent(prompt: str) -> str:
    """AgentCore のエージェントを呼び出します。同じセッション ID なら会話が続きます。"""
    res = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt}),
    )
    return json.loads(res["response"].read())["response"]


def read_site() -> str | None:
    """TiDB Cloud FS から /agents/site/index.html を読みます。"""
    r = subprocess.run(["ti", "fs", "read-file", "--path", "/agents/site/index.html"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


chat, preview = st.columns([2, 3])

with chat:
    st.subheader("チャット")
    history = st.container(height=640)  # 履歴はこの枠の中でスクロールする
    for m in st.session_state.messages:
        history.chat_message(m["role"]).write(m["content"])
    if prompt := st.chat_input("例：企業向けのLPを作って / 配色を落ち着いたトーンにして"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        history.chat_message("user").write(prompt)
        with history, st.spinner("エージェントが作業中です（数分かかります）"):
            answer = ask_agent(prompt)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

with preview:
    st.subheader("TiDB Cloud FS の /agents/site/index.html")
    html = read_site()
    if html:
        # LLM が書いた HTML なので、data: URL にして Streamlit とは別のオリジンで表示する
        src = "data:text/html;base64," + base64.b64encode(html.encode()).decode()
        st.iframe(src, height=700)
    else:
        st.info("まだページはありません。")
