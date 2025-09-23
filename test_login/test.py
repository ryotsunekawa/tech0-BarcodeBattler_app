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
    st.title("ログイン / サインアップ（β版）")
    tab1,tab2 = st.tabs(["ログイン","サインアップ"])
    
    with tab1:
        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード",type="password",key="login_password")
        if st.button("ログイン"):
            try:
                res = sign_in(email,password)
                st.session_state.user = res.user
                st.success("ログインに成功しました")
                st.rerun()



            except Exception as e:
                st.error(f"ログインに失敗しました: {str(e)}")

    with tab2:
        new_email = st.text_input("メールアドレス",key="signup_email")
        new_password = st.text_input("パスワード",type="password",key="signup_password")
        if st.button("サインアップ"):
            res = sign_up(new_email, new_password)

                
            try:
                res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                st.success("アカウントが作成されました。メールを確認して有効化してください。")
            except Exception as e:
                error_msg = str(e)
                if "already registered" in error_msg.lower():
                    st.error("このメールアドレスはすでに登録済みです。")
                else:
                    st.error(f"サインアップに失敗しました: {error_msg}")



#メイン画面

def main_app():
    st.title("メインアプリケーション")
    st.write(f"ようこそ、{st.session_state.user.email}さん！")

    menu = ["ホーム", "コンテンツ",]
    choice = st.sidebar.selectbox("メニュー", menu)

    if choice == "ホーム":
        st.subheader("ホーム")
        st.write("ホームです。")

    elif choice == "コンテンツ":
        st.subheader("コンテンツ")
        st.write("ここにコンテンツを表示できます。")


    if st.sidebar.button("ログアウト"):
        sign_out()
        st.rerun()

#　アプリケーション全体の流れを制御する

#check_auth()はsession_stateにuserと言うキーが登録されているかの確認。

def check_auth():
    return 'user' in st.session_state

#mainとは 起動時にcheckがFalseであればlogin_signup_pageを起動し、Trueでればmain_appを起動すること。

def main():
    if not check_auth():
        login_signup_page()
    else:
        main_app()


#__name__はpythonファイルが実行されるときに自動で設定される。
#また、直接実行されたとき、__name__は"__main__"になる。（他ファイルからインポートされた場合は）
if __name__ == "__main__":
    main()
