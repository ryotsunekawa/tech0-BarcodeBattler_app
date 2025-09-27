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

class SupabaseImageManager:
    """Supabase Storageを使用した画像管理クラス"""
    
    def __init__(self):
        """初期化"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_anon_key)
        self.bucket_name = "character-images"
        
        # バケットの存在確認・作成
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """バケットが存在することを確認、なければ作成"""
        try:
            # バケット一覧を取得
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                # バケットを作成（パブリック設定）
                result = self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": True}
                )
                print(f"バケット '{self.bucket_name}' を作成しました")
            else:
                print(f"バケット '{self.bucket_name}' は既に存在します")
        except Exception as e:
            print(f"バケット確認エラー: {str(e)}")
    
    def upload_character_image(self, image_file, user_id, character_name):
        """
        キャラクター画像をStorageにアップロード
        
        Args:
            image_file: アップロードする画像ファイル
            user_id: ユーザーID
            character_name: キャラクター名
            
        Returns:
            dict: アップロード結果とURL
        """
        try:
            # デバッグ用：アップロード前の情報を表示
            print(f"アップロード開始 - ファイル名: {image_file.name}, ユーザーID: {user_id}")
            
            # ファイル名を生成（ユニーク、パス区切り文字を使用しない）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = image_file.name.split('.')[-1].lower()
            # ファイル名をASCII文字のみに制限（日本語等のUnicode文字を除去）
            safe_character_name = "".join(c for c in character_name if c.isascii() and (c.isalnum() or c in (' ', '-', '_'))).strip()
            if not safe_character_name:  # 日本語のみの場合はデフォルト名を使用
                safe_character_name = "character"
            safe_character_name = safe_character_name.replace(' ', '_')
            filename = f"{safe_character_name}_{timestamp}_{str(uuid.uuid4())[:8]}.{file_extension}"
            
            print(f"生成されたファイル名: {filename}")
            
            # 画像ファイルを読み込み
            image_bytes = image_file.read()
            print(f"画像サイズ: {len(image_bytes)} bytes")
            
            # Supabase Storageにアップロード
            print("Supabaseにアップロード中...")
            result = self.supabase.storage.from_(self.bucket_name).upload(
                filename,
                image_bytes,
                file_options={
                    "content-type": f"image/{file_extension}",
                    "cache-control": "3600"
                }
            )
            
            # デバッグ用：結果の詳細を表示
            print(f"アップロード結果タイプ: {type(result)}")
            print(f"アップロード結果: {result}")
            
            # アップロード成功かどうかの判定（複数パターンで確認）
            upload_success = False
            error_message = None
            
            # パターン1: resultが文字列（成功）
            if isinstance(result, str):
                upload_success = True
            # パターン2: resultがオブジェクトでerrorがない
            elif result and not (hasattr(result, 'error') and result.error):
                upload_success = True
            # パターン3: resultがNoneでない
            elif result is not None:
                upload_success = True
            else:
                error_message = "アップロード結果が空です"
            
            if upload_success:
                # 公開URLを取得
                try:
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(filename)
                    print(f"公開URL生成成功: {public_url}")
                    
                    return {
                        "success": True,
                        "filename": filename,
                        "public_url": public_url,
                        "message": "画像アップロードに成功しました"
                    }
                except Exception as url_error:
                    print(f"URL生成エラー: {url_error}")
                    return {
                        "success": False,
                        "error": str(url_error),
                        "message": f"アップロードは成功しましたが、URL生成でエラー: {str(url_error)}"
                    }
            else:
                if hasattr(result, 'error'):
                    error_message = result.error
                return {
                    "success": False,
                    "error": error_message,
                    "message": f"画像アップロードに失敗しました: {error_message}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"アップロードエラー: {str(e)}"
            }
    
    def generate_character_image_url(self, character_name, character_params):
        """
        AI画像生成APIを呼び出してキャラクター画像を生成
        
        Args:
            character_name: キャラクター名
            character_params: キャラクターパラメータ
            
        Returns:
            str: 生成された画像URL
        """
        try:
            # 外部AI画像生成APIを呼び出す（開発中は仮実装）
            return self._call_external_image_api(character_name, character_params)
        except Exception as e:
            print(f"AI画像生成エラー: {str(e)}")
            # フォールバック: プレースホルダー画像
            return self._generate_placeholder_image(character_name, character_params)
    
    def _call_external_image_api(self, character_name, character_params):
        """
        外部AI画像生成APIを呼び出す（将来実装）
        
        Args:
            character_name: キャラクター名
            character_params: キャラクターパラメータ
            
        Returns:
            str: AI生成画像URL
        """
        # TODO: 外部AI APIとの連携実装
        # 例: OpenAI DALL-E、Stable Diffusion API、Midjourney API等
        
        # APIリクエスト例（疑似コード）
        """
        api_prompt = f"A cute character named {character_name} with {character_params.get('element', 'neutral')} element, "
        api_prompt += f"attack: {character_params.get('attack', 50)}, defense: {character_params.get('defense', 50)}"
        
        response = requests.post(
            "https://your-ai-api-endpoint.com/generate",
            json={
                "prompt": api_prompt,
                "style": "anime",
                "size": "512x512",
                "character_name": character_name
            },
            headers={"Authorization": f"Bearer {AI_API_KEY}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["image_url"]
        """
        
        # 現在は例外を投げてフォールバックを使用
        raise Exception("外部AI APIは開発中です")
    
    def _generate_placeholder_image(self, character_name, character_params):
        """
        プレースホルダー画像URLを生成
        
        Args:
            character_name: キャラクター名
            character_params: キャラクターパラメータ
            
        Returns:
            str: プレースホルダー画像URL
        """
        element = character_params.get('element', 'unknown')
        
        # キャラクター名をURL安全な形式に変換
        safe_name = "".join(c for c in character_name if c.isascii() and (c.isalnum() or c in ('-', '_'))).lower()
        if not safe_name:
            safe_name = "character"
        
        # Dicebear API (アバター生成) - 開発中のプレースホルダー
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/png?seed={safe_name}&backgroundColor={self._get_color_by_element(element)}"
        
        return avatar_url
    
    def _get_color_by_element(self, element):
        """属性に応じた色を返す"""
        color_map = {
            "知識": "blue",
            "炭酸": "cyan", 
            "苦味": "brown",
            "紅茶": "orange",
            "和食": "green",
            "fire": "red",
            "water": "blue",
            "earth": "brown",
            "air": "lightgray"
        }
        return color_map.get(element, "gray")
    
    def save_character_to_database(self, user_id, code_number, item_name, character_name, character_params, image_url):
        """
        キャラクター情報をuser_operationsテーブルに保存
        
        Args:
            user_id: ユーザーID
            code_number: バーコード
            item_name: 商品名
            character_name: キャラクター名
            character_params: キャラクターパラメータ
            image_url: 画像URL
            
        Returns:
            dict: 保存結果
        """
        try:
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
    
    def get_user_characters(self, user_id):
        """
        ユーザーのキャラクター一覧を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            list: キャラクター一覧
        """
        try:
            result = self.supabase.table('user_operations').select('*').eq('user_id', user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            st.error(f"キャラクター取得エラー: {str(e)}")
            return []

def main():
    """画像管理システムのデモ"""
    st.title("🖼️ Supabase Storage 画像管理システム")
    
    # 重要：初回使用時の設定案内
    if 'setup_complete' not in st.session_state:
        st.warning("⚠️ 初回使用時は以下の設定が必要です：")
        st.code("""
1. Supabaseダッシュボード → SQL Editor で以下のSQLを実行：

-- デモ用ポリシー（誰でもアップロード可能）
DROP POLICY IF EXISTS "Authenticated users can upload character images" ON storage.objects;
CREATE POLICY "Demo: Anyone can upload to character-images" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'character-images');
CREATE POLICY "Demo: Anyone can view character-images" ON storage.objects
FOR SELECT USING (bucket_id = 'character-images');

2. 設定完了後、下のチェックボックスを選択してください
        """, language="sql")
        
        setup_done = st.checkbox("✅ Supabase設定完了")
        if setup_done:
            st.session_state.setup_complete = True
            st.rerun()
        else:
            st.stop()
    
    # 画像管理クラス初期化
    img_manager = SupabaseImageManager()
    
    # 実際のユーザーIDを取得（既存のダミーデータから）
    try:
        # 既存のユーザーIDを取得
        result = img_manager.supabase.table('users').select('user_id').limit(1).execute()
        if result.data:
            sample_user_id = result.data[0]['user_id']
            st.info(f"使用中のユーザーID: {sample_user_id}")
        else:
            st.error("ユーザーデータが見つかりません。先にダミーデータを作成してください。")
            st.stop()
    except Exception as e:
        st.error(f"ユーザーID取得エラー: {str(e)}")
        # フォールバック: 既知のダミーユーザーIDを使用
        sample_user_id = None
    
    tab1, tab2, tab3 = st.tabs(["📤 画像アップロード", "🎨 キャラクター生成", "👥 キャラクター一覧"])
    
    with tab1:
        st.header("画像アップロード")
        
        # 画像ファイルアップロード
        uploaded_file = st.file_uploader(
            "キャラクター画像を選択してください",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            help="対応形式: PNG, JPG, JPEG, GIF, WEBP"
        )
        
        character_name = st.text_input("キャラクター名", placeholder="例: ファイアドラゴン")
        
        if st.button("🚀 アップロード実行") and uploaded_file and character_name:
            with st.spinner("画像をアップロード中..."):
                result = img_manager.upload_character_image(
                    uploaded_file, 
                    sample_user_id, 
                    character_name
                )
                
                if result["success"]:
                    st.success(result["message"])
                    st.image(result["public_url"], caption=f"{character_name}", width=200)
                    st.text(f"公開URL: {result['public_url']}")
                else:
                    st.error(result["message"])
    
    with tab2:
        st.header("キャラクター自動生成")
        
        # バーコード入力
        barcode = st.text_input("バーコード", placeholder="例: 4901480072968")
        item_name = st.text_input("商品名", placeholder="例: コクヨ キャンパスノート")
        
        col1, col2 = st.columns(2)
        with col1:
            char_name = st.text_input("キャラクター名", placeholder="例: ノートマスター")
            attack = st.number_input("攻撃力", min_value=1, max_value=100, value=50)
            defense = st.number_input("防御力", min_value=1, max_value=100, value=50)
        
        with col2:
            speed = st.number_input("素早さ", min_value=1, max_value=100, value=50)
            magic = st.number_input("魔力", min_value=1, max_value=100, value=50)
            element = st.selectbox("属性", ["知識", "炭酸", "苦味", "紅茶", "和食", "火", "水", "土", "風"])
            rarity = st.selectbox("レアリティ", ["コモン", "アンコモン", "レア", "エピック", "レジェンダリー"])
        
        if st.button("🎨 キャラクター生成") and barcode and item_name and char_name and sample_user_id:
            character_params = {
                "attack": attack,
                "defense": defense, 
                "speed": speed,
                "magic": magic,
                "element": element,
                "rarity": rarity,
                "skills": ["スキル1", "スキル2", "スキル3"]  # デモ用
            }
            
            # AI画像生成（プレースホルダー）
            generated_image_url = img_manager.generate_character_image_url(char_name, character_params)
            
            # データベースに保存
            save_result = img_manager.save_character_to_database(
                sample_user_id,
                barcode,
                item_name,
                char_name,
                character_params,
                generated_image_url
            )
            
            if save_result["success"]:
                st.success("キャラクター生成完了！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(generated_image_url, caption=char_name, width=200)
                with col2:
                    st.json(character_params)
            else:
                st.error(save_result["message"])
    
    with tab3:
        st.header("キャラクター一覧")
        
        if sample_user_id:
            characters = img_manager.get_user_characters(sample_user_id)
        else:
            characters = []
            st.warning("ユーザーIDが取得できないため、キャラクター一覧を表示できません")
        
        if characters:
            for i, char in enumerate(characters):
                with st.expander(f"{char['character_name']} - {char['item_name']}"):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        if char['character_img_url']:
                            st.image(char['character_img_url'], width=150)
                        else:
                            st.info("画像なし")
                    
                    with col2:
                        st.write(f"**商品名:** {char['item_name']}")
                        st.write(f"**バーコード:** {char['code_number']}")
                        st.write(f"**作成日:** {char['created_at']}")
                    
                    with col3:
                        if char['character_parameter']:
                            params = char['character_parameter']
                            st.write(f"**攻撃力:** {params.get('attack', 'N/A')}")
                            st.write(f"**防御力:** {params.get('defense', 'N/A')}")
                            st.write(f"**素早さ:** {params.get('speed', 'N/A')}")
                            st.write(f"**魔力:** {params.get('magic', 'N/A')}")
                            st.write(f"**属性:** {params.get('element', 'N/A')}")
                            st.write(f"**レアリティ:** {params.get('rarity', 'N/A')}")
        else:
            st.info("キャラクターが登録されていません")

if __name__ == "__main__":
    main()