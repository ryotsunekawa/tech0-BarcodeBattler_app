from supabase import create_client
import streamlit as st
import pandas as pd
import requests
import uuid
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
JANCODE_API_KEY = os.environ.get("JANCODE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

sample_data = {
    "user_id": "c1f72922-b67e-402a-96e0-e593a5299b9f",
    "user_name": "Taro Yamada",
    "user_location": "Tokyo, Japan",
    "barcode_info": "4901234567890",
    "char_image_url": "https://example.com/images/character_01.png",
    "char_name": "Flame Guardian",
    "char_power": 95,
}

def insert_character(data):
    try:
        # 'from_'メソッドでテーブルを指定し、insertでデータを挿入
        response = supabase.from_("characters").insert(data).execute()
        # 挿入の確認
        if response.data:
            st.success("キャラデータが正常に挿入されました！")
            st.json(response.data)
        else:
            st.error("データ挿入に失敗しました。")
            st.json(response.error)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

def insert_multiple_characters(data_list):
    """複数のキャラクターデータを一括挿入"""
    try:
        response = supabase.from_("characters").insert(data_list).execute()
        if response.data:
            st.success(f"{len(data_list)}件のキャラデータが正常に挿入されました！")
            return response.data
        else:
            st.error("データ挿入に失敗しました。")
            return None
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        return None

def get_barcode_info_jancode(barcode):
    """JANCODE LOOKUP APIからバーコード情報を取得（認証キー付き）"""
    if not JANCODE_API_KEY:
        st.warning("⚠️ JANCODE API キーが設定されていません")
        return None
        
    try:
        url = f"https://jancode.xyz/api/v1/items/{barcode}"
        headers = {
            'User-Agent': 'BarcodeApp/1.0',
            'Accept': 'application/json',
            'Authorization': f'Bearer {JANCODE_API_KEY}'  # 認証キーを追加
        }
        
        # パラメータとして認証キーを送信する場合（APIの仕様に応じて調整）
        params = {
            'api_key': JANCODE_API_KEY
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]  # 最初のアイテムを取得
                return {
                    "api": "JANCODE LOOKUP",
                    "name": item.get("name", "Unknown Product"),
                    "brand": item.get("maker", "Unknown Brand"),
                    "category": item.get("category", "Unknown Category"),
                    "jancode": item.get("jancode", barcode),
                    "price": item.get("price", "価格不明"),
                    "image_url": item.get("image_url", "")
                }
        elif response.status_code == 401:
            st.error("🔑 JANCODE API 認証エラー: APIキーが無効です")
        elif response.status_code == 403:
            st.error("🚫 JANCODE API アクセス拒否: APIキーの権限が不足しています")
        else:
            st.warning(f"⚠️ JANCODE API エラー: HTTP {response.status_code}")
            
    except Exception as e:
        st.warning(f"JANCODE LOOKUP API エラー: {e}")
    return None

def get_barcode_info_openfood(barcode):
    """Open Food Facts APIからバーコード情報を取得"""
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                return {
                    "api": "Open Food Facts",
                    "name": product.get("product_name", "Unknown Product"),
                    "brand": product.get("brands", "Unknown Brand"),
                    "category": product.get("categories", "Unknown Category"),
                    "image_url": product.get("image_url", "")
                }
    except Exception as e:
        st.warning(f"Open Food Facts API エラー: {e}")
    return None

def get_barcode_info(barcode):
    """複数のAPIからバーコード情報を取得（優先順位付き）"""
    st.info("🔍 バーコード情報を検索中...")
    
    # 日本のJANコード（13桁または8桁）の場合、JANCODE LOOKUPを優先
    if len(barcode) in [8, 13] and barcode.startswith(('45', '49')):
        st.info("🇯🇵 日本のJANコードを検出 - JANCODE LOOKUP APIで検索中...")
        jancode_result = get_barcode_info_jancode(barcode)
        if jancode_result:
            return jancode_result
    
    # JANCODE LOOKUPで見つからない場合、Open Food Factsを試す
    st.info("🌍 Open Food Facts APIで検索中...")
    openfood_result = get_barcode_info_openfood(barcode)
    if openfood_result:
        return openfood_result
    
    # 両方で見つからない場合
    return None

def generate_character_from_barcode(barcode_info, user_data, product_data=None):
    """バーコード情報と商品データからキャラクターデータを生成"""
    # バーコード数値からパワーを生成
    power = int(barcode_info[-3:]) if len(barcode_info) >= 3 else 50
    power = max(1, min(100, power))  # 1-100の範囲に制限
    
    # 商品情報を使ったキャラクター名生成
    char_name = f"バトラー{barcode_info[-4:]}"
    char_image_url = user_data.get("char_image_url", "")
    
    if product_data:
        product_name = product_data.get('name', '')
        category = product_data.get('category', '')
        
        # 商品名からキャラクター名を生成
        if product_name and product_name != "Unknown Product":
            # 商品名の最初の部分を使用
            name_parts = product_name.split()[:2]  # 最初の2単語
            char_name = f"{''.join(name_parts)[:8]}・バトラー"
        
        # カテゴリによるパワー補正
        category_power_bonus = {
            "食品": 10, "飲料": 5, "お菓子": 15, "日用品": 8,
            "化粧品": 12, "医薬品": 20, "書籍": 7, "文具": 6
        }
        
        for cat, bonus in category_power_bonus.items():
            if cat in category:
                power = min(100, power + bonus)
                break
        
        # 商品画像があれば使用
        if product_data.get('image_url'):
            char_image_url = product_data['image_url']
    
    return {
        "user_id": user_data.get("user_id", str(uuid.uuid4())),
        "user_name": user_data.get("user_name", "Unknown User"),
        "user_location": user_data.get("user_location", "Unknown Location"),
        "barcode_info": barcode_info,
        "char_image_url": char_image_url,
        "char_name": char_name,
        "char_power": power,
        "generated_date": datetime.now().isoformat()
    }

def process_csv_data(df):
    """CSVデータを処理してSupabase形式に変換"""
    processed_data = []
    
    for _, row in df.iterrows():
        # 必須フィールドの確認
        if pd.isna(row.get('barcode_info')) or pd.isna(row.get('user_name')):
            continue
            
        data = {
            "user_id": row.get('user_id', str(uuid.uuid4())),
            "user_name": str(row.get('user_name', 'Unknown')),
            "user_location": str(row.get('user_location', 'Unknown')),
            "barcode_info": str(row.get('barcode_info', '')),
            "char_image_url": str(row.get('char_image_url', '')),
            "char_name": str(row.get('char_name', f"キャラ{len(processed_data)+1}")),
            "char_power": int(row.get('char_power', 50)),
            "generated_date": row.get('generated_date', datetime.now().isoformat())
        }
        processed_data.append(data)
    
    return processed_data

# Streamlit UI
st.title("🎮 バーコードバトラー お供DB管理システム v3")

# タブ作成
tab1, tab2, tab3 = st.tabs(["📊 CSVアップロード", "🔍 バーコードスキャン", "💾 サンプルデータ"])

# Tab 1: CSVアップロード
with tab1:
    st.header("CSVファイルからデータ取り込み")
    
    uploaded_file = st.file_uploader("CSVファイルを選択してください", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # CSVファイルを読み込み
            df = pd.read_csv(uploaded_file)
            
            st.subheader("📋 アップロードされたデータ")
            st.dataframe(df.head(10))  # 最初の10行を表示
            
            st.write(f"総データ数: {len(df)}行")
            
            # データ処理と挿入
            if st.button("🚀 データをSupabaseに挿入"):
                processed_data = process_csv_data(df)
                
                if processed_data:
                    with st.spinner('データを挿入中...'):
                        result = insert_multiple_characters(processed_data)
                        
                    if result:
                        st.balloons()
                        st.success(f"✅ {len(processed_data)}件のデータが正常に挿入されました！")
                else:
                    st.error("❌ 処理可能なデータが見つかりませんでした。")
                    
        except Exception as e:
            st.error(f"❌ CSVファイル読み込みエラー: {e}")

# Tab 2: バーコードスキャン
with tab2:
    st.header("バーコードからキャラクター生成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 ユーザー情報")
        user_name = st.text_input("ユーザー名", value="プレイヤー1")
        user_location = st.text_input("所在地", value="東京")
        user_id_input = st.text_input("ユーザーID（任意）", placeholder="空白の場合は自動生成")
        
    with col2:
        st.subheader("📱 バーコード情報")
        barcode_input = st.text_input("バーコード番号", placeholder="例: 4901234567890 (JANコード)")
        
        # バーコード形式の説明
        with st.expander("💡 対応バーコード形式"):
            st.write("""
            **JANコード（日本）:**
            - 13桁: 4901234567890
            - 8桁: 49012345
            - 国コード: 45, 49で始まる
            
            **その他の国際バーコード:**
            - EAN-13, UPC-A, EAN-8など
            """)
        
        if barcode_input:
            # 外部APIからバーコード情報取得
            barcode_data = get_barcode_info(barcode_input)
                
            if barcode_data:
                st.success(f"✅ {barcode_data.get('api', 'API')} から情報取得成功！")
                
                # 見やすく情報を表示
                col2_1, col2_2 = st.columns(2)
                
                with col2_1:
                    st.write("**📦 商品情報**")
                    st.write(f"**商品名:** {barcode_data.get('name', 'N/A')}")
                    st.write(f"**ブランド:** {barcode_data.get('brand', 'N/A')}")
                    st.write(f"**カテゴリ:** {barcode_data.get('category', 'N/A')}")
                    
                    # JANCODE固有の情報
                    if 'price' in barcode_data:
                        st.write(f"**価格:** {barcode_data.get('price', 'N/A')}")
                
                with col2_2:
                    # 商品画像があれば表示
                    if barcode_data.get('image_url'):
                        try:
                            st.image(barcode_data['image_url'], caption="商品画像", width=150)
                        except:
                            st.write("🖼️ 画像の読み込みに失敗しました")
                
                # 詳細データ（開発者向け）
                with st.expander("🔍 詳細データ（JSON）"):
                    st.json(barcode_data)
                    
            else:
                st.warning("⚠️ バーコード情報を取得できませんでした。")
                st.info("""
                **考えられる原因:**
                - バーコード番号が間違っている
                - 商品がデータベースに登録されていない
                - APIのアクセス制限
                """)
    
    if st.button("🎯 キャラクター生成＆登録"):
        if barcode_input and user_name:
            user_data = {
                "user_id": user_id_input if user_id_input else str(uuid.uuid4()),
                "user_name": user_name,
                "user_location": user_location,
                "char_image_url": ""
            }
            
            # バーコード情報を再取得（キャラクター生成時）
            product_data = get_barcode_info(barcode_input) if barcode_input else None
            
            character_data = generate_character_from_barcode(barcode_input, user_data, product_data)
            
            with st.spinner('キャラクターを生成中...'):
                insert_character(character_data)
                
            # 生成されたキャラクター情報をプレビュー
            st.subheader("🎮 生成されたキャラクター")
            col3_1, col3_2 = st.columns(2)
            
            with col3_1:
                st.write(f"**👤 キャラクター名:** {character_data['char_name']}")
                st.write(f"**⚡ パワー:** {character_data['char_power']}")
                st.write(f"**📱 バーコード:** {character_data['barcode_info']}")
            
            with col3_2:
                if character_data['char_image_url']:
                    try:
                        st.image(character_data['char_image_url'], caption="キャラクター画像", width=100)
                    except:
                        st.write("🖼️ 画像なし")
                        
        else:
            st.error("❌ バーコード番号とユーザー名は必須です。")

# Tab 3: サンプルデータ & 設定
with tab3:
    st.header("サンプルデータ & API設定")
    
    # API設定状況を表示
    st.subheader("🔧 API設定状況")
    col3_1, col3_2 = st.columns(2)
    
    with col3_1:
        st.write("**Supabase接続:**")
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            st.success("✅ 設定済み")
        else:
            st.error("❌ 未設定")
    
    with col3_2:
        st.write("**JANCODE API:**")
        if JANCODE_API_KEY:
            st.success("✅ 認証キー設定済み")
            st.write(f"キー: {JANCODE_API_KEY[:8]}***")  # 最初の8文字のみ表示
        else:
            st.error("❌ 認証キー未設定")
            st.info("`.env`ファイルに`JANCODE_API_KEY`を追加してください")
    
    st.divider()
    
    # サンプルデータ
    st.subheader("📝 サンプルデータ挿入")
    st.json(sample_data)
    
    if st.button("📝 サンプルデータを挿入"):
        insert_character(sample_data)
        
    # テスト用バーコード
    st.subheader("🧪 テスト用バーコード")
    st.write("""
    **テスト用日本のJANコード:**
    - `4901234567890` (一般的なテストコード)
    - `4902102072854` (実在商品例)
    - `4547691316643` (実在商品例)
    
    **注意:** 実在しない商品のバーコードは情報が取得できません
    """)