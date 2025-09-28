"""
開発用認証テストアプリ（メール確認無効版）

メール確認機能を無効化した開発用の認証システムテストアプリです。
SMTPサーバー設定なしでも認証機能をテストできます。
"""

import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 認証インスタンスを初期化
auth = BarcodeBattlerAuth()

def main():
    st.title("🔐 認証システムテスト（開発版）")
    st.info("💡 このアプリはメール確認機能を無効化した開発用バージョンです。")
    
    # サイドバーに現在の状態を表示
    show_auth_status()
    
    # 認証状態による画面切り替え
    if st.session_state.get("authenticated", False):
        show_authenticated_page()
    else:
        show_auth_page()

def show_auth_status():
    """認証状態をサイドバーに表示"""
    st.sidebar.header("🔒 認証状態")
    
    if st.session_state.get("authenticated", False):
        user_data = st.session_state.get("user_data", {})
        st.sidebar.success("✅ ログイン中")
        st.sidebar.write(f"👤 {user_data.get('user_name', 'Unknown')}")
        st.sidebar.write(f"📧 {user_data.get('mail_address', 'Unknown')}")
        
        if st.sidebar.button("ログアウト"):
            result = auth.sign_out()
            if result["success"]:
                st.rerun()
    else:
        st.sidebar.info("🔓 未ログイン")
    
    # 開発モード情報
    st.sidebar.header("⚙️ 開発設定")
    st.sidebar.write("📧 メール確認: 無効")
    st.sidebar.write("🚀 開発モード: 有効")
    
    if os.getenv('SUPABASE_URL'):
        st.sidebar.success("✅ Supabase: 接続済み")
    else:
        st.sidebar.error("❌ Supabase: 未設定")

def show_auth_page():
    """認証ページ（ログイン・新規登録）"""
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_signup_form()

def show_login_form():
    """ログインフォーム"""
    st.header("🔐 ログイン")
    
    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="example@mail.com")
        password = st.text_input("パスワード", type="password")
        
        submit = st.form_submit_button("ログイン", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("メールアドレスとパスワードを入力してください。")
                return
            
            with st.spinner("ログイン中..."):
                result = auth.sign_in(email, password)
            
            if result["success"]:
                st.success("✅ ログインしました！")
                st.rerun()
            else:
                st.error(f"❌ {result.get('message', 'ログインに失敗しました')}")
                
                # デバッグ情報を表示
                if st.checkbox("🔍 エラー詳細を表示"):
                    st.json(result)

def show_signup_form():
    """新規登録フォーム"""
    st.header("👤 新規アカウント作成")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("ユーザー名", placeholder="山田太郎")
            email = st.text_input("メールアドレス", placeholder="example@mail.com")
        
        with col2:
            password = st.text_input("パスワード", type="password", help="6文字以上")
            confirm_password = st.text_input("パスワード確認", type="password")
        
        submit = st.form_submit_button("アカウント作成", use_container_width=True)
        
        if submit:
            # バリデーション
            if not all([name, email, password, confirm_password]):
                st.error("すべてのフィールドを入力してください。")
                return
            
            if password != confirm_password:
                st.error("パスワードが一致しません。")
                return
            
            if len(password) < 6:
                st.error("パスワードは6文字以上で設定してください。")
                return
            
            # アカウント作成を実行
            with st.spinner("アカウントを作成中..."):
                result = auth.sign_up(email, password, name)
            
            if result["success"]:
                st.success("✅ アカウントが作成されました！")
                st.info("🔐 作成したアカウントですぐにログインできます。")
                
                # 自動的にログインタブに切り替えるための案内
                st.write("「ログイン」タブに切り替えてログインしてください。")
                
            else:
                st.error(f"❌ {result.get('message', 'アカウント作成に失敗しました')}")
                
                # デバッグ情報を表示
                if st.checkbox("🔍 エラー詳細を表示"):
                    st.json(result)

def show_authenticated_page():
    """認証後のページ"""
    user_data = st.session_state.get("user_data", {})
    
    st.header(f"👋 こんにちは、{user_data.get('user_name', 'ユーザー')}さん！")
    st.success("✅ 認証システムが正常に動作しています。")
    
    # ユーザー情報を表示
    st.subheader("👤 ユーザー情報")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**ユーザー名:** {user_data.get('user_name', 'N/A')}")
        st.write(f"**ユーザーID:** {user_data.get('user_id', 'N/A')}")
    
    with col2:
        st.write(f"**メールアドレス:** {user_data.get('mail_address', 'N/A')}")
        st.write(f"**登録日時:** {user_data.get('created_at', 'N/A')}")
    
    # 次のステップの案内
    st.subheader("🚀 次のステップ")
    st.write("認証システムが正常に動作していることが確認できました。")
    st.write("これで以下の機能を安全に利用できます：")
    st.write("- 📱 バーコードスキャナー機能")
    st.write("- 🗄️ データベース連携")
    st.write("- 🖼️ 画像管理システム")
    st.write("- 👥 マルチユーザー対応")
    
    # メインアプリへのリンク案内
    st.info("💡 準備ができましたら、メインのバーコードバトラーアプリを起動してお楽しみください！")
    
    # デバッグ情報
    if st.checkbox("🔍 セッション情報を表示"):
        st.subheader("🔧 開発者向け情報")
        st.write("**セッション状態:**")
        session_info = {
            "authenticated": st.session_state.get("authenticated", False),
            "user_id": st.session_state.get("user_id"),
            "full_name": st.session_state.get("full_name"),
        }
        st.json(session_info)

if __name__ == "__main__":
    main()