from supabase import create_client
import streamlit as st

SUPABASE_URL = "https://lkhbqezbsjojrlmhnuev.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxraGJxZXpic2pvanJsbWhudWV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg1OTgyMDMsImV4cCI6MjA3NDE3NDIwM30.iaXHvXMn2Hgejjm6R6k0E66fxvMREdGtgAkYyP8dz_M"

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
        # 'from_'メソッドでテーブルそして医師、 insertでデータを挿入
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

# Streamlitのボタンをクリックでデータ挿入を実行
if st.button("サンプルデータを挿入"):
    insert_character(sample_data)
