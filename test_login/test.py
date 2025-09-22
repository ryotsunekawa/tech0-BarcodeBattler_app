import os, io, re, json, base64, zipfile, random
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client

# .env ファイルを読み込む
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# supabaseを呼び出すためのコード
supabase = create_client(url, key)


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

