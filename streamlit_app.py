import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Supabase Todo App")
st.title("Supabase Todo リストアプリ")

# --- Supabase クライアント作成 ---
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Todo 追加フォーム ---
with st.form("add_todo"):
    new_task = st.text_input("新しいタスク")
    submitted = st.form_submit_button("追加")
    if submitted and new_task.strip():
        try:
            supabase.table("todos").insert({"task": new_task, "is_complete": False}).execute()
            st.success(f"タスク追加: {new_task}")
            st.experimental_refresh()  # ← 最新版対応
        except Exception as e:
            st.error(f"タスク追加に失敗: {e}")

# --- Todo 取得 ---
try:
    response = supabase.table("todos").select("*").order("id").execute()
    todos = response.data if response.data else []
except Exception as e:
    st.error(f"Todo取得失敗: {e}")
    todos = []

# --- Todo 表示・操作 ---
st.subheader("タスクリスト")
for todo in todos:
    col1, col2 = st.columns([4,1])
    with col1:
        checkbox = st.checkbox(todo["task"], value=todo["is_complete"], key=f"chk-{todo['id']}")
        if checkbox != todo["is_complete"]:
            try:
                supabase.table("todos").update({"is_complete": checkbox}).eq("id", todo["id"]).execute()
                st.experimental_refresh()  # ← 最新版対応
            except Exception as e:
                st.error(f"更新失敗: {e}")
    with col2:
        if st.button("削除", key=f"del-{todo['id']}"):
            try:
                supabase.table("todos").delete().eq("id", todo["id"]).execute()
                st.experimental_refresh()  # ← 最新版対応
            except Exception as e:
                st.error(f"削除失敗: {e}")
