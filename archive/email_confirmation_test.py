"""
メール確認機能のテストアプリ

このアプリでは以下の機能をテストします：
1. 新規アカウント作成時のメール確認
2. ログイン時のメール確認状態チェック
3. 確認メールの再送信
4. SMTPサーバー設定状況の確認
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
    st.title("📧 メール確認機能テスト")
    st.write("このアプリでメール確認機能をテストできます。")
    
    # 現在の認証設定を表示
    show_auth_settings()
    
    # メインのタブ
    tab1, tab2, tab3, tab4 = st.tabs(["新規登録", "ログイン", "確認メール再送信", "設定チェック"])
    
    with tab1:
        test_signup()
    
    with tab2:
        test_signin()
    
    with tab3:
        test_resend_confirmation()
    
    with tab4:
        show_detailed_settings()

def show_auth_settings():
    """認証設定の状況を表示"""
    st.sidebar.header("🔧 認証設定状況")
    
    # SMTP設定の確認
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    
    if smtp_host and smtp_user and smtp_pass:
        st.sidebar.success("✅ SMTP設定: 設定済み")
        st.sidebar.write(f"📧 SMTPホスト: {smtp_host}")
    else:
        st.sidebar.warning("⚠️ SMTP設定: 未設定")
        st.sidebar.write("Supabase標準メール機能使用")
    
    # Supabase設定の確認
    if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY'):
        st.sidebar.success("✅ Supabase: 接続済み")
    else:
        st.sidebar.error("❌ Supabase: 設定エラー")

def test_signup():
    """新規登録のテスト"""
    st.header("👤 新規アカウント作成テスト")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ユーザー名", placeholder="山田太郎")
            email = st.text_input("メールアドレス", placeholder="test@example.com")
        with col2:
            password = st.text_input("パスワード", type="password", placeholder="6文字以上")
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
                st.error("パスワードは6文字以上で入力してください。")
                return
            
            # アカウント作成を実行
            with st.spinner("アカウントを作成中..."):
                result = auth.sign_up(email, password, name)
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
                
                # 結果の詳細を表示
                st.info("📊 登録結果の詳細")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**メール確認状態:**")
                    if result.get("email_confirmed", False):
                        st.write("✅ 確認済み（すぐにログイン可能）")
                    else:
                        st.write("⏳ 確認待ち（確認メールをチェック）")
                
                with col2:
                    st.write("**次のステップ:**")
                    if result.get("needs_email_confirmation", False):
                        st.write("1. 📬 受信箱をチェック")
                        st.write("2. 🔗 確認リンクをクリック")
                        st.write("3. 🔐 ログインページへ移動")
                    else:
                        st.write("すぐにログインできます！")
                
                # デバッグ情報（開発時のみ表示）
                if st.checkbox("🔍 デバッグ情報を表示"):
                    st.json(result)
            
            else:
                st.error(f"❌ {result.get('message', 'アカウント作成に失敗しました')}")
                
                # エラーの詳細を表示
                if "error" in result:
                    st.write("**エラー詳細:**")
                    st.code(result["error"])

def test_signin():
    """ログインのテスト"""
    st.header("🔐 ログインテスト")
    
    with st.form("signin_form"):
        email = st.text_input("メールアドレス", placeholder="登録済みのメールアドレス")
        password = st.text_input("パスワード", type="password")
        
        submit = st.form_submit_button("ログイン", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("メールアドレスとパスワードを入力してください。")
                return
            
            # ログインを実行
            with st.spinner("ログイン中..."):
                result = auth.sign_in(email, password)
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
                
                # ユーザー情報を表示
                user_info = result.get("user", {})
                st.info("👤 ログイン済みユーザー情報")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ユーザー名:** {user_info.get('user_name', 'N/A')}")
                    st.write(f"**ユーザーID:** {user_info.get('user_id', 'N/A')}")
                
                with col2:
                    st.write(f"**メールアドレス:** {user_info.get('mail_address', 'N/A')}")
                    st.write(f"**登録日:** {user_info.get('created_at', 'N/A')}")
            
            else:
                st.error(f"❌ {result.get('message', 'ログインに失敗しました')}")
                
                # メール確認が必要な場合の案内
                if result.get("needs_email_confirmation", False):
                    st.warning("📧 メール確認が必要です")
                    st.write("以下の方法で解決できます：")
                    st.write("1. **受信箱を確認** - 確認メールが届いているかチェック")
                    st.write("2. **確認メール再送信** - 「確認メール再送信」タブを使用")
                    st.write("3. **迷惑メールフォルダ確認** - 迷惑メールに振り分けられていないかチェック")
                
                # デバッグ情報
                if st.checkbox("🔍 エラー詳細を表示", key="signin_debug"):
                    st.json(result)

def test_resend_confirmation():
    """確認メール再送信のテスト"""
    st.header("📬 確認メール再送信テスト")
    
    st.write("メール確認がお済みでない場合、確認メールを再送信できます。")
    
    with st.form("resend_form"):
        email = st.text_input("メールアドレス", placeholder="確認メールを再送信したいメールアドレス")
        
        submit = st.form_submit_button("確認メールを再送信", use_container_width=True)
        
        if submit:
            if not email:
                st.error("メールアドレスを入力してください。")
                return
            
            # 確認メール再送信を実行
            with st.spinner("確認メールを再送信中..."):
                result = auth.resend_confirmation(email)
            
            if result["success"]:
                st.success(f"✅ {result['message']}")
                
                st.info("📧 次のステップ")
                st.write("1. **受信箱をチェック** - 新しい確認メールが届きます")
                st.write("2. **確認リンクをクリック** - メール内のリンクをクリック")
                st.write("3. **ログインを試す** - 確認後にログインできます")
                
                # 注意事項
                st.warning("⚠️ 注意事項")
                st.write("- 確認メールが届くまで数分かかる場合があります")
                st.write("- 迷惑メールフォルダもチェックしてください")
                if not os.getenv('SMTP_HOST'):
                    st.write("- 現在Supabase標準メール機能を使用中（制限あり）")
            
            else:
                st.error(f"❌ {result.get('message', '確認メール送信に失敗しました')}")
                
                if "error" in result:
                    st.write("**エラー詳細:**")
                    st.code(result["error"])

def show_detailed_settings():
    """詳細設定の表示"""
    st.header("⚙️ 詳細設定情報")
    
    # 認証設定チェック結果を表示
    check_result = auth.check_auth_settings()
    
    if check_result["smtp_configured"]:
        st.success("✅ SMTP設定: 正常")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**SMTPサーバー:**")
            st.write(f"ホスト: {check_result['smtp_host']}")
            st.write(f"ポート: {check_result['smtp_port']}")
            st.write(f"セキュリティ: {check_result['smtp_security']}")
        
        with col2:
            st.write("**認証情報:**")
            st.write(f"ユーザー: {check_result['smtp_user']}")
            st.write(f"パスワード: {'設定済み' if check_result['smtp_pass'] else '未設定'}")
    
    else:
        st.warning("⚠️ SMTP設定: 未設定（Supabase標準機能使用）")
        st.write("**制限事項:**")
        st.write("- 1時間あたりのメール送信数に制限あり")
        st.write("- メール到達率が低い場合がある")
        st.write("- 迷惑メールに振り分けられる可能性が高い")
        
        st.info("💡 推奨解決策")
        st.write("1. **Resend SMTPを設定** - `RESEND_SMTP_SETUP.md`を参照")
        st.write("2. **開発時は確認スキップ** - Supabase設定で無効化")
    
    # 環境変数の状況
    st.subheader("🔐 環境変数設定状況")
    
    env_vars = [
        ("SUPABASE_URL", "Supabase プロジェクトURL"),
        ("SUPABASE_KEY", "Supabase API キー"),
        ("SMTP_HOST", "SMTPサーバーホスト"),
        ("SMTP_PORT", "SMTPポート"),
        ("SMTP_USER", "SMTP認証ユーザー"),
        ("SMTP_PASS", "SMTP認証パスワード"),
    ]
    
    for var_name, description in env_vars:
        value = os.getenv(var_name)
        if value:
            if "PASS" in var_name or "KEY" in var_name:
                display_value = "設定済み（非表示）"
            else:
                display_value = value
            st.write(f"✅ **{description}**: {display_value}")
        else:
            st.write(f"❌ **{description}**: 未設定")
    
    # Supabase認証設定（参考）
    st.subheader("📋 Supabase認証設定（参考）")
    st.write("Supabaseダッシュボードで以下を確認してください：")
    st.write("1. **Authentication > Settings > Email Auth** - メール認証が有効")
    st.write("2. **Authentication > Settings > SMTP Settings** - カスタムSMTP設定")
    st.write("3. **Authentication > Email Templates** - メールテンプレート")

if __name__ == "__main__":
    main()