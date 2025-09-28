def create_fully_unified_user_profile(auth_user_id: str, email: str, full_name: str = ""):
    """
    完全統一版：Auth UIDをそのままuser_idとして使用
    """
    try:
        profile_data = {
            "user_id": auth_user_id,  # Auth UIDをそのままuser_idとして使用
            "auth_user_id": auth_user_id,  # 互換性のため同じ値を設定
            "mail_address": email,
            "user_name": full_name or email.split('@')[0],
            "location": ""
        }
        
        response = supabase.table('users').insert(profile_data).execute()
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"統一プロフィール作成エラー: {str(e)}")
        return None

def save_character_with_auth_uid(character_data: dict):
    """
    完全統一版：Auth UIDを直接使用してキャラクター保存
    """
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("認証情報が見つかりません")
        return False
    
    try:
        # Auth UIDを直接使用
        character_data["user_id"] = st.session_state.user.id
        
        response = supabase.table('user_operations').insert(character_data).execute()
        
        if response.data:
            st.success("キャラクターを保存しました！")
            return True
        else:
            st.error("キャラクター保存に失敗しました")
            return False
            
    except Exception as e:
        st.error(f"キャラクター保存エラー: {str(e)}")
        return False