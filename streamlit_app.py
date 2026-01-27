import streamlit as st
from supabase import create_client

st.title("Supabase 接続テスト")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

try:
    # supabase のバージョンによっては .from_() も使う
    res = supabase.table("todos").select("*").limit(1).execute()
    st.write("接続成功！", res.data)
except Exception as e:
    st.error(f"接続失敗: {e}")
