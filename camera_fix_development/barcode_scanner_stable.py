"""
pyzbar問題を回避したカメラ機能付きバーコードスキャナー
- OpenCVでカメラ機能
- QRコード生成機能
- 手動入力フォールバック
- pyzbar不使用で安定動作
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import qrcode
import io
import base64
import os
from datetime import datetime
import tempfile

# Supabase client (既存のコードと同じ設定を想定)
try:
    from supabase import create_client, Client
    
    # 環境変数から取得
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        SUPABASE_ENABLED = True
    else:
        SUPABASE_ENABLED = False
        st.warning("Supabase環境変数が設定されていません。ローカルモードで動作します。")
except ImportError:
    SUPABASE_ENABLED = False
    st.warning("Supabaseライブラリがインストールされていません。ローカルモードで動作します。")

def init_session_state():
    """セッション状態の初期化"""
    if 'barcode_history' not in st.session_state:
        st.session_state.barcode_history = []
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False

def generate_qr_code(data):
    """QRコードを生成"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # PILイメージをbase64に変換
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return img_str
    except Exception as e:
        st.error(f"QRコード生成エラー: {e}")
        return None

def capture_camera_image():
    """カメラから画像をキャプチャ"""
    try:
        # OpenCVでカメラ初期化
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("カメラにアクセスできません")
            return None
        
        # フレームをキャプチャ
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            st.error("画像キャプチャに失敗しました")
            return None
        
        # BGR to RGB変換
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
        
    except Exception as e:
        st.error(f"カメラエラー: {e}")
        return None

def save_barcode_to_history(barcode_data, source="manual"):
    """バーコードデータを履歴に保存"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        'timestamp': timestamp,
        'data': barcode_data,
        'source': source
    }
    
    st.session_state.barcode_history.append(entry)
    
    # Supabaseに保存（可能な場合）
    if SUPABASE_ENABLED:
        try:
            result = supabase.table('barcode_scans').insert(entry).execute()
            st.success("データベースに保存されました！")
        except Exception as e:
            st.warning(f"データベース保存エラー: {e}")

def display_camera_interface():
    """カメラインターフェースを表示"""
    st.subheader("📷 カメラでスキャン")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📸 写真を撮る", type="primary"):
            with st.spinner("カメラから画像を取得中..."):
                captured_image = capture_camera_image()
                
                if captured_image:
                    st.image(captured_image, caption="キャプチャされた画像", use_column_width=True)
                    st.session_state.captured_image = captured_image
                    
                    # 画像処理とバーコード解析のプレースホルダー
                    st.info("💡 現在、この画像からのバーコード自動読取りは開発中です。\n手動でバーコードの内容を入力してください。")
    
    with col2:
        st.markdown("### カメラ機能について")
        st.markdown("""
        **現在利用可能：**
        - ✅ カメラから画像キャプチャ
        - ✅ 撮影した画像の表示
        - ✅ 手動でバーコード入力
        
        **開発中：**
        - 🔄 画像からの自動バーコード読取り
        - 🔄 リアルタイムスキャン
        """)

def display_manual_input():
    """手動入力インターフェース"""
    st.subheader("✏️ 手動でバーコード入力")
    
    barcode_input = st.text_input(
        "バーコードの内容を入力してください：",
        placeholder="例：1234567890123"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 登録", type="primary") and barcode_input:
            save_barcode_to_history(barcode_input, "manual")
            st.success(f"バーコード '{barcode_input}' を登録しました！")
            
    with col2:
        if st.button("🔄 QRコード生成") and barcode_input:
            qr_image = generate_qr_code(barcode_input)
            if qr_image:
                st.image(f"data:image/png;base64,{qr_image}", 
                        caption=f"QRコード: {barcode_input}", 
                        width=200)

def display_upload_interface():
    """ファイルアップロードインターフェース"""
    st.subheader("📁 画像ファイルをアップロード")
    
    uploaded_file = st.file_uploader(
        "バーコード画像を選択してください", 
        type=['png', 'jpg', 'jpeg']
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた画像", use_column_width=True)
        
        st.info("💡 アップロードされた画像からの自動バーコード読取りは開発中です。\n手動でバーコードの内容を入力してください。")

def display_history():
    """履歴表示"""
    st.subheader("📜 スキャン履歴")
    
    if st.session_state.barcode_history:
        for i, entry in enumerate(reversed(st.session_state.barcode_history)):
            with st.expander(f"#{len(st.session_state.barcode_history)-i}: {entry['data']} ({entry['timestamp']})"):
                st.write(f"**データ:** {entry['data']}")
                st.write(f"**取得方法:** {entry['source']}")
                st.write(f"**時刻:** {entry['timestamp']}")
                
                # QRコード生成
                qr_image = generate_qr_code(entry['data'])
                if qr_image:
                    st.image(f"data:image/png;base64,{qr_image}", width=150)
    else:
        st.info("まだスキャン履歴がありません。")
    
    if st.button("🗑️ 履歴をクリア"):
        st.session_state.barcode_history = []
        st.success("履歴をクリアしました。")

def main():
    st.set_page_config(
        page_title="バーコードスキャナー",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 バーコード・QRコードスキャナー")
    st.markdown("---")
    
    # セッション状態初期化
    init_session_state()
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📷 カメラ", "✏️ 手動入力", "📁 ファイル", "📜 履歴"])
    
    with tab1:
        display_camera_interface()
    
    with tab2:
        display_manual_input()
    
    with tab3:
        display_upload_interface()
    
    with tab4:
        display_history()
    
    # サイドバーに情報表示
    with st.sidebar:
        st.markdown("### ℹ️ アプリ情報")
        st.markdown(f"""
        **バージョン:** 2.0
        **最終更新:** {datetime.now().strftime('%Y-%m-%d')}
        
        **機能状況:**
        - ✅ カメラキャプチャ
        - ✅ 手動入力
        - ✅ QRコード生成
        - ✅ 履歴管理
        - 🔄 自動読取り（開発中）
        """)
        
        if SUPABASE_ENABLED:
            st.success("🔗 データベース接続済み")
        else:
            st.warning("🔌 ローカルモード")

if __name__ == "__main__":
    main()