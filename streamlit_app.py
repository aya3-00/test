import streamlit as st
from supabase import create_client

st.title("Supabase Todo リストアプリ")

# Supabase クライアント作成
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]
supabase = create_client(url, key)

# Todo の追加
with st.form("add_todo"):
    new_task = st.text_input("新しいタスク")
    submitted = st.form_submit_button("追加")
    if submitted and new_task.strip():
        supabase.table("Todos").insert({"task": new_task, "is_complete": False}).execute()
        st.success(f"タスク追加: {new_task}")

# Todo の取得
response = supabase.table("Todos").select("*").order("id").execute()
todos = response.data if response.data else []

st.subheader("タスクリスト")
for todo in todos:
    col1, col2, col3 = st.columns([4,1,1])
    with col1:
        checkbox = st.checkbox(todo["task"], value=todo["is_complete"], key=todo["id"])
        if checkbox != todo["is_complete"]:
            # 完了状態を更新
            supabase.table("Todos").update({"is_complete": checkbox}).eq("id", todo["id"]).execute()
            st.experimental_rerun()
    with col2:
        if st.button("削除", key=f"del-{todo['id']}"):
            supabase.table("Todos").delete().eq("id", todo["id"]).execute()
            st.experimental_rerun()
