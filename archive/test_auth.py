"""
バーコードバトラー認証システム テスト用デモ

使用方法:
1. まずSQLファイルを実行してusersテーブルを更新
2. streamlit run barcode_battler_auth.py でテスト実行
"""

import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth

def test_auth_demo():
    """認証システムのデモ画面"""
    st.title("🧪 バーコードバトラー認証システム テスト")
    
    auth = BarcodeBattlerAuth()
    
    st.header("現在の認証状態")
    if auth.is_authenticated():
        st.success("✅ ログイン済み")
        st.json(st.session_state.user_data)
        
        if st.button("ログアウトテスト"):
            result = auth.sign_out()
            st.write(result)
            st.rerun()
    else:
        st.warning("❌ 未ログイン")
    
    st.header("機能テスト")
    
    tab1, tab2 = st.tabs(["登録テスト", "ログインテスト"])
    
    with tab1:
        st.subheader("新規登録テスト")
        test_email = st.text_input("テスト用メール", value="test@example.com")
        test_password = st.text_input("テスト用パスワード", value="test123456", type="password")
        test_name = st.text_input("テスト用名前", value="テストユーザー")
        
        if st.button("登録テスト実行"):
            result = auth.sign_up(test_email, test_password, test_name)
            st.json(result)
    
    with tab2:
        st.subheader("ログインテスト")
        login_email = st.text_input("ログイン用メール", value="test@example.com")
        login_password = st.text_input("ログイン用パスワード", value="test123456", type="password")
        
        if st.button("ログインテスト実行"):
            result = auth.sign_in(login_email, login_password)
            st.json(result)


if __name__ == "__main__":
    test_auth_demo()