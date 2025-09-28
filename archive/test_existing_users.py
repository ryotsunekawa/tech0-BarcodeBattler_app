"""
既存ユーザーデータとの連携テスト

CSV確認済みの既存ユーザー:
- tanaka@example.com (田中太郎)
- yamada@example.com (山田一郎) 
- watanabe@example.com (渡辺健司)
- suzuki@example.com (鈴木美咲)
- sato@example.com (佐藤花子)
"""

import streamlit as st
from barcode_battler_auth import BarcodeBattlerAuth

def existing_user_test():
    """既存ユーザーとの連携テスト"""
    st.title("🔗 既存ユーザー連携テスト")
    
    auth = BarcodeBattlerAuth()
    
    st.header("既存ユーザー情報（CSV確認済み）")
    existing_users = [
        {"email": "tanaka@example.com", "name": "田中太郎", "location": "東京都"},
        {"email": "yamada@example.com", "name": "山田一郎", "location": "愛知県"},
        {"email": "watanabe@example.com", "name": "渡辺健司", "location": "北海道"},
        {"email": "suzuki@example.com", "name": "鈴木美咲", "location": "福岡県"},
        {"email": "sato@example.com", "name": "佐藤花子", "location": "大阪府"}
    ]
    
    for user in existing_users:
        st.write(f"📧 {user['email']} - {user['name']} ({user['location']})")
    
    st.header("既存ユーザーログインテスト")
    
    selected_user = st.selectbox(
        "テスト用ユーザー選択", 
        existing_users,
        format_func=lambda x: f"{x['email']} ({x['name']})"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. 新規Supabase認証アカウント作成")
        test_password = st.text_input("パスワード設定", value="test123456", type="password")
        
        if st.button("🆕 認証アカウント作成"):
            result = auth.sign_up(
                selected_user['email'], 
                test_password, 
                selected_user['name']
            )
            st.json(result)
            
            if result.get('success'):
                st.success("✅ Supabase認証アカウント作成完了")
                st.info("📧 メール認証後、ログインテストを実行してください")
    
    with col2:
        st.subheader("2. 既存ユーザーログインテスト")
        login_password = st.text_input("ログイン用パスワード", value="test123456", type="password", key="login_pass")
        
        if st.button("🔐 ログインテスト"):
            result = auth.sign_in(selected_user['email'], login_password)
            st.json(result)
            
            if result.get('success'):
                st.success("✅ 既存ユーザーとの連携成功！")
                st.write("セッション情報:")
                st.write(f"- ユーザー名: {st.session_state.get('full_name')}")
                st.write(f"- DB user_id: {st.session_state.get('user_id')}")
                st.json(st.session_state.get('user_data'))
    
    if auth.is_authenticated():
        st.header("認証後の操作テスト")
        
        # 既存のキャラクター一覧表示
        user_data = st.session_state.get('user_data')
        if user_data:
            user_id = user_data['user_id']
            
            try:
                # user_operationsから該当ユーザーのデータを取得
                operations = auth.supabase.table('user_operations').select('*').eq('user_id', user_id).execute()
                
                if operations.data:
                    st.subheader(f"🎮 {user_data['user_name']}さんのキャラクター")
                    for op in operations.data:
                        with st.expander(f"{op['character_name']} - {op['item_name']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                if op['character_img_url']:
                                    st.image(op['character_img_url'], width=150)
                            with col2:
                                st.write(f"バーコード: {op['code_number']}")
                                if op['character_parameter']:
                                    params = op['character_parameter']
                                    st.write(f"攻撃力: {params.get('attack')}")
                                    st.write(f"属性: {params.get('element')}")
                                    st.write(f"レアリティ: {params.get('rarity')}")
                else:
                    st.info("まだキャラクターがありません")
            except Exception as e:
                st.error(f"キャラクター取得エラー: {str(e)}")
        
        if st.button("🚪 ログアウト"):
            auth.sign_out()
            st.rerun()


if __name__ == "__main__":
    existing_user_test()