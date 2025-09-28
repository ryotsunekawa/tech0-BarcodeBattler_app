import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth
import time

def main():
    st.title("🔐 バーコードバトラー認証テスト（開発版）")
    
    # 認証システムの初期化（メール確認スキップモード）
    auth = BarcodeBattlerAuth(skip_email_confirmation=True)
    
    # セッション状態の確認
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # 設定確認セクション
    with st.sidebar:
        st.title("🔧 設定確認")
        
        if st.button("認証設定を確認"):
            settings = auth.check_auth_settings()
            if settings["success"]:
                st.success("✅ 設定確認完了")
                st.json(settings)
            else:
                st.error(f"❌ 設定エラー: {settings['message']}")
    
    # メイン認証フロー
    st.sidebar.title("機能選択")
    
    if not st.session_state.authenticated:
        mode = st.sidebar.selectbox(
            "モードを選択:",
            ["新規登録（開発版）", "ログイン", "既存ユーザーでテスト"]
        )
        
        if mode == "新規登録（開発版）":
            st.header("🆕 新規ユーザー登録（開発版）")
            st.info("📧 **開発モード**: メール確認をスキップして即座にログイン可能")
            
            with st.form("signup_form"):
                email = st.text_input("メールアドレス", placeholder="test@example.com")
                password = st.text_input("パスワード", type="password", help="6文字以上で設定してください")
                full_name = st.text_input("ユーザー名", placeholder="テストユーザー")
                
                submit_button = st.form_submit_button("新規登録")
                
                if submit_button:
                    if email and password and full_name:
                        if len(password) < 6:
                            st.error("パスワードは6文字以上で設定してください")
                        else:
                            with st.spinner("登録中..."):
                                result = auth.sign_up(email, password, full_name)
                            
                            if result["success"]:
                                st.success("✅ 登録成功！")
                                st.info(result['message'])
                                
                                # ユーザー情報表示
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.info(f"**ユーザーID:** {result['user']['user_id']}")
                                    st.info(f"**メールアドレス:** {result['user']['mail_address']}")
                                with col2:
                                    st.info(f"**ユーザー名:** {result['user']['user_name']}")
                                
                                # 開発モードでは即座にログイン
                                st.session_state.authenticated = True
                                st.session_state.user_info = result['user']
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ 登録失敗: {result['message']}")
                                if 'debug_info' in result:
                                    with st.expander("🔧 デバッグ情報"):
                                        st.code(result['debug_info'])
                    else:
                        st.error("全ての項目を入力してください")
        
        elif mode == "ログイン":
            st.header("🔑 ログイン")
            
            with st.form("login_form"):
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                
                submit_button = st.form_submit_button("ログイン")
                
                if submit_button:
                    if email and password:
                        with st.spinner("ログイン中..."):
                            result = auth.sign_in(email, password)
                        
                        if result["success"]:
                            st.success("✅ ログイン成功！")
                            st.session_state.authenticated = True
                            st.session_state.user_info = result['user']
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ ログイン失敗")
                            st.error(result['message'])
                            
                            # デバッグ情報表示
                            if "debug_info" in result:
                                with st.expander("🔧 デバッグ情報"):
                                    st.code(f"エラー詳細: {result['debug_info']}")
                                    st.code(f"エラーメッセージ: {result['error']}")
                    else:
                        st.error("メールアドレスとパスワードを入力してください")
        
        elif mode == "既存ユーザーでテスト":
            st.header("👥 既存ユーザーでテスト")
            
            # 既存ユーザーの例を表示
            st.info("**テスト用既存ユーザー:**")
            test_users = [
                {"email": "tanaka@example.com", "name": "田中太郎"},
                {"email": "yamada@example.com", "name": "山田花子"},
                {"email": "sato@example.com", "name": "佐藤次郎"},
            ]
            
            for user in test_users:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"📧 {user['email']}")
                with col2:
                    st.text(f"👤 {user['name']}")
                with col3:
                    if st.button("選択", key=f"select_{user['email']}"):
                        # テスト用の仮ログイン
                        st.session_state.authenticated = True
                        st.session_state.user_info = {
                            "user_id": f"test-{user['email'].split('@')[0]}",
                            "mail_address": user['email'],
                            "user_name": user['name']
                        }
                        st.rerun()
    
    else:
        # ログイン済みの場合
        st.header("🎉 ログイン済み")
        
        if st.session_state.user_info:
            st.success(f"ようこそ、{st.session_state.user_info['user_name']}さん！")
            
            # ユーザー情報表示
            st.subheader("📋 ユーザー情報")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**ユーザーID:** {st.session_state.user_info['user_id']}")
                st.info(f"**メールアドレス:** {st.session_state.user_info['mail_address']}")
            
            with col2:
                st.info(f"**ユーザー名:** {st.session_state.user_info['user_name']}")
                st.info("**モード:** 開発・テスト版")
        
        # ログアウトボタン
        if st.button("🚪 ログアウト"):
            result = auth.sign_out()
            if result["success"]:
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.success("ログアウトしました")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"ログアウトに失敗: {result['error']}")

if __name__ == "__main__":
    main()