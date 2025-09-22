import os, io, re, json, base64, zipfile, random
import streamlit as st
from supabase import create_client

# .env ファイルを読み込む

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_api_url(env_url: str = "SUPABASE_URL") -> str | None:
    url = os.getenv(env_url)
    if url:
        return url
    try:
        return st.secrets[env_url]  # secrets.toml が無い場合もあるため例外安全にする
    except Exception:
        return None
    
def get_api_key(env_key: str = "SUPABASE_KEY") -> str | None:
    key = os.getenv(env_key)
    if key:
        return key
    try:
        return st.secrets[env_key]  # secrets.toml が無い場合もあるため例外安全にする
    except Exception:
        return None
    
API_URL = get_api_url()
if not API_URL:
    st.error(
        "APIのURLが見つかりません。\n\n"
         )
    st.stop() 

API_KEY = get_api_key()
if not API_KEY:
    st.error(
        "APIのキーが見つかりません。\n\n"
       )
    st.stop()

# supabaseを呼び出すためのコード
supabase = create_client(API_URL, API_KEY)


# これらはcreate_clientを使うことで呼び出される関数である。
def sign_up(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out():
    supabase.auth.sign_out()
    st.session_state.clear()


def login_signup_page():
    st.title("ログイン / サインアップ")
    tab1,tab2 = st.tabs(["ログイン","サインアップ"])
    
    with tab1:
        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード",type="password",key="login_password")
        if st.button("ログイン"):
            try:
                res = sign_in(email,password)
                st.session_state.user = res.user
                st.success("ログインに成功しました")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"ログインに失敗しました: {str(e)}")

    with tab2:
        new_email = st.text_input("メールアドレス",key="signup_email")
        new_password = st.text_input("パスワード",type="password",key="signup_password")
        if st.button("サインアップ"):
            try:
                res = sign_up(new_email,new_password)
                st.success("アカウントが作成されました。メールを確認してアカウントを有効化してください。")
            except Exception as e:
                st.error(f"サインアップに失敗しました:{str(e)}")


login_signup_page()

