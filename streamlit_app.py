import streamlit as st
from supabase import create_client

st.title("Supabase 接続テスト")

# TOML で [general] セクションを使った場合
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]

supabase = create_client(url, key)

# 例: todo テーブルを読む
try:
    response = supabase.table("todos").select("*").limit(5).execute()
    st.write(response.data)
except Exception as e:
    st.error(f"接続失敗: {e}")
