# =============================================================================
# バーコードバトラー認証システム
# ベース: login.py の認証機能を既存DBスキーマ（users, user_operations）に対応
# =============================================================================

import os
import streamlit as st
from supabase import create_client, Client, AuthApiError
from dotenv import load_dotenv
import uuid
from datetime import datetime

# 環境変数を読み込み（login.pyから継承）
load_dotenv()

class BarcodeBattlerAuth:
    """
    バーコードバトラー用認証システム
    
    【login.pyベース】認証機能の基本構造を継承：松井
    【修正点】既存DBスキーマ（users, user_operations）に対応：松井
    """
    
    def __init__(self):
        """
        初期化
        
        【login.pyベース】get_secret_or_env関数の機能を統合：松井
        【修正点】環境変数名をSUPABASE_ANON_KEYに統一：松井
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")  # 【修正】login.pyのSUPABASE_KEYから変更：松井
        
        if not self.supabase_url or not self.supabase_anon_key:
            st.error("Supabase設定が見つかりません。.envファイルを確認してください。")
            st.stop()
            
        # 【login.pyベース】create_client呼び出し
        self.supabase: Client = create_client(self.supabase_url, self.supabase_anon_key)
        
        # 【login.pyベース】セッション状態の初期化
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
    
    def sign_up(self, email: str, password: str, full_name: str):
        """
        新規ユーザー登録
        
        【login.pyベース】sign_up関数の基本機能を継承：松井
        【修正点】既存usersテーブル（mail_address, user_name, location）に対応：松井
        
        Args:
            email: メールアドレス
            password: パスワード
            full_name: ユーザー名
            
        Returns:
            dict: 登録結果
        """
        try:
            # 【login.pyベース】Supabase Authで認証ユーザー作成
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name  # 【login.pyベース】full_nameをmetadataに保存
                    }
                }
            })
            
            if response.user:
                # 【修正点】usersテーブルにユーザー情報を登録（既存DBスキーマに対応）：松井
                # テーブル構造: user_id, mail_address, user_name
                
                # Option 1: Python側でUUID生成（現在の方法）
                user_data = {
                    "user_id": str(uuid.uuid4()),           # 【修正】UUIDで自動生成：松井
                    "user_name": full_name,                 # 【修正】ユーザー名：松井
                    "mail_address": email                   # 【修正】メールアドレス：松井
                }
                
                # Option 2: PostgreSQL側で自動生成（user_idを省略）
                # user_data = {
                #     "user_name": full_name,
                #     "mail_address": email
                # }
                
                # usersテーブルに挿入
                db_result = self.supabase.table('users').insert(user_data).execute()
                
                if db_result.data:
                    return {
                        "success": True,
                        "message": "アカウントが作成されました。メールを確認してください。",
                        "user": response.user,
                        "user_data": db_result.data[0]
                    }
                else:
                    # 認証は成功したがDBエラーの場合
                    return {
                        "success": False,
                        "message": "アカウント作成中にエラーが発生しました。再度お試しください。",
                        "error": "Database insertion failed"
                    }
            else:
                return {
                    "success": False,
                    "message": "アカウント作成に失敗しました。",
                    "error": "Auth user creation failed"
                }
                
        except AuthApiError as e:
            error_message = self._handle_auth_error(e)
            return {
                "success": False,
                "message": error_message,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"予期しないエラーが発生しました: {str(e)}",
                "error": str(e)
            }
    
    def sign_in(self, email: str, password: str):
        """
        ログイン処理
        
        【login.pyベース】sign_in関数の基本機能を継承：松井
        【修正点】既存ユーザーとの連携機能を追加：松井
        
        Args:
            email: メールアドレス
            password: パスワード
            
        Returns:
            dict: ログイン結果
        """
        try:
            # 【login.pyベース】Supabase Authでログイン
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # 2. usersテーブルからユーザー情報を取得
                # 【一時的修正】auth_user_idカラム追加まではmail_addressで検索：松井
                # user_data = self.supabase.table('users').select('*').eq('auth_user_id', response.user.id).execute()
                user_data = self.supabase.table('users').select('*').eq('mail_address', email).execute()
                
                # 【一時的コメントアウト】auth_user_idカラム追加後に有効化予定：松井
                # if not user_data.data:
                #     # auth_user_idが設定されていない既存ユーザーの場合、mail_addressで検索
                #     user_data = self.supabase.table('users').select('*').eq('mail_address', email).execute()
                #     
                #     if user_data.data:
                #         # auth_user_idを更新（既存ユーザーとSupabase認証を紐付け）
                #         self.supabase.table('users').update({
                #             "auth_user_id": response.user.id
                #         }).eq('user_id', user_data.data[0]['user_id']).execute()
                
                if user_data.data:
                    # セッション状態を更新
                    st.session_state.user = response.user
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data.data[0]
                    st.session_state.full_name = user_data.data[0]['user_name']
                    st.session_state.user_id = user_data.data[0]['user_id']  # 既存DBのuser_idを保持
                    
                    return {
                        "success": True,
                        "message": "ログインに成功しました",
                        "user": response.user,
                        "user_data": user_data.data[0]
                    }
                else:
                    return {
                        "success": False,
                        "message": "ユーザーデータが見つかりません。",
                        "error": "User data not found in database"
                    }
            else:
                return {
                    "success": False,
                    "message": "ログインに失敗しました。",
                    "error": "Authentication failed"
                }
                
        except AuthApiError as e:
            error_message = self._handle_auth_error(e)
            return {
                "success": False,
                "message": error_message,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"ログインエラー: {str(e)}",
                "error": str(e)
            }
    
    def sign_out(self):
        """ログアウト処理"""
        try:
            self.supabase.auth.sign_out()
            # セッション状態をクリア
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            return {"success": True, "message": "ログアウトしました"}
        except Exception as e:
            return {"success": False, "message": f"ログアウトエラー: {str(e)}"}
    
    def _handle_auth_error(self, error: AuthApiError):
        """認証エラーのハンドリング"""
        error_msg = str(error).lower()
        
        if "already" in error_msg or "registered" in error_msg:
            return "このメールアドレスは既に登録済みです。"
        elif "invalid" in error_msg and "email" in error_msg:
            return "メールアドレスの形式が正しくありません。"
        elif "password" in error_msg and ("weak" in error_msg or "short" in error_msg):
            return "パスワードは6文字以上で設定してください。"
        elif "invalid" in error_msg and ("credentials" in error_msg or "login" in error_msg):
            return "メールアドレスまたはパスワードが正しくありません。"
        else:
            return f"認証エラー: {str(error)}"
    
    def is_authenticated(self):
        """認証状態の確認"""
        return st.session_state.get('authenticated', False) and st.session_state.get('user') is not None


def main():
    """メイン認証画面"""
    st.set_page_config(
        page_title="バーコードバトラー - ログイン",
        page_icon="📱",
        layout="centered"
    )
    
    # 認証システム初期化
    auth = BarcodeBattlerAuth()
    
    # 認証済みの場合はメイン画面へリダイレクト
    if auth.is_authenticated():
        st.success(f"ログイン済み: {st.session_state.full_name}さん")
        if st.button("メイン画面へ"):
            # 将来的にメイン画面にリダイレクト
            st.info("メイン画面への遷移機能は今後実装予定です")
        if st.button("ログアウト"):
            result = auth.sign_out()
            if result["success"]:
                st.success(result["message"])
                st.rerun()
        return
    
    # ログイン・登録画面
    st.header("🎮 令和版バーコードバトラー（β版）", divider="gray")
    
    tab1, tab2 = st.tabs(["🔑 ログイン", "✍️ 新規会員登録"])
    
    with tab1:
        st.subheader("ログイン")
        
        with st.form("login_form"):
            login_email = st.text_input(
                "📧 メールアドレス", 
                placeholder="example@email.com",
                key="login_email"
            )
            login_password = st.text_input(
                "🔒 パスワード", 
                type="password",
                placeholder="パスワードを入力",
                key="login_password"
            )
            login_submit = st.form_submit_button("🚀 ログインする", type="primary", use_container_width=True)
            
            if login_submit:
                if not login_email or not login_password:
                    st.error("メールアドレスとパスワードを入力してください。")
                else:
                    with st.spinner("ログイン中..."):
                        result = auth.sign_in(login_email, login_password)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(result["message"])
        
        st.markdown("---")
        if st.button("🔑 パスワードをお忘れの方はこちら（未実装）", disabled=True):
            st.info("パスワードリセット機能は今後実装予定です")
    
    with tab2:
        st.subheader("新規会員登録")
        
        with st.form("signup_form"):
            signup_email = st.text_input(
                "📧 メールアドレス", 
                placeholder="example@email.com",
                key="signup_email"
            )
            signup_password = st.text_input(
                "🔒 パスワード", 
                type="password",
                placeholder="6文字以上",
                key="signup_password",
                help="6文字以上で設定してください"
            )
            signup_password_confirm = st.text_input(
                "🔒 パスワード確認", 
                type="password",
                placeholder="パスワードを再入力",
                key="signup_password_confirm"
            )
            signup_name = st.text_input(
                "👤 お名前", 
                placeholder="例：田中太郎",
                key="signup_name"
            )
            signup_submit = st.form_submit_button("📝 会員登録をする", type="primary", use_container_width=True)
            
            if signup_submit:
                # バリデーション
                if not signup_email or not signup_password or not signup_name:
                    st.error("すべての項目を入力してください。")
                elif len(signup_password) < 6:
                    st.error("パスワードは6文字以上で設定してください。")
                elif signup_password != signup_password_confirm:
                    st.error("パスワードが一致しません。")
                else:
                    with st.spinner("アカウント作成中..."):
                        result = auth.sign_up(signup_email, signup_password, signup_name)
                        
                        if result["success"]:
                            st.success(result["message"])
                            st.info("📧 メールボックスを確認し、認証リンクをクリックしてください。")
                        else:
                            st.error(result["message"])
        
        st.markdown("---")
        st.info("💡 アカウント作成後、メール認証が必要です")


if __name__ == "__main__":
    main()