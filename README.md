# 🐱 スケジュール管理アプリ

## 概要
「スケジュール管理」は、作業予定・期限・実作業時間を管理できる  
**学習用タスク管理Webアプリ**です。

Streamlit と Supabase を用いて開発しており、  
タスクの登録・進捗管理・作業ログの記録をブラウザ上で行えます。

---

## 主な機能

- タスクの追加（開始予定日時・期限日時・予定作業時間）
- タスク一覧表示
- 作業開始／一時停止／完了操作
- 実作業時間の記録（ログ）
- 過去ログをもとにした **AIによる作業時間予測**
- 1週間分のタスクを確認できる簡易カレンダー表示

---

## 使用技術

- Python
- Streamlit
- Supabase（PostgreSQL）
- NumPy

---

## アプリURL（試用はこちら）

👉 **https://blank-app-hvwfy2j0g5.streamlit.app/**

※ Streamlit Cloud 上で公開しています

---

## 起動方法（ローカル実行）

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
