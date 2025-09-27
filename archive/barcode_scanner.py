import streamlit as st
import requests
import cv2
import numpy as np
from pyzbar import pyzbar
import os
from dotenv import load_dotenv
from PIL import Image
import io

# .envファイルを読み込み
load_dotenv()

JANCODE_API_KEY = os.environ.get("JANCODE_API_KEY")

def get_jancode_info(barcode):
    """JANCODE LOOKUP APIからバーコード情報を取得"""
    if not JANCODE_API_KEY:
        st.error("⚠️ JANCODE API キーが設定されていません")
        st.info("`.env`ファイルに`JANCODE_API_KEY`を追加してください")
        return None
        
    try:
        url = f"https://jancode.xyz/api/v1/items/{barcode}"
        headers = {
            'User-Agent': 'BarcodeScanner/1.0',
            'Accept': 'application/json',
            'Authorization': f'Bearer {JANCODE_API_KEY}'
        }
        
        params = {
            'api_key': JANCODE_API_KEY
        }
        
        with st.spinner(f'🔍 バーコード {barcode} を検索中...'):
            response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                return {
                    "success": True,
                    "barcode": barcode,
                    "name": item.get("name", "商品名不明"),
                    "maker": item.get("maker", "メーカー不明"),
                    "category": item.get("category", "カテゴリ不明"),
                    "price": item.get("price", "価格不明"),
                    "image_url": item.get("image_url", ""),
                    "description": item.get("description", ""),
                    "jancode": item.get("jancode", barcode)
                }
            else:
                return {"success": False, "error": "商品が見つかりませんでした"}
                
        elif response.status_code == 401:
            return {"success": False, "error": "API認証エラー: APIキーが無効です"}
        elif response.status_code == 403:
            return {"success": False, "error": "アクセス拒否: APIキーの権限が不足しています"}
        elif response.status_code == 404:
            return {"success": False, "error": "商品が見つかりませんでした"}
        else:
            return {"success": False, "error": f"APIエラー: HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "タイムアウト: APIの応答が遅すぎます"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "接続エラー: インターネット接続を確認してください"}
    except Exception as e:
        return {"success": False, "error": f"予期しないエラー: {str(e)}"}

def decode_barcode_from_image(image):
    """画像からバーコードをデコード"""
    try:
        # PIL ImageをOpenCV形式に変換
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            # RGBからBGRに変換
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # グレースケール変換
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        # バーコードをデコード
        barcodes = pyzbar.decode(gray)
        
        results = []
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            results.append({
                'data': barcode_data,
                'type': barcode_type,
                'rect': barcode.rect
            })
        
        return results
    except Exception as e:
        st.error(f"画像処理エラー: {e}")
        return []

def display_product_info(product_data):
    """商品情報を見やすく表示"""
    if not product_data.get("success"):
        st.error(f"❌ {product_data.get('error', '不明なエラー')}")
        return
    
    st.success("✅ 商品情報を取得しました！")
    
    # メイン情報表示
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📦 商品情報")
        
        # 基本情報をテーブル形式で表示
        info_data = {
            "バーコード": product_data.get('barcode', 'N/A'),
            "商品名": product_data.get('name', 'N/A'),
            "メーカー": product_data.get('maker', 'N/A'),
            "カテゴリ": product_data.get('category', 'N/A'),
            "価格": product_data.get('price', 'N/A'),
        }
        
        for key, value in info_data.items():
            st.write(f"**{key}:** {value}")
        
        # 説明文があれば表示
        description = product_data.get('description', '')
        if description and description.strip():
            st.write(f"**説明:** {description}")
    
    with col2:
        # 商品画像表示
        image_url = product_data.get('image_url', '')
        if image_url:
            try:
                st.image(image_url, caption="商品画像", width=200)
            except:
                st.write("🖼️ 画像の読み込みに失敗")
        else:
            st.write("🖼️ 画像なし")
    
    # 詳細データ（開発者向け）
    with st.expander("🔍 詳細データ（JSON形式）"):
        st.json(product_data)

def main():
    st.set_page_config(
        page_title="バーコードスキャナー",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 JANCODE バーコードスキャナー")
    st.markdown("---")
    
    # API設定状況
    st.sidebar.header("🔧 設定状況")
    if JANCODE_API_KEY:
        st.sidebar.success("✅ JANCODE API設定済み")
        st.sidebar.write(f"キー: {JANCODE_API_KEY[:8]}***")
    else:
        st.sidebar.error("❌ JANCODE API未設定")
        st.sidebar.info("`.env`ファイルにAPIキーを設定してください")
    
    # タブ作成
    tab1, tab2, tab3 = st.tabs(["✏️ 手動入力", "📷 画像アップロード", "ℹ️ 使い方"])
    
    # Tab 1: 手動入力
    with tab1:
        st.header("✏️ バーコード手動入力")
        
        barcode_input = st.text_input(
            "バーコード番号を入力してください",
            placeholder="例: 4901234567890",
            help="13桁または8桁のJANコードを入力"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            search_button = st.button("🔍 検索", type="primary", disabled=not barcode_input)
        
        with col2:
            if st.button("🗑️ クリア"):
                st.rerun()
        
        if search_button and barcode_input:
            # バーコード形式チェック
            if not barcode_input.isdigit():
                st.error("❌ バーコードは数字のみ入力してください")
            elif len(barcode_input) not in [8, 13]:
                st.warning("⚠️ JANコードは通常8桁または13桁です")
                # それでも検索を実行
                result = get_jancode_info(barcode_input)
                display_product_info(result)
            else:
                result = get_jancode_info(barcode_input)
                display_product_info(result)
    
    # Tab 2: 画像アップロード
    with tab2:
        st.header("📷 バーコード画像スキャン")
        
        uploaded_file = st.file_uploader(
            "バーコード画像をアップロードしてください",
            type=['png', 'jpg', 'jpeg'],
            help="バーコードが写っている画像をアップロード"
        )
        
        if uploaded_file is not None:
            try:
                # 画像を読み込み
                image = Image.open(uploaded_file)
                
                # 画像表示
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.image(image, caption="アップロード画像", width=300)
                
                with col2:
                    st.write("**画像解析中...**")
                    
                    # バーコードをデコード
                    barcodes = decode_barcode_from_image(image)
                    
                    if barcodes:
                        st.success(f"✅ {len(barcodes)}個のバーコードを検出しました")
                        
                        for i, barcode in enumerate(barcodes):
                            st.write(f"**バーコード {i+1}:**")
                            st.write(f"- データ: `{barcode['data']}`")
                            st.write(f"- タイプ: {barcode['type']}")
                            
                            # 検索ボタン
                            if st.button(f"🔍 商品情報を検索", key=f"search_{i}"):
                                result = get_jancode_info(barcode['data'])
                                display_product_info(result)
                    else:
                        st.warning("⚠️ バーコードが検出されませんでした")
                        st.info("""
                        **改善のヒント:**
                        - バーコードがはっきりと写っているか確認
                        - 画像の明度を調整
                        - バーコード全体が画像に収まっているか確認
                        """)
            
            except Exception as e:
                st.error(f"画像処理エラー: {e}")
    
    # Tab 3: 使い方
    with tab3:
        st.header("ℹ️ 使い方ガイド")
        
        st.markdown("""
        ## 🎯 このアプリについて
        
        JANCODE LOOKUP APIを使用して、日本の商品バーコード（JANコード）から商品情報を取得するツールです。
        
        ## 📱 機能一覧
        
        ### ✏️ 手動入力
        - バーコード番号を直接入力して検索
        - 8桁または13桁のJANコードに対応
        
        ### 📷 画像スキャン
        - バーコード画像をアップロードして自動読み取り
        - 複数のバーコードを同時検出可能
        
        ## 🔧 設定方法
        
        1. JANCODE LOOKUP APIのアカウント作成
        2. APIキーを取得
        3. `.env`ファイルに以下を追加：
        ```
        JANCODE_API_KEY=your_api_key_here
        ```
        
        ## 📋 対応バーコード形式
        
        - **JANコード（13桁）**: 4901234567890
        - **JANコード（8桁）**: 49012345
        - **国コード**: 45, 49で始まる日本の商品
        
        ## 🛠️ 必要なライブラリ
        
        ```bash
        pip install streamlit requests opencv-python pyzbar pillow python-dotenv
        ```
        
        ## ⚠️ 注意事項
        
        - APIキーが必要です
        - インターネット接続が必要です
        - 実在しない商品は検索できません
        - API使用制限がある場合があります
        
        ## 🆘 トラブルシューティング
        
        | エラー | 原因 | 解決方法 |
        |--------|------|----------|
        | API認証エラー | APIキーが無効 | APIキーを確認 |
        | 商品が見つからない | 商品未登録 | 正しいバーコードか確認 |
        | 接続エラー | ネットワーク問題 | インターネット接続確認 |
        | バーコード検出失敗 | 画像品質 | より鮮明な画像を使用 |
        """)

if __name__ == "__main__":
    main()