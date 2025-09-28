"""
段階的Auth UID統合システム
既存のuser_idを維持しつつauth_user_idで認証と紐付け
"""

import streamlit as st
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

class GradualAuthManager:
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
                auth_user_id = auth_response.user.id
                
                profile_data = {
                    "auth_user_id": auth_user_id,  # AuthのUIDを設定
                    "mail_address": email,
                    "user_name": user_name,
                    "location": location
                }
                
                # usersテーブルに挿入（user_idは自動生成）
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
        既存ユーザーとの互換性を保持
        """
        try:
            # 1. Supabase Authでログイン
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                auth_user_id = response.user.id
                
                # 2. プロフィール情報を取得（auth_user_idまたはmail_addressで検索）
                profile = self.get_or_create_user_profile(auth_user_id, email)
                
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
    
    def get_or_create_user_profile(self, auth_user_id: str, email: str):
        """
        ユーザープロフィールを取得、または既存ユーザーのauth_user_idを更新
        """
        try:
            # 1. auth_user_idで検索
            response = self.supabase.table('users').select('*').eq('auth_user_id', auth_user_id).execute()
            if response.data:
                return response.data[0]
            
            # 2. auth_user_idが設定されていない既存ユーザーをmail_addressで検索
            response = self.supabase.table('users').select('*').eq('mail_address', email).execute()
            if response.data:
                # 既存ユーザーのauth_user_idを更新
                user_record = response.data[0]
                updated_response = self.supabase.table('users').update({
                    "auth_user_id": auth_user_id
                }).eq('user_id', user_record['user_id']).execute()
                
                return updated_response.data[0] if updated_response.data else user_record
            
            # 3. どちらでも見つからない場合はNoneを返す
            return None
            
        except Exception as e:
            print(f"Profile取得エラー: {str(e)}")
            return None
    
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
                profile = self.get_user_profile_by_auth_id(user.user.id)
                return {
                    "user": user.user,
                    "profile": profile
                }
            return None
        except Exception:
            return None
    
    def get_user_profile_by_auth_id(self, auth_user_id: str):
        """
        auth_user_idでプロフィール取得
        """
        try:
            response = self.supabase.table('users').select('*').eq('auth_user_id', auth_user_id).execute()
            return response.data[0] if response.data else None
        except Exception:
            return None
    
    def save_character_to_db(self, character_data: dict):
        """
        キャラクターを操作ログに保存
        現在のユーザーのuser_id（DB）を使用
        """
        current_user_data = self.get_current_user()
        if not current_user_data or not current_user_data.get("profile"):
            return {
                "success": False,
                "message": "ログインが必要です"
            }
        
        try:
            # 現在のユーザーのDB user_idを追加
            character_data["user_id"] = current_user_data["profile"]["user_id"]
            
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
        if not current_user_data or not current_user_data.get("profile"):
            return []
        
        try:
            # DB user_idでキャラクターを取得
            user_id = current_user_data["profile"]["user_id"]
            response = self.supabase.table('user_operations').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return response.data
        except Exception:
            return []
    
    def update_user_profile(self, updates: dict):
        """
        ユーザープロフィール更新
        """
        current_user_data = self.get_current_user()
        if not current_user_data or not current_user_data.get("profile"):
            return {
                "success": False,
                "message": "ログインが必要です"
            }
        
        try:
            user_id = current_user_data["profile"]["user_id"]
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


# Streamlitアプリ用のヘルパー関数
def initialize_gradual_auth():
    """
    段階的認証マネージャーを初期化
    """
    if 'gradual_auth_manager' not in st.session_state:
        st.session_state.gradual_auth_manager = GradualAuthManager()
    return st.session_state.gradual_auth_manager

def check_gradual_authentication():
    """
    認証状態をチェック
    """
    auth = initialize_gradual_auth()
    current_user = auth.get_current_user()
    
    if current_user:
        st.session_state.authenticated = True
        st.session_state.current_user = current_user
        return True
    else:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        return False

def display_gradual_user_info():
    """
    ユーザー情報表示（段階的統合版）
    """
    if st.session_state.get('authenticated') and st.session_state.get('current_user'):
        user_data = st.session_state.current_user
        profile = user_data.get('profile')
        
        if profile:
            st.sidebar.success(f"👋 {profile.get('user_name', 'ユーザー')}さん")
            st.sidebar.write(f"📧 {profile.get('mail_address')}")
            if profile.get('location'):
                st.sidebar.write(f"📍 {profile.get('location')}")
            
            # デバッグ情報
            with st.sidebar.expander("🔧 デバッグ情報"):
                st.write(f"Auth UID: {user_data['user'].id[:8]}...")
                st.write(f"DB user_id: {profile['user_id']}")
                auth_linked = "✅" if profile.get('auth_user_id') else "❌"
                st.write(f"Auth連携: {auth_linked}")
        
        if st.sidebar.button("ログアウト"):
            auth = initialize_gradual_auth()
            result = auth.sign_out()
            if result["success"]:
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.rerun()


# テスト用メイン関数
def main():
    """
    段階的Auth UID統合テストアプリ
    """
    st.title("🔗 段階的Auth UID統合テスト")
    
    # 認証状態チェック
    is_authenticated = check_gradual_authentication()
    
    if not is_authenticated:
        tab1, tab2, tab3 = st.tabs(["ログイン", "新規登録", "既存ユーザーテスト"])
        
        with tab1:
            st.header("🔑 ログイン")
            with st.form("login_form"):
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                submit = st.form_submit_button("ログイン")
                
                if submit and email and password:
                    auth = initialize_gradual_auth()
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
                    auth = initialize_gradual_auth()
                    result = auth.sign_up(email, password, user_name, location)
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.info("ログインしてください")
                    else:
                        st.error(result["message"])
        
        with tab3:
            st.header("👥 既存ユーザーテスト")
            st.info("既存のCSVユーザーでテストしてください:")
            
            test_users = [
                "tanaka@example.com",
                "yamada@example.com", 
                "sato@example.com",
                "suzuki@example.com",
                "watanabe@example.com"
            ]
            
            for email in test_users:
                st.write(f"📧 {email}")
            
            st.warning("⚠️ 注意: 既存ユーザーは初回ログイン時にSupabase Authのアカウント作成が必要です")
    
    else:
        # 認証済みユーザーの画面
        display_gradual_user_info()
        
        st.header("🎮 キャラクター管理")
        
        # 既存キャラクター表示
        auth = initialize_gradual_auth()
        characters = auth.get_user_characters()
        
        if characters:
            st.subheader("あなたのキャラクター")
            for char in characters:
                with st.expander(f"{char.get('character_name', '無名キャラ')} - {char.get('item_name', '不明アイテム')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if char.get('character_img_url'):
                            st.image(char['character_img_url'], width=150)
                    with col2:
                        st.write(f"バーコード: {char.get('code_number', 'N/A')}")
                        if char.get('character_parameter'):
                            params = char['character_parameter']
                            if isinstance(params, dict):
                                for key, value in params.items():
                                    st.write(f"{key}: {value}")
                        st.write(f"作成日: {char.get('created_at', 'N/A')}")
        else:
            st.info("まだキャラクターがありません")
        
        # テスト用キャラクター作成
        if st.button("テストキャラクター作成"):
            test_character = {
                "code_number": "1234567890123",
                "item_name": "テスト商品",
                "character_name": "統合テストキャラ",
                "character_img_url": "https://via.placeholder.com/150",
                "character_parameter": {
                    "attack": 50,
                    "defense": 60,
                    "speed": 70,
                    "magic": 40,
                    "element": "統合",
                    "rarity": "テスト"
                }
            }
            
            result = auth.save_character_to_db(test_character)
            if result["success"]:
                st.success("テストキャラクターを作成しました！")
                st.rerun()
            else:
                st.error(result["message"])
        
        # 既存データの移行状況確認
        with st.expander("📊 データ移行状況"):
            current_user = st.session_state.current_user
            profile = current_user.get('profile') if current_user else None
            
            if profile:
                st.write("**現在のユーザー情報:**")
                st.json(profile)
                
                auth_linked = profile.get('auth_user_id') is not None
                if auth_linked:
                    st.success("✅ Auth UID連携済み")
                else:
                    st.warning("⚠️ Auth UID未連携（既存ユーザー）")


if __name__ == "__main__":
    main()