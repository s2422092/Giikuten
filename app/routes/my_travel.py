# app/routes/index.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # ← .envファイルの内容を読み込む

my_travel_bp = Blueprint("my_travel", __name__)

# DB接続設定を環境変数から取得
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def get_user_icon(user_id):
    """
    user_iconsテーブルから指定ユーザーの最新アイコンを取得し、
    ブラウザで表示可能な形式のdata URIに変換して返す。
    未設定の場合はデフォルト画像URLを返す。
    """
    DEFAULT_ICON_URL = "https://cdn-icons-png.flaticon.com/512/847/847969.png"
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT icon_base64
            FROM user_icons
            WHERE user_id = %s
            ORDER BY uploaded_at DESC
            LIMIT 1
        """, (user_id,))
        result = cur.fetchone()
        cur.close()

        if result and result[0]:
            return f"data:image/png;base64,{result[0]}"
        
        return DEFAULT_ICON_URL

    except Exception as e:
        print(f"アイコン取得エラー: {e}")
        return DEFAULT_ICON_URL
    finally:
        if conn:
            conn.close()



@my_travel_bp.route("/travel_details/<int:plan_id>")
def travel_details(plan_id):
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)

    conn = get_conn()
    cur = conn.cursor()

    # ✅ travel_plans と travel_requests を結合して1件の詳細を取得
    cur.execute("""
        SELECT 
            tp.id,
            tp.title,
            tp.summary,
            tp.total_budget,
            tr.trip_name,
            tr.start_date,
            tr.end_date,
            tr.region,
            tr.prefecture,
            tr.city,
            tr.departure,
            tr.transport_pref,
            tr.budget,
            tr.must_visit,
            tr.notes
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tp.id = %s AND tr.user_id = %s
    """, (plan_id, user_id))

    plan = cur.fetchone()
    cur.close()
    conn.close()

    if not plan:
        return "指定された旅行プランが見つかりません。", 404

    # ✅ データ整形
    plan_data = {
        "id": plan[0],
        "title": plan[1],
        "summary": plan[2],
        "total_budget": plan[3],
        "trip_name": plan[4],
        "start_date": plan[5],
        "end_date": plan[6],
        "region": plan[7],
        "prefecture": plan[8],
        "city": plan[9],
        "departure": plan[10],
        "transport_pref": plan[11],
        "budget": plan[12],
        "must_visit": plan[13],
        "notes": plan[14],
    }

    # ✅ テンプレートに渡す
    return render_template(
        "my_travel/travel_details.html",
        username=username,
        user_icon=user_icon,
        plan=plan_data
    )


@my_travel_bp.route("/budget")
def budget():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)  # ←ここでアイコン取得

    return render_template(
        "my_travel/budget.html",
        username=username,
        user_icon=user_icon
    )