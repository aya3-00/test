import streamlit as st
from supabase import create_client
from datetime import datetime, date, time, timedelta
import numpy as np
import json

st.set_page_config(page_title="ねこスケジュール", layout="centered")
st.title("🐱 ねこスケジュール (Supabase版)")

# --- Supabase クライアント ---
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- セッションステート更新用 ---
if "refresh" not in st.session_state:
    st.session_state.refresh = False

def trigger_refresh():
    st.session_state.refresh = not st.session_state.refresh

# =====================
# タスク取得
# =====================
def get_tasks():
    try:
        response = supabase.table("todos").select("*").order("id").execute()
        return response.data if response.data else []
    except:
        return []

# =====================
# タスク追加フォーム
# =====================
st.subheader("➕ タスクを追加")

with st.form("add_task"):
    title = st.text_input("タスク名")

    col1, col2 = st.columns(2)
    today = date.today()
    now = datetime.now()
    with col1:
        deadline_date = st.date_input("期限（日付）", today)
        start_time_input = st.time_input("開始目安", time(19,0))
    with col2:
        deadline_time = st.time_input("期限（時間）", time(23,59))
        planned = st.number_input("予定作業時間（分）", 5, 600, 30, 5)

    if st.form_submit_button("追加する") and title.strip():
        # AI作業時間予測
        tasks = get_tasks()
        logs = [log["minutes"] for t in tasks if t["title"]==title for log in t.get("log", []) if "minutes" in log]
        predicted = int(np.mean(logs)) if len(logs)>=3 else int(planned*1.2)

        task_id = int(datetime.now().timestamp() * 1000)
        new_task = {
            "id": task_id,
            "title": title,
            "start_time": start_time_input.strftime("%H:%M"),
            "planned": planned,
            "predicted": predicted,
            "deadline": datetime.combine(deadline_date, deadline_time).isoformat(),
            "done": False,
            "working": False,
            "start_at": None,
            "log": []
        }
        try:
            supabase.table("todos").insert(new_task).execute()
            st.success(f"🧠 AI予測：{predicted}分くらいにゃ！")
            trigger_refresh()
        except Exception as e:
            st.error(f"タスク追加失敗: {e}")

# =====================
# タスク一覧表示
# =====================
st.divider()
st.subheader("📋 タスク一覧")
tasks = get_tasks()
if not tasks:
    st.info("まだタスクがないにゃ 🐾")

for t in tasks:
    try:
        deadline_dt = datetime.fromisoformat(str(t["deadline"]))
    except:
        continue

    start_dt = datetime.combine(today, datetime.strptime(t.get("start_time", "00:00"), "%H:%M").time())
    remaining = int((start_dt - now).total_seconds()//60)
    
    if t.get("done"):
        status = "✅"
    elif t.get("working"):
        status = "🐱‍💻"
    elif deadline_dt < now:
        status = "🔥"
    else:
        status = "⏳"

    col1, col2 = st.columns([5,2])
    with col1:
        st.markdown(
            f"""
            <div style="background:#f4f4f4;padding:12px;border-radius:12px">
            {status} <b>{t['title']}</b><br>
            ⏰ 開始目安：{t['start_time']}（あと {remaining} 分）<br>
            🧠 AI予測：{t['predicted']}分 / 🧩 予定：{t['planned']}分<br>
            📅 期限：{deadline_dt.strftime('%m/%d %H:%M')}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # 開始
        if not t.get("done") and not t.get("working"):
            if st.button("▶️", key=f"start_{t['id']}"):
                supabase.table("todos").update({"working": True, "start_at": datetime.now().isoformat()}).eq("id", t["id"]).execute()
                trigger_refresh()

        # 停止
        if t.get("working"):
            if st.button("⏸", key=f"stop_{t['id']}"):
                start_time = datetime.fromisoformat(t["start_at"])
                minutes = max(int((datetime.now()-start_time).total_seconds()//60),1)
                logs = t.get("log", [])
                logs.append({"time": datetime.now().isoformat(), "minutes": minutes})
                supabase.table("todos").update({"working": False, "start_at": None, "log": logs}).eq("id", t["id"]).execute()
                st.success(f"{minutes}分 作業したにゃ 🐾")
                trigger_refresh()

        # 完了
        if not t.get("done"):
            if st.button("✅", key=f"done_{t['id']}"):
                supabase.table("todos").update({"done": True}).eq("id", t["id"]).execute()
                trigger_refresh()

        # 削除
        if st.button("🗑", key=f"del_{t['id']}"):
            supabase.table("todos").delete().eq("id", t["id"]).execute()
            trigger_refresh()

# =====================
# 1週間カレンダー表示
# =====================
st.divider()
st.subheader("📅 1週間カレンダー")
dates = [today + timedelta(days=i) for i in range(7)]
calendar = {d.strftime("%m/%d"): [] for d in dates}
for t in tasks:
    try:
        d = datetime.fromisoformat(str(t["deadline"])).date()
        if d in dates:
            calendar[d.strftime("%m/%d")].append(t["title"])
    except:
        pass

df = {day: [" / ".join(tasks)] for day, tasks in calendar.items()}
st.dataframe(df, use_container_width=True)
