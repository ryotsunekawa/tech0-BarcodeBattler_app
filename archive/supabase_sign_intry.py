import os 
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(url, key)

def sign_up(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out():
    supabase.auth.sign_out()
    st.session_state.clear()

def login_sign_page():
    st.title("ログイン / サインアップ")
    tab1, tab2 = st.tabs(["ログイン", "サインアップ"])

    with tab1:
        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード", type="password", key="login_password")
        if st.button("ログイン"):
            try:
                res = sign_in(email, password)
                st.session_state.user = res.user
                st.success("ログイン成功")
            except Exception as e:
                st.error(f"ログイン失敗: {e}")

    with tab2:
        new_email = st.text_input("メールアドレス", key="signup_email")
        new_password = st.text_input("パスワード", type="password", key="signup_password")
        if st.button("サインアップ"):
            try:
                res = sign_up(new_email, new_password)
                st.success("アカウントが作成されました。メールを核にしてアカウントを有効化してください。")
            except Exception as e:
                st.error(f"サインアップ失敗しました: {e}")

# メイン実行部分
if __name__ == "__main__":
    login_sign_page()