import streamlit as st
from supabase import create_client
from datetime import datetime, date, time, timedelta
import numpy as np

# =====================
# 基本設定
# =====================
st.set_page_config(page_title="ねこスケジュール", layout="centered")
st.title("🐱 ねこスケジュール (Supabase版)")

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
        return res.data if res.data else []
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
        start_date = st.date_input("開始日", today)
        start_time_input = st.time_input("開始時刻", time(19, 0))
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

        start_at_planned = datetime.combine(start_date, start_time_input)
        deadline_dt = datetime.combine(deadline_date, deadline_time)

        new_task = {
            "id": int(datetime.now().timestamp() * 1000),
            "title": title,
            "start_at_planned": start_at_planned.isoformat(),
            "planned": planned,
            "predicted": predicted,
            "deadline": deadline_dt.isoformat(),
            "done": False,
            "working": False,
            "start_at": None,
            "log": []
        }

        try:
            supabase.table("todos").insert(new_task).execute()
            st.success(f"🧠 AI予測：{predicted}分くらいにゃ！")
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
    st.info("まだタスクがないにゃ 🐾")

for t in tasks:
    try:
        start_dt = datetime.fromisoformat(t["start_at_planned"])
        deadline_dt = datetime.fromisoformat(t["deadline"])
        remaining = max(int((start_dt - now).total_seconds() // 60), 0)
    except Exception:
        continue

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
            {status} <b>{t['title']}</b><br>
            ⏰ 開始目安：{start_dt.strftime('%m/%d %H:%M')}（あと {remaining} 分）<br>
            🧠 AI予測：{t['predicted']}分 / 🧩 予定：{t['planned']}分<br>
            📅 期限：{deadline_dt.strftime('%m/%d %H:%M')}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # 開始
        if not t["done"] and not t["working"]:
            if st.button("▶️", key=f"start_{t['id']}"):
                supabase.table("todos").update(
                    {"working": True, "start_at": datetime.now().isoformat()}
                ).eq("id", t["id"]).execute()
                st.rerun()

        # 停止
        if t["working"]:
            if st.button("⏸", key=f"stop_{t['id']}"):
                try:
                    start_real = datetime.fromisoformat(t["start_at"])
                    minutes = max(int((datetime.now() - start_real).total_seconds() // 60), 1)
                except Exception:
                    minutes = 1

                logs = t.get("log") or []
                logs.append({"time": datetime.now().isoformat(), "minutes": minutes})

                supabase.table("todos").update(
                    {"working": False, "start_at": None, "log": logs}
                ).eq("id", t["id"]).execute()

                st.success(f"{minutes}分 作業したにゃ 🐾")
                st.rerun()

        # 完了
        if not t["done"]:
            if st.button("✅", key=f"done_{t['id']}"):
                supabase.table("todos").update(
                    {"done": True}
                ).eq("id", t["id"]).execute()
                st.rerun()

        # 削除
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
        d = datetime.fromisoformat(t["start_at_planned"]).date()
        if d in dates:
            calendar[d.strftime("%m/%d")].append(t["title"])
    except Exception:
        pass

st.dataframe(
    {day: [" / ".join(v)] for day, v in calendar.items()},
    use_container_width=True
)
