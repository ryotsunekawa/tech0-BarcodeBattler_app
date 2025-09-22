from __future__ import annotations
import os, io, re, json, base64, zipfile, random
from typing import Dict, List, Tuple
import streamlit as st
import streamlit.components.v1 as components

import requests
import time

# .env 読み込み（無ければ何もしない）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_api_key(env_key: str = "STABILITY_API_KEY") -> str | None:
    #環境変数でAPIキーを取得。secretsは存在しない環境でも例外にならないように参照。
    key = os.getenv(env_key)
    if key:
        return key
    try:
        return st.secrets[env_key]
    except Exception:
        return None

API_KEY = get_api_key()
if not API_KEY:
    st.error(
        "APIキーが見つかりません。\n\n"
        "■ 推奨（ローカル学習向け）\n"
        "  1) .env を作成し STABILITY_API_KEY=sk-xxxx を記載\n"
        "  2) このアプリを再実行\n\n"
        "■ 参考（secrets を使う場合）\n"
        "  .streamlit/secrets.toml に STABILITYAPI_KEY を記載（※リポジトリにコミットしない）\n"
        "  公式: st.secrets / secrets.toml の使い方はドキュメント参照"
    )
    st.stop()
    # ノートブック上では停止しません。実アプリでは st.stop() します。


    