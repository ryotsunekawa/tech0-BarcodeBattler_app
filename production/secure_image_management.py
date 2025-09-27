import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import requests
from PIL import Image
import io
from datetime import datetime
import json

# 環境変数を読み込み
load_dotenv()

class SecureImageManager:
    """認証必須のセキュアな画像管理クラス"""
    
    def __init__(self):
        """初期化"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_anon_key)
        self.bucket_name = "character-images"
        
        # セッション初期化
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user' not in st.session_state:
            st.session_state.user = None
    
    def authenticate_user(self, email, password, is_signup=False):
        """ユーザー認証"""
        try:
            if is_signup:
                # サインアップ
                result = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
            else:
                # サインイン
                result = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
            
            if result.user:
                st.session_state.authenticated = True
                st.session_state.user = result.user
                return {"success": True, "user": result.user}
            else:
                return {"success": False, "error": "認証に失敗しました"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_out(self):
        """サインアウト"""
        try:
            self.supabase.auth.sign_out()
            st.session_state.authenticated = False
            st.session_state.user = None
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_character_image(self, image_file, character_name):
        """
        認証済みユーザーの画像アップロード
        ファイルパス: {user_id}/{filename}
        """
        if not st.session_state.authenticated or not st.session_state.user:
            return {"success": False, "error": "認証が必要です"}
        
        try:
            user_id = st.session_state.user.id
            
            # ファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = image_file.name.split('.')[-1].lower()
            safe_character_name = "".join(c for c in character_name if c.isascii() and (c.isalnum() or c in (' ', '-', '_'))).strip()
            if not safe_character_name:
                safe_character_name = "character"
            safe_character_name = safe_character_name.replace(' ', '_')
            
            # ユーザーIDをパスに含める（セキュリティ用）
            filename = f"{user_id}/{safe_character_name}_{timestamp}_{str(uuid.uuid4())[:8]}.{file_extension}"
            
            # 画像ファイルを読み込み
            image_bytes = image_file.read()
            
            # Supabase Storageにアップロード
            result = self.supabase.storage.from_(self.bucket_name).upload(
                filename,
                image_bytes,
                file_options={
                    "content-type": f"image/{file_extension}",
                    "cache-control": "3600"
                }
            )
            
            if result.data:
                # 公開URLを取得
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(filename)
                
                return {
                    "success": True,
                    "filename": filename,
                    "public_url": public_url,
                    "message": "画像アップロードに成功しました"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "画像アップロードに失敗しました"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"アップロードエラー: {str(e)}"
            }
    
    def save_character_to_database(self, code_number, item_name, character_name, character_params, image_url):
        """認証済みユーザーのキャラクター情報保存"""
        if not st.session_state.authenticated or not st.session_state.user:
            return {"success": False, "error": "認証が必要です"}
        
        try:
            user_id = st.session_state.user.id
            
            data = {
                "user_id": user_id,
                "code_number": code_number,
                "item_name": item_name,
                "character_name": character_name,
                "character_parameter": character_params,
                "character_img_url": image_url
            }
            
            result = self.supabase.table('user_operations').insert(data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "data": result.data[0],
                    "message": "キャラクター情報を保存しました"
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": "データベース保存に失敗しました"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"保存エラー: {str(e)}"
            }
    
    def get_user_characters(self):
        """認証済みユーザーのキャラクター一覧取得"""
        if not st.session_state.authenticated or not st.session_state.user:
            return []
        
        try:
            user_id = st.session_state.user.id
            result = self.supabase.table('user_operations').select('*').eq('user_id', user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            st.error(f"キャラクター取得エラー: {str(e)}")
            return []

def main():
    """セキュアな画像管理システム（認証必須）"""
    st.title("🔒 セキュア画像管理システム（認証必須）")
    
    # セキュア画像管理クラス初期化
    secure_manager = SecureImageManager()
    
    # 認証チェック
    if not st.session_state.authenticated:
        st.warning("🔐 このシステムを使用するには認証が必要です")
        
        # 認証タブ
        tab1, tab2 = st.tabs(["🔑 サインイン", "✍️ サインアップ"])
        
        with tab1:
            st.header("サインイン")
            with st.form("signin_form"):
                email = st.text_input("メールアドレス", placeholder="example@email.com")
                password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
                submit = st.form_submit_button("🔓 サインイン")
                
                if submit and email and password:
                    result = secure_manager.authenticate_user(email, password, is_signup=False)
                    if result["success"]:
                        st.success("サインインしました！")
                        st.rerun()
                    else:
                        st.error(f"サインインエラー: {result['error']}")
        
        with tab2:
            st.header("新規登録")
            with st.form("signup_form"):
                email = st.text_input("メールアドレス", placeholder="example@email.com", key="signup_email")
                password = st.text_input("パスワード", type="password", placeholder="6文字以上", key="signup_password")
                confirm_password = st.text_input("パスワード確認", type="password", placeholder="パスワードを再入力", key="signup_confirm")
                submit = st.form_submit_button("📝 新規登録")
                
                if submit and email and password:
                    if password != confirm_password:
                        st.error("パスワードが一致しません")
                    elif len(password) < 6:
                        st.error("パスワードは6文字以上である必要があります")
                    else:
                        result = secure_manager.authenticate_user(email, password, is_signup=True)
                        if result["success"]:
                            st.success("アカウントを作成しました！メール認証後にサインインしてください。")
                        else:
                            st.error(f"登録エラー: {result['error']}")
        
        st.stop()
    
    # 認証済みユーザー向けUI
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"✅ 認証済み: {st.session_state.user.email}")
    with col2:
        if st.button("🚪 サインアウト"):
            secure_manager.sign_out()
            st.rerun()
    
    # メイン機能
    tab1, tab2, tab3 = st.tabs(["📤 画像アップロード", "🎨 キャラクター生成", "👥 マイキャラクター"])
    
    with tab1:
        st.header("画像アップロード（認証済みユーザーのみ）")
        
        uploaded_file = st.file_uploader(
            "キャラクター画像を選択してください",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp']
        )
        
        character_name = st.text_input("キャラクター名", placeholder="例: ファイアドラゴン")
        
        if st.button("🚀 セキュアアップロード") and uploaded_file and character_name:
            with st.spinner("画像をアップロード中..."):
                result = secure_manager.upload_character_image(uploaded_file, character_name)
                
                if result["success"]:
                    st.success(result["message"])
                    st.image(result["public_url"], caption=f"{character_name}", width=200)
                    st.info(f"ファイルパス: {result['filename']}")  # ユーザーIDが含まれる
                else:
                    st.error(result["message"])
    
    with tab2:
        st.header("キャラクター生成（認証済みユーザーのみ）")
        
        barcode = st.text_input("バーコード", placeholder="例: 4901480072968")
        item_name = st.text_input("商品名", placeholder="例: コクヨ キャンパスノート")
        char_name = st.text_input("キャラクター名", placeholder="例: ノートマスター")
        
        col1, col2 = st.columns(2)
        with col1:
            attack = st.number_input("攻撃力", min_value=1, max_value=100, value=50)
            defense = st.number_input("防御力", min_value=1, max_value=100, value=50)
        with col2:
            speed = st.number_input("素早さ", min_value=1, max_value=100, value=50)
            magic = st.number_input("魔力", min_value=1, max_value=100, value=50)
        
        element = st.selectbox("属性", ["火", "水", "土", "風", "光", "闇"])
        rarity = st.selectbox("レアリティ", ["コモン", "アンコモン", "レア", "エピック", "レジェンダリー"])
        
        if st.button("🎨 キャラクター生成") and barcode and item_name and char_name:
            character_params = {
                "attack": attack, "defense": defense, "speed": speed, "magic": magic,
                "element": element, "rarity": rarity, "skills": ["スキル1", "スキル2"]
            }
            
            # プレースホルダー画像URL
            placeholder_url = f"https://api.dicebear.com/7.x/avataaars/png?seed={char_name}"
            
            save_result = secure_manager.save_character_to_database(
                barcode, item_name, char_name, character_params, placeholder_url
            )
            
            if save_result["success"]:
                st.success("キャラクター生成完了！")
                col1, col2 = st.columns(2)
                with col1:
                    st.image(placeholder_url, caption=char_name, width=200)
                with col2:
                    st.json(character_params)
    
    with tab3:
        st.header("マイキャラクター（自分のみ表示）")
        
        characters = secure_manager.get_user_characters()
        
        if characters:
            for char in characters:
                with st.expander(f"{char['character_name']} - {char['item_name']}"):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        if char['character_img_url']:
                            st.image(char['character_img_url'], width=150)
                    
                    with col2:
                        st.write(f"**商品名:** {char['item_name']}")
                        st.write(f"**バーコード:** {char['code_number']}")
                        st.write(f"**作成日:** {char['created_at']}")
                    
                    with col3:
                        if char['character_parameter']:
                            params = char['character_parameter']
                            st.write(f"**攻撃力:** {params.get('attack', 'N/A')}")
                            st.write(f"**防御力:** {params.get('defense', 'N/A')}")
                            st.write(f"**属性:** {params.get('element', 'N/A')}")
                            st.write(f"**レアリティ:** {params.get('rarity', 'N/A')}")
        else:
            st.info("まだキャラクターが登録されていません")

if __name__ == "__main__":
    main()