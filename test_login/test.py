import os, io, re, json, base64, zipfile, random
import streamlit as st
from supabase import create_client, AuthApiError

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
    st.header("令和版バーコードバトラー（β版）",divider="red")
    tab1,tab2 = st.tabs(["ログイン","新規会員登録"])
    
    with tab1:
        email = st.text_input("メールアドレス", key="login_email") #session_state.login_emailが使えるようになる。
        password = st.text_input("パスワード",type="password",key="login_password")
        if st.button("ログイン",type="primary"):
            try:
                res = sign_in(email,password)
                user = res.user
                if user :
                    st.session_state.user = user
                    st.session_state.full_name = user.user_metadata.get("full_name", user.email)
                    st.success("ログインに成功しました")
                    st.rerun()
                else:
                    st.error("userを取得できずにログインに失敗しました")
            except Exception as e:
                st.error(f"ログインに失敗しました: {str(e)}")
                
        st.markdown("---")
        st.button("パスワードをお忘れの方はこちら（ダミー）")

    with tab2:
        new_email = st.text_input("メールアドレス",key="signup_email")
        new_password = st.text_input("パスワード",type="password",key="signup_password")
        new_name = st.text_input("名前（任意）",key="signup_name")
        if st.button("サインアップ",type="primary"):
            try:
                response = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password,
                    "options": {
                        "data": {
                            "full_name": new_name
                        }
                    }
                })
                st.success("アカウントが作成されました。メールを確認してください。※登録済みの場合はメールが送信されません。")

            except AuthApiError as e:
                # e.code があれば取得
                code = getattr(e, "code", None)
                message = str(e)
                status = getattr(e, "status_code", None)  # or whatever属性があれば

                st.write("error message:", message)
                st.write("error code property:", code)
                st.write("status code:", status)
            
                if "already" in code:
                    st.error("このメールアドレスはすでに登録済みです。")
                elif "validation" in code:
                   st.error("メールアドレスの書き方不適切です。")
                else:
                    st.error("その他のエラー: " + message)
            


#メイン画面

def main_app():
    # full_name があればそれを、なければ email を表示
    name_to_display = st.session_state.get("full_name", st.session_state.user.email)
    st.subheader(f"{name_to_display} さん、おかえりなさい！")

    tab1,tab2,tab3 = st.tabs(["キャラ生成","図鑑","バトル"])
    
    with tab1:
        scan = st.text_input("スキャン", key="login_email") #session_state.login_emailが使えるようになる。
        todoufuken = st.text_input("都道府県",key="login_password")
        st.button("生成する")
    
    with tab2:
        st.write("cominng soon")

    
    with tab3:
        st.write("cominng soon")



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
