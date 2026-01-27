import streamlit as st
from supabase import create_client

st.title("Supabase 接続テスト（安全版）")

# Secrets から URL と Key を取得
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]

# Supabase クライアント作成
supabase = create_client(url, key)

# 接続テスト
try:
    # 例: todo というテーブルを取得（最大5件）
    response = supabase.table("test").select("*").limit(5).execute()
    st.success("接続成功！")
    st.write(response.data)
except Exception as e:
    st.error(f"接続失敗: {e}")
