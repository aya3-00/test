import streamlit as st
from supabase import create_client
from datetime import datetime, date, time, timedelta
import numpy as np

# =====================
# 基本設定
# =====================
st.set_page_config(page_title="スケジュール管理", layout="centered")
st.title("🐱 スケジュール管理 (Supabase版)")

# =====================
# Supabase クライアント
# =====================
url = st.secrets["general"]["SUPABASE_URL"]
key = st.secrets["general"]["SUPABASE_KEY"]
supabase = create_client(url, key)

# =====================
# 現在時刻（timezoneなしで統一）
# =====================
now = datetime.now()
today = date.today()

# =====================
# タスク取得
# =====================
def get_tasks():
    try:
        res = supabase.table("todos").select("*").order("id").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Todo取得失敗: {e}")
        return []

# =====================
# タスク追加
# =====================
st.subheader("➕ タスクを追加")

with st.form("add_task"):
    title = st.text_input("タスク名")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始予定（日付）", today)
        start_time_input = st.time_input("開始予定（時間）", time(19, 0))
    with col2:
        deadline_date = st.date_input("期限（日付）", today)
        deadline_time = st.time_input("期限（時間）", time(23, 59))

    planned = st.number_input("予定作業時間（分）", 5, 600, 30, 5)

    submitted = st.form_submit_button("追加する")

    if submitted and title.strip():
        tasks = get_tasks()

        # --- AI作業時間予測 ---
        logs = [
            log["minutes"]
            for t in tasks
            if t.get("title") == title
            for log in (t.get("log") or [])
            if isinstance(log, dict) and "minutes" in log
        ]
        predicted = int(np.mean(logs)) if len(logs) >= 3 else int(planned * 1.2)

        new_task = {
            "id": int(datetime.now().timestamp() * 1000),
            "title": title,
            "start_at_planned": datetime.combine(start_date, start_time_input).isoformat(),
            "deadline": datetime.combine(deadline_date, deadline_time).isoformat(),
            "planned": planned,
            "predicted": predicted,
            "done": False,
            "working": False,
            "start_at": None,
            "log": []
        }

        try:
            supabase.table("todos").insert(new_task).execute()
            st.success(f"🧠 AI予測：{predicted}分くらい！")
            st.rerun()
        except Exception as e:
            st.error(f"タスク追加失敗: {e}")

# =====================
# タスク一覧
# =====================
st.divider()
st.subheader("📋 タスク一覧")

tasks = get_tasks()
if not tasks:
    st.info("まだタスクがないよ～ 🐾")

for t in tasks:
    # --- deadline ---
    deadline_raw = t.get("deadline")
    if not deadline_raw:
        continue
    deadline_dt = datetime.fromisoformat(deadline_raw).replace(tzinfo=None)

    # --- start planned（NULL安全） ---
    start_raw = t.get("start_at_planned")
    if start_raw:
        start_dt = datetime.fromisoformat(start_raw).replace(tzinfo=None)
    else:
        start_dt = deadline_dt

    remaining = int((start_dt - now).total_seconds() // 60)

    if t.get("done"):
        status = "✅"
    elif t.get("working"):
        status = "🐱‍💻"
    elif deadline_dt < now:
        status = "🔥"
    else:
        status = "⏳"

    col1, col2 = st.columns([5, 2])

    with col1:
        st.markdown(
            f"""
            <div style="background:#f4f4f4;padding:12px;border-radius:12px">
            {status} <b>{t.get("title","(無題)")}</b><br>
            ⏰ 開始予定：{start_dt.strftime('%m/%d %H:%M')}（あと {remaining} 分）<br>
            🧠 AI予測：{t.get("predicted",0)}分 / 🧩 予定：{t.get("planned",0)}分<br>
            📅 期限：{deadline_dt.strftime('%m/%d %H:%M')}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        if not t.get("done") and not t.get("working"):
            if st.button("▶️", key=f"start_{t['id']}"):
                supabase.table("todos").update(
                    {"working": True, "start_at": datetime.now().isoformat()}
                ).eq("id", t["id"]).execute()
                st.rerun()

        if t.get("working"):
            if st.button("⏸", key=f"stop_{t['id']}"):
                start = datetime.fromisoformat(t["start_at"])
                minutes = max(int((datetime.now() - start).total_seconds() // 60), 1)

                logs = t.get("log") or []
                logs.append({"time": datetime.now().isoformat(), "minutes": minutes})

                supabase.table("todos").update(
                    {"working": False, "start_at": None, "log": logs}
                ).eq("id", t["id"]).execute()

                st.success(f"{minutes}分 作業したにゃ 🐾")
                st.rerun()

        if not t.get("done"):
            if st.button("✅", key=f"done_{t['id']}"):
                supabase.table("todos").update(
                    {"done": True}
                ).eq("id", t["id"]).execute()
                st.rerun()

        if st.button("🗑", key=f"del_{t['id']}"):
            supabase.table("todos").delete().eq("id", t["id"]).execute()
            st.rerun()

# =====================
# 1週間カレンダー
# =====================
st.divider()
st.subheader("📅 1週間カレンダー")

dates = [today + timedelta(days=i) for i in range(7)]
calendar = {d.strftime("%m/%d"): [] for d in dates}

for t in tasks:
    try:
        d = datetime.fromisoformat(t["deadline"]).date()
        if d in dates:
            calendar[d.strftime("%m/%d")].append(t["title"])
    except:
        pass

st.dataframe(
    {day: [" / ".join(v)] for day, v in calendar.items()},
    use_container_width=True
)
