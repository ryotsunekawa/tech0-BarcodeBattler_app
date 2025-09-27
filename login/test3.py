#諦めた残骸

import streamlit as st
import os, io, re, json, base64, zipfile, random
from supabase import create_client, AuthApiError

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

email = "example@example.com"

try:
    res = supabase.from_("auth.users").select("*").eq("email", email).execute()
    if res.data:
        st.write("登録済み")
    else:
        st.write("未登録")
except Exception as e:
    st.error(f"エラー発生: {str(e)}")