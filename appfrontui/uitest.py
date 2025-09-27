import streamlit as st
import zxingcpp
from PIL import Image
import io

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def main_app():
    name_to_display = st.session_state.get("full_name", st.session_state.user.email)
    st.subheader(f"{name_to_display}さん、おかえりなさい！")

    if "page" not in st.session_state:
        st.session_state.page = "main"
    if "characters" not in st.session_state:
        st.session_state.characters = []

    # --- メイン画面 ---
    if st.session_state.page == "main":
        st.title("📚 バーコードキャラクター図鑑")
        st.write("遊び方を選んでください")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📷 スキャン画面へ", key="scan_btn"):
                go_to("scan")
        with col2:
            if st.button("📖 図鑑画面へ", key="zukan_btn"):
                go_to("zukan")

        # ボタンデザイン
        st.markdown(
            """
            <style>
            div.stButton > button:first-child {
                height: 180px;
                width: 100%;
                font-size: 36px;
                font-weight: bold;
                border-radius: 15px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # --- スキャン画面 ---
    elif st.session_state.page == "scan":
        st.title("📷 バーコードスキャン")
        img_file = st.camera_input("JANコードを撮影してください")

        digits, result = None, None
        if img_file:
            img = Image.open(io.BytesIO(img_file.getvalue()))
            result = zxingcpp.read_barcode(img)
            if result:
                digits = result.text
                st.success(f"読み取ったコード: {digits} (種類: {result.format})")
            else:
                st.warning("バーコードの読み取りに失敗しました")

        # 数字入力
        col1, col2 = st.columns([3,1])
        with col1:
            digits_input = st.text_input(
                "数字を入力（読み取ったコードがあれば自動入力されます）",
                value=digits or ""
            )
        with col2:
            st.write("")  # 縦位置調整
            number_ok = st.button("✅ 数字OK")

        # 都道府県選択
        prefectures = [
            "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
            "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
            "新潟県","富山県","石川県","福井県","山梨県","長野県",
            "岐阜県","静岡県","愛知県","三重県",
            "滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
            "鳥取県","島根県","岡山県","広島県","山口県",
            "徳島県","香川県","愛媛県","高知県",
            "福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県",
            "沖縄県"
        ]
        selected_pref = st.selectbox("都道府県を選択", prefectures, index=12)

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            generate_btn = st.button("✨ 生成する", use_container_width=True)

        if number_ok or generate_btn:
            if digits_input.strip():
                character = {
                    "name": f"キャラ_{len(st.session_state.characters)+1}",
                    "power": len(digits_input) + prefectures.index(selected_pref),
                    "barcode": digits_input,
                    "region": selected_pref,
                    "type": "OCR" if not result else result.format
                }
                st.session_state.characters.append(character)
                st.success(f"🎉 新キャラを獲得！: {character}")
            else:
                st.error("数字が入力されていません")

        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    # --- 図鑑画面 ---
    elif st.session_state.page == "zukan":
        st.title("📖 図鑑")
        if st.session_state.characters:
            for idx, char in enumerate(st.session_state.characters, start=1):
                st.write(f"### {idx}. {char['name']}")
                st.write(f"バーコード: {char['barcode']} (種類: {char['type']})")
                st.write(f"地域: {char['region']}")
                st.write(f"強さ: {char['power']}")
                st.divider()
        else:
            st.info("まだキャラクターがいません。スキャンしてみましょう！")

        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    # --- サイドバー ---
    if st.sidebar.button("🔄 セッションをリセット"):
        st.session_state.clear()
        st.rerun()

