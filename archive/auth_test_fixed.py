import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth
import time

def main():
    st.title("🔐 バーコードバトラー認証テスト（修正版）")
    
    # 認証システムの初期化
    auth = BarcodeBattlerAuth()
    
    # セッション状態の確認
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # 重要な設定確認セクション
    st.sidebar.title("🚨 重要な設定確認")
    st.sidebar.markdown("""
    **Supabaseの設定を確認してください:**
    
    1. **Authentication > Settings**
    2. **Email Auth セクション**
    3. **「Enable email confirmations」を❌OFF**
    4. **Save をクリック**
    
    設定後、既存のテストユーザーを削除してください。
    """)
    
    if st.sidebar.button("🔍 認証設定を確認"):
        settings = auth.check_auth_settings()
        if settings["success"]:
            st.sidebar.success("✅ 接続確認完了")
            st.sidebar.json(settings)
        else:
            st.sidebar.error(f"❌ 接続エラー: {settings['message']}")
    
    # サイドバーで機能選択
    st.sidebar.title("機能選択")
    
    if not st.session_state.authenticated:
        mode = st.sidebar.selectbox(
            "モードを選択:",
            ["新規登録", "ログイン", "設定確認"]
        )
        
        if mode == "新規登録":
            st.header("🆕 新規ユーザー登録")
            
            st.info("📧 **設定確認**: Supabaseでメール確認を無効化してから実行してください")
            
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
                                
                                # 自動的にログイン状態に
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
            
            st.info("🔧 **ログインできない場合**: Supabaseの「Enable email confirmations」が無効化されているか確認してください")
            
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
                            
                            # 具体的な解決方法を表示
                            st.warning("🚨 **解決方法:**")
                            st.info("1. Supabase Dashboard > Authentication > Settings")
                            st.info("2. 「Enable email confirmations」を❌OFFに設定")
                            st.info("3. 既存のテストユーザーを削除")
                            st.info("4. 新規登録から再実行")
                            
                            # デバッグ情報表示
                            if "debug_info" in result:
                                with st.expander("🔧 デバッグ情報"):
                                    st.code(f"エラー詳細: {result['debug_info']}")
                    else:
                        st.error("メールアドレスとパスワードを入力してください")
        
        elif mode == "設定確認":
            st.header("🔧 設定確認")
            
            st.markdown("""
            ## Supabaseの設定手順
            
            ### 1. メール確認の無効化
            
            1. **Supabaseダッシュボードにアクセス**
            2. **Authentication > Settings**
            3. **Email Auth セクションで:**
               - ✅ 「Enable email confirmations」を**❌OFF**
               - ✅ 「Save」をクリック
            
            ### 2. 既存ユーザーの削除
            
            1. **Authentication > Users**
            2. **テスト用ユーザーをすべて削除**
            
            ### 3. 動作確認
            
            - 新規登録が即座に完了
            - ログインが正常に動作
            
            ### 4. 現在の制限について
            
            表示されている「Email rate-limits and restrictions」は：
            - **無料プランの制限**: 1時間に30通まで
            - **本番環境**: カスタムSMTPプロバイダー推奨
            - **開発環境**: メール確認無効化で解決
            """)
            
            if st.button("接続テスト"):
                settings = auth.check_auth_settings()
                if settings["success"]:
                    st.success("✅ Supabase接続OK")
                    st.json(settings)
                else:
                    st.error(f"❌ 接続エラー: {settings['message']}")
    
    else:
        # ログイン済みの場合
        st.header("🎉 ログイン成功！")
        
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
                st.success("**状態:** 認証完了")
        
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