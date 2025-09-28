"""
図鑑画面のDB連携機能追加

login.pyの図鑑画面を拡張して、以下の機能を追加：
1. charactersテーブルからキャラクター情報を取得
2. character_img_urlからSupabase Storageの画像を表示
3. ユーザーごとのキャラクター管理
"""

# login.pyに追加する関数群

# 1. キャラクターデータを取得する関数
def get_user_characters():
    """
    現在のユーザーのキャラクター一覧を取得
    
    Returns:
        list: キャラクターデータのリスト
    """
    try:
        user_id = st.session_state.user.id if st.session_state.user else None
        if not user_id:
            return []
        
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

# 2. Supabase Storageから画像URLを取得する関数
def get_storage_image_url(img_path):
    """
    Supabase Storageから公開URLを取得
    
    Args:
        img_path (str): Storageのファイルパス
        
    Returns:
        str: 公開URL またはエラー時はNone
    """
    try:
        if not img_path:
            return None
            
        # Supabase StorageのURLを構築
        # 形式: https://[project-ref].supabase.co/storage/v1/object/public/[bucket]/[path]
        project_url = API_URL  # SUPABASE_URL
        bucket_name = "character-images"  # バケット名（設定に合わせて変更）
        
        # すでに完全なURLの場合はそのまま返す
        if img_path.startswith('http'):
            return img_path
        
        # Storage URLを構築
        storage_url = f"{project_url}/storage/v1/object/public/{bucket_name}/{img_path}"
        return storage_url
        
    except Exception as e:
        print(f"Storage URL取得エラー: {str(e)}")
        return None

# 3. キャラクター保存機能
def save_character_to_db(character_name, barcode, region, power_level, image_data, character_prompt):
    """
    キャラクターをデータベースとStorageに保存
    
    Args:
        character_name (str): キャラクター名
        barcode (str): バーコード
        region (str): 地域
        power_level (int): 強さ
        image_data: 画像データ（PIL Image）
        character_prompt (str): キャラクター生成プロンプト
        
    Returns:
        dict: 保存結果
    """
    try:
        user_id = st.session_state.user.id if st.session_state.user else None
        if not user_id:
            return {"success": False, "error": "ユーザーが認証されていません"}
        
        # 1. 画像をStorageに保存
        import io
        import uuid
        
        # ユニークなファイル名を生成
        file_id = str(uuid.uuid4())
        file_name = f"{user_id}/{file_id}.png"
        
        # 画像をバイナリデータに変換
        img_buffer = io.BytesIO()
        image_data.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Supabase Storageにアップロード
        storage_response = supabase.storage.from_("character-images").upload(
            file_name, 
            img_buffer.getvalue(),
            file_options={"content-type": "image/png"}
        )
        
        if storage_response.get('error'):
            return {"success": False, "error": f"画像保存エラー: {storage_response['error']}"}
        
        # 2. キャラクター情報をDBに保存
        character_data = {
            "user_id": user_id,
            "character_name": character_name,
            "barcode": barcode,
            "region": region,
            "power_level": power_level or random.randint(100, 999),  # デフォルト値
            "character_img_url": file_name,  # Storageのパス
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

# 4. 拡張された図鑑画面の関数
def enhanced_zukan_page():
    """
    DB連携機能付きの図鑑画面
    """
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
                                st.warning("画像の読み込みに失敗しました")
                                st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                        
                        # 詳細情報
                        st.write(f"**バーコード:** {char['barcode']}")
                        st.write(f"**出身地:** {char['region']}")
                        st.write(f"**パワー:** {char['power_level']}")
                        st.write(f"**獲得日:** {char['created_at'][:10]}")
                        
                        # 詳細表示ボタン
                        if st.button(f"詳細", key=f"detail_{char['character_id']}"):
                            st.session_state.selected_character = char
                            st.session_state.show_character_detail = True
                        
                        st.divider()
        
        # キャラクター詳細モーダル（選択された場合）
        if st.session_state.get('show_character_detail', False):
            show_character_detail_modal()
    
    else:
        st.info("🔍 まだキャラクターがいません")
        st.write("バーコードをスキャンして新しいキャラクターを獲得しよう！")
        
        # サンプル画像を表示
        st.image("https://via.placeholder.com/400x200?text=Scan+Barcode+to+Get+Characters!", use_container_width=True)
    
    st.markdown("---")
    if st.button("⬅️ メイン画面へ戻る"):
        go_to("main")

# 5. キャラクター詳細表示
def show_character_detail_modal():
    """
    選択されたキャラクターの詳細を表示
    """
    char = st.session_state.get('selected_character')
    if not char:
        return
    
    st.markdown("---")
    st.markdown("## 🔍 キャラクター詳細")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 画像表示
        img_url = get_storage_image_url(char['character_img_url'])
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
    
    with col2:
        # 詳細情報
        st.markdown(f"### 🎭 {char['character_name']}")
        st.write(f"**キャラクターID:** {char['character_id']}")
        st.write(f"**バーコード:** {char['barcode']}")
        st.write(f"**出身地:** {char['region']}")
        st.write(f"**パワーレベル:** {char['power_level']}")
        st.write(f"**獲得日時:** {char['created_at']}")
        
        # 生成プロンプト表示
        if char.get('character_prompt'):
            with st.expander("🎨 キャラクター設定"):
                st.write(char['character_prompt'])
    
    # 閉じるボタン
    if st.button("❌ 閉じる"):
        st.session_state.show_character_detail = False
        st.session_state.selected_character = None
        st.rerun()