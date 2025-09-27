import streamlit as st
import zxingcpp
from PIL import Image
import io


if "reset" not in st.session_state:
    st.session_state.clear()
    st.session_state.page = "main"
    st.session_state.characters = []
    st.session_state.reset = True  


def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()  


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

    
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            height: 180px;      /* ボタンの高さ */
            width: 100%;        /* 横幅いっぱい（colの半分を占有） */
            font-size: 36px;    /* 文字サイズ */
            font-weight: bold;
            border-radius: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )



elif st.session_state.page == "scan":
    st.title("📷 バーコードスキャン")

    img_file = st.camera_input("JANコードを撮影してください")

    if img_file:
        img = Image.open(io.BytesIO(img_file.getvalue()))

       
        result = zxingcpp.read_barcode(img)

        if result:
            st.success(f"読み取ったコード: {result.text} (種類: {result.format})")

            
            character = {
                "name": f"キャラ_{len(st.session_state.characters)+1}",
                "power": len(result.text),
                "barcode": result.text,
                "type": result.format
            }

            
            st.session_state.characters.append(character)

            st.write(f"🎉 新キャラを獲得！: {character}")
        else:
            st.error("JANコードを読み取れませんでした。")

    if st.button("⬅️ メイン画面へ戻る"):
        go_to("main")


elif st.session_state.page == "zukan":
    st.title("📖 図鑑")

    if st.session_state.characters:
        for idx, char in enumerate(st.session_state.characters, start=1):
            st.write(f"### {idx}. {char['name']}")
            st.write(f"バーコード: {char['barcode']} (種類: {char['type']})")
            st.write(f"強さ: {char['power']}")
            st.divider()
    else:
        st.info("まだキャラクターがいません。スキャンしてみましょう！")

    if st.button("⬅️ メイン画面へ戻る"):
        go_to("main")


if st.sidebar.button("🔄 セッションをリセット"):
    st.session_state.clear()
    st.rerun()
