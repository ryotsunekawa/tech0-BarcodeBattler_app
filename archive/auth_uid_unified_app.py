"""
Auth UID統一後のユーザー管理システム
Supabase AuthのUIDとusersテーブルのuser_idを統一した後の処理
"""

import streamlit as st
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

class AuthManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            st.error("❌ Supabase設定が見つかりません")
            st.stop()
        
        self.supabase: Client = create_client(url, key)
    
    def sign_up(self, email: str, password: str, user_name: str, location: str = ""):
        """
        新規ユーザー登録
        Auth登録と同時にusersテーブルにプロフィール作成
        """
        try:
            # 1. Supabase Authに登録
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # 2. usersテーブルにプロフィール情報を保存
                user_id = auth_response.user.id
                
                profile_data = {
                    "user_id": user_id,  # AuthのUIDをそのまま使用
                    "mail_address": email,
                    "user_name": user_name,
                    "location": location
                }
                
                # usersテーブルに挿入
                profile_response = self.supabase.table('users').insert(profile_data).execute()
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "profile": profile_response.data[0] if profile_response.data else None,
                    "message": "アカウント作成が完了しました"
                }
            else:
                return {
                    "success": False,
                    "message": "アカウント作成に失敗しました"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"エラー: {str(e)}"
            }
    
    def sign_in(self, email: str, password: str):
        """
        ユーザーログイン
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # プロフィール情報も取得
                profile = self.get_user_profile(response.user.id)
                
                return {
                    "success": True,
                    "user": response.user,
                    "profile": profile,
                    "message": "ログインしました"
                }
            else:
                return {
                    "success": False,
                    "message": "ログインに失敗しました"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"エラー: {str(e)}"
            }
    
    def sign_out(self):
        """
        ログアウト
        """
        try:
            self.supabase.auth.sign_out()
            return {
                "success": True,
                "message": "ログアウトしました"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"エラー: {str(e)}"
            }
    
    def get_current_user(self):
        """
        現在のログインユーザー取得
        """
        try:
            user = self.supabase.auth.get_user()
            if user.user:
                profile = self.get_user_profile(user.user.id)
                return {
                    "user": user.user,
                    "profile": profile
                }
            return None
        except Exception:
            return None
    
    def get_user_profile(self, user_id: str):
        """
        ユーザープロフィール取得
        """
        try:
            response = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None
    
    def update_user_profile(self, user_id: str, updates: dict):
        """
        ユーザープロフィール更新
        """
        try:
            response = self.supabase.table('users').update(updates).eq('user_id', user_id).execute()
            return {
                "success": True,
                "data": response.data[0] if response.data else None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"エラー: {str(e)}"
            }
    
    def save_character_to_db(self, character_data: dict):
        """
        キャラクターを操作ログに保存
        現在のユーザーIDを自動的に使用
        """
        current_user_data = self.get_current_user()
        if not current_user_data:
            return {
                "success": False,
                "message": "ログインが必要です"
            }
        
        try:
            # 現在のユーザーIDを追加
            character_data["user_id"] = current_user_data["user"].id
            
            response = self.supabase.table('user_operations').insert(character_data).execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
                "message": "キャラクターを保存しました"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"エラー: {str(e)}"
            }
    
    def get_user_characters(self):
        """
        現在のユーザーのキャラクター一覧を取得
        """
        current_user_data = self.get_current_user()
        if not current_user_data:
            return []
        
        try:
            response = self.supabase.table('user_operations').select('*').eq('user_id', current_user_data["user"].id).order('created_at', desc=True).execute()
            return response.data
        except Exception:
            return []


# Streamlitアプリ用のヘルパー関数
def initialize_auth():
    """
    認証マネージャーを初期化
    """
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    return st.session_state.auth_manager

def check_authentication():
    """
    認証状態をチェック
    """
    auth = initialize_auth()
    current_user = auth.get_current_user()
    
    if current_user:
        st.session_state.authenticated = True
        st.session_state.current_user = current_user
        return True
    else:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        return False

def display_user_info():
    """
    ユーザー情報表示
    """
    if st.session_state.get('authenticated') and st.session_state.get('current_user'):
        user_data = st.session_state.current_user
        profile = user_data.get('profile')
        
        st.sidebar.success(f"👋 {profile.get('user_name', 'ユーザー')}さん")
        st.sidebar.write(f"📧 {profile.get('mail_address')}")
        if profile.get('location'):
            st.sidebar.write(f"📍 {profile.get('location')}")
        
        if st.sidebar.button("ログアウト"):
            auth = initialize_auth()
            result = auth.sign_out()
            if result["success"]:
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.rerun()


# テスト用メイン関数
def main():
    """
    Auth UID統一後のテストアプリ
    """
    st.title("🔐 Auth UID統一後 認証テスト")
    
    # 認証状態チェック
    is_authenticated = check_authentication()
    
    if not is_authenticated:
        tab1, tab2 = st.tabs(["ログイン", "新規登録"])
        
        with tab1:
            st.header("🔑 ログイン")
            with st.form("login_form"):
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                submit = st.form_submit_button("ログイン")
                
                if submit and email and password:
                    auth = initialize_auth()
                    result = auth.sign_in(email, password)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        
        with tab2:
            st.header("👤 新規登録")
            with st.form("signup_form"):
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                user_name = st.text_input("ユーザー名")
                location = st.text_input("居住地（任意）")
                submit = st.form_submit_button("アカウント作成")
                
                if submit and email and password and user_name:
                    auth = initialize_auth()
                    result = auth.sign_up(email, password, user_name, location)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.info("ログインしてください")
                    else:
                        st.error(result["message"])
    else:
        # 認証済みユーザーの画面
        display_user_info()
        
        st.header("🎮 キャラクター管理")
        
        # 既存キャラクター表示
        auth = initialize_auth()
        characters = auth.get_user_characters()
        
        if characters:
            st.subheader("あなたのキャラクター")
            for char in characters:
                with st.expander(f"{char['character_name']} - {char['item_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if char.get('character_img_url'):
                            st.image(char['character_img_url'], width=150)
                    with col2:
                        st.write(f"バーコード: {char['code_number']}")
                        if char.get('character_parameter'):
                            params = char['character_parameter']
                            if isinstance(params, dict):
                                for key, value in params.items():
                                    st.write(f"{key}: {value}")
        else:
            st.info("まだキャラクターがありません")
        
        # テスト用キャラクター作成
        if st.button("テストキャラクター作成"):
            test_character = {
                "code_number": "1234567890123",
                "item_name": "テスト商品",
                "character_name": "テストキャラ",
                "character_img_url": "https://via.placeholder.com/150",
                "character_parameter": {
                    "attack": 50,
                    "defense": 60,
                    "speed": 70,
                    "magic": 40
                }
            }
            
            result = auth.save_character_to_db(test_character)
            if result["success"]:
                st.success("テストキャラクターを作成しました！")
                st.rerun()
            else:
                st.error(result["message"])


if __name__ == "__main__":
    main()