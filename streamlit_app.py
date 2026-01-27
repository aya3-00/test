import streamlit as st
from supabase import create_client

st.title("Supabase 接続テスト")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 例: todo というテーブルを読む
response = supabase.table("todos").select("*").limit(5).execute()

st.write(response.data)
