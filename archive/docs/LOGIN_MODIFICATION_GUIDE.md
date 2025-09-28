# login.py修正ガイド - 図鑑画面のDB連携対応

## 📝 修正手順

### 1. インポートの追加
login.pyの先頭に以下を追加：

```python
import uuid
from io import BytesIO
```

### 2. 新しい関数を追加（main_app()関数の前に追加）

```python
def get_user_characters():
    """現在のユーザーのキャラクター一覧を取得"""
    try:
        user_email = st.session_state.user.email if st.session_state.user else None
        if not user_email:
            return []
        
        # usersテーブルからuser_idを取得
        user_response = supabase.table('users').select('user_id').eq('mail_address', user_email).execute()
        if not user_response.data:
            return []
        
        user_id = user_response.data[0]['user_id']
        
        # charactersテーブルからユーザーのキャラクターを取得
        response = supabase.table('characters').select('''
            character_id,
            character_name,
            barcode,
            region,
            power_level,
            character_img_url,
            created_at,
            character_prompt
        ''').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"キャラクターデータの取得に失敗しました: {str(e)}")
        return []

def get_storage_image_url(img_path):
    """Supabase Storageから公開URLを取得"""
    try:
        if not img_path:
            return None
            
        # すでに完全なURLの場合はそのまま返す
        if img_path.startswith('http'):
            return img_path
        
        # Storage URLを構築
        project_url = API_URL  # SUPABASE_URL
        bucket_name = "character-images"
        storage_url = f"{project_url}/storage/v1/object/public/{bucket_name}/{img_path}"
        return storage_url
        
    except Exception as e:
        print(f"Storage URL取得エラー: {str(e)}")
        return None

def save_character_to_db(character_name, barcode, region, character_prompt, image):
    """キャラクターをデータベースとStorageに保存"""
    try:
        user_email = st.session_state.user.email if st.session_state.user else None
        if not user_email:
            return {"success": False, "error": "ユーザーが認証されていません"}
        
        # usersテーブルからuser_idを取得
        user_response = supabase.table('users').select('user_id').eq('mail_address', user_email).execute()
        if not user_response.data:
            return {"success": False, "error": "ユーザー情報が見つかりません"}
        
        user_id = user_response.data[0]['user_id']
        
        # 1. 画像をStorageに保存
        file_id = str(uuid.uuid4())
        file_name = f"user_{user_id}/{file_id}.png"
        
        # 画像をバイナリデータに変換
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Supabase Storageにアップロード
        storage_response = supabase.storage.from_("character-images").upload(
            file_name, 
            img_buffer.getvalue(),
            file_options={"content-type": "image/png"}
        )
        
        # 2. キャラクター情報をDBに保存
        character_data = {
            "user_id": user_id,
            "character_name": character_name,
            "barcode": barcode,
            "region": region,
            "power_level": random.randint(100, 999),
            "character_img_url": file_name,
            "character_prompt": character_prompt
        }
        
        db_response = supabase.table('characters').insert(character_data).execute()
        
        if db_response.data:
            return {
                "success": True, 
                "message": "キャラクターを図鑑に保存しました！",
                "character_id": db_response.data[0]['character_id']
            }
        else:
            return {"success": False, "error": "データベース保存に失敗しました"}
            
    except Exception as e:
        return {"success": False, "error": f"保存エラー: {str(e)}"}
```

### 3. 図鑑画面の修正
main_app()関数内の「--- 図鑑画面 ---」部分を以下に置き換え：

```python
    # --- 図鑑画面 ---
    elif st.session_state.page == "zukan":
        st.title("📖 キャラクター図鑑")
        
        # キャラクターデータを取得
        characters = get_user_characters()
        
        if characters:
            st.success(f"🎉 {len(characters)}体のキャラクターを発見！")
            
            # キャラクター表示設定
            cols_per_row = 2
            for i in range(0, len(characters), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(characters):
                        char = characters[idx]
                        
                        with col:
                            # キャラクター情報を表示
                            st.markdown(f"### 🎭 {char['character_name']}")
                            
                            # 画像を表示
                            img_url = get_storage_image_url(char['character_img_url'])
                            if img_url:
                                try:
                                    st.image(img_url, use_container_width=True)
                                except Exception:
                                    st.warning("⚠️ 画像読み込みエラー")
                                    st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                            
                            # 詳細情報
                            st.write(f"**🔢 バーコード:** `{char['barcode']}`")
                            st.write(f"**🌍 出身地:** {char['region']}")
                            st.write(f"**⚡ パワー:** {char['power_level']}")
                            st.write(f"**📅 獲得日:** {char['created_at'][:10]}")
                            
                            # 詳細表示
                            with st.expander("🔍 詳細設定"):
                                st.write(f"**キャラID:** {char['character_id']}")
                                if char.get('character_prompt'):
                                    st.write(f"**設定:** {char['character_prompt'][:100]}...")
                            
                            st.divider()
        
        else:
            st.info("🔍 まだキャラクターがいません")
            st.write("バーコードをスキャンして新しいキャラクターを獲得しよう！")
            
            # プレースホルダー画像
            st.image("https://via.placeholder.com/400x200?text=Scan+Barcode+to+Get+Characters!", 
                    use_container_width=True)
        
        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")
```

### 4. スキャン画面の保存機能追加
generate_character_image()関数の呼び出し後に以下を追加：

```python
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("✨ 生成する", use_container_width=True):
                sd_prompt, character_name, image = generate_character_image()
                
                if sd_prompt and character_name and image:
                    # 保存オプションを表示
                    st.markdown("---")
                    col_save1, col_save2 = st.columns(2)
                    
                    with col_save1:
                        if st.button("💾 図鑑に保存する", type="primary", use_container_width=True):
                            # バーコード情報を取得
                            current_barcode = digits_input if digits_input else "000000000000"
                            current_region = selected_pref
                            
                            # DB保存実行
                            with st.spinner("図鑑に保存中..."):
                                result = save_character_to_db(
                                    character_name=character_name,
                                    barcode=current_barcode,
                                    region=current_region,
                                    character_prompt=sd_prompt,
                                    image=image
                                )
                            
                            if result["success"]:
                                st.success(f"✅ {result['message']}")
                                st.balloons()
                            else:
                                st.error(f"❌ 保存失敗: {result['error']}")
                    
                    with col_save2:
                        if st.button("🔄 再生成する", use_container_width=True):
                            st.rerun()
```

## 🛠️ 実装前の準備

### Supabase Storage設定
1. Supabaseダッシュボード → Storage
2. "character-images" バケットを作成
3. 公開アクセス許可を設定

### テーブル確認
charactersテーブルに以下のカラムが必要：
- character_id (主キー)
- user_id (外部キー)
- character_name
- barcode
- region
- power_level
- character_img_url
- character_prompt
- created_at