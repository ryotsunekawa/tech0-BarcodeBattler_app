import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth
import time

def main():
    st.title("🔐 バーコードバトラー認証テスト")
    
    # 認証システムの初期化
    auth = BarcodeBattlerAuth()
    
    # セッション状態の確認
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # サイドバーで機能選択
    st.sidebar.title("機能選択")
    
    if not st.session_state.authenticated:
        mode = st.sidebar.selectbox(
            "モードを選択:",
            ["新規登録", "ログイン"]
        )
        
        if mode == "新規登録":
            st.header("🆕 新規ユーザー登録")
            
            with st.form("signup_form"):
                email = st.text_input("メールアドレス", placeholder="your-email@example.com")
                password = st.text_input("パスワード", type="password", help="6文字以上で設定してください")
                full_name = st.text_input("ユーザー名", placeholder="山田太郎")
                
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
                                    
                                # メール確認が必要な場合の処理
                                if result.get('needs_email_confirmation', False):
                                    st.warning("📧 **メール確認が必要です**")
                                    st.info("登録したメールアドレスに確認メールを送信しました。")
                                    st.info("メール内のリンクをクリックして、アカウントを有効化してください。")
                                    
                                    # 確認メール再送信ボタン
                                    if st.button("📬 確認メールを再送信"):
                                        resend_result = auth.resend_confirmation(email)
                                        if resend_result["success"]:
                                            st.success(resend_result["message"])
                                        else:
                                            st.error(resend_result["message"])
                                else:
                                    # メール確認済みの場合は自動ログイン
                                    st.session_state.authenticated = True
                                    st.session_state.user_info = result['user']
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error(f"❌ 登録失敗: {result['error']}")
                    else:
                        st.error("全ての項目を入力してください")
        
        elif mode == "ログイン":
            st.header("🔑 ログイン")
            
            # 既存ユーザーの例を表示
            with st.expander("テスト用既存ユーザー"):
                st.write("以下のユーザーでテストできます:")
                st.code("""
tanaka@example.com
yamada@example.com
sato@example.com
suzuki@example.com
                """)
                st.warning("⚠️ これらのユーザーはまだSupabase Authに登録されていない可能性があります")
            
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
                            st.error(f"❌ ログイン失敗")
                            st.error(result['message'])
                            
                            # メール確認関連のエラーの場合、再送信オプションを提供
                            if "確認" in result['message'] or "confirmation" in result['error'].lower():
                                st.info("💡 **解決方法:**")
                                st.info("1. メールボックス（迷惑メールフォルダも含む）を確認")
                                st.info("2. 確認メール内のリンクをクリック")
                                st.info("3. 下のボタンで確認メールを再送信")
                                
                                if st.button("📬 確認メール再送信"):
                                    resend_result = auth.resend_confirmation(email)
                                    if resend_result["success"]:
                                        st.success(resend_result["message"])
                                    else:
                                        st.error(resend_result["message"])
                            
                            # デバッグ情報がある場合は表示
                            if "debug_info" in result:
                                with st.expander("🔧 デバッグ情報"):
                                    st.code(f"デバッグ情報: {result['debug_info']}")
                    else:
                        st.error("メールアドレスとパスワードを入力してください")
    
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
                st.info("**テーブル構造:** user_id, mail_address, user_name")
        
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