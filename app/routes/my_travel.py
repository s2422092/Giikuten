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



@my_travel_bp.route("/travel_details")
def travel_details():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)  # ←ここでアイコン取得

    return render_template(
        "my_travel/travel_details.html",
        username=username,
        user_icon=user_icon
    )

@my_travel_bp.route("/travel_schedule/<int:plan_id>")
def travel_schedule(plan_id):
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)

    conn = get_conn()
    cur = conn.cursor()

    # --- ① 旅行プラン情報（travel_plans + travel_requests） ---
    cur.execute("""
        SELECT 
            tp.id, tp.title, tp.summary, tp.total_budget,
            tr.trip_name, tr.start_date, tr.end_date, tr.region,
            tr.prefecture, tr.city, tr.departure, tr.transport_pref,
            tr.budget, tr.must_visit, tr.notes
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tp.id = %s AND tr.user_id = %s
    """, (plan_id, user_id))
    plan = cur.fetchone()

    if not plan:
        cur.close()
        conn.close()
        return "指定された旅行プランが見つかりません。", 404

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

    # --- ② 日別行程（day_plans） ---
    cur.execute("""
        SELECT id, day_number, theme, route_summary, total_time, estimated_cost
        FROM day_plans
        WHERE travel_plan_id = %s
        ORDER BY day_number
    """, (plan_id,))
    days = cur.fetchall()

    day_list = []
    for d in days:
        day_id = d[0]
        # --- ③ 各日の観光地（places） ---
        cur.execute("""
            SELECT id, time, name, description, stay_time, access, map_url, cost_estimate, type
            FROM places
            WHERE day_plan_id = %s
            ORDER BY time
        """, (day_id,))
        places = cur.fetchall()

        place_list = [
            {
                "id": p[0],
                "time": p[1],
                "name": p[2],
                "description": p[3],
                "stay_time": p[4],
                "access": p[5],
                "map_url": p[6],
                "cost_estimate": p[7],
                "type": p[8],
            }
            for p in places
        ]

        day_list.append({
            "day_number": d[1],
            "theme": d[2],
            "route_summary": d[3],
            "total_time": d[4],
            "estimated_cost": d[5],
            "places": place_list
        })

    # --- ④ 予算情報（budget_items） ---
    cur.execute("""
        SELECT category, amount, description
        FROM budget_items
        WHERE travel_plan_id = %s
    """, (plan_id,))
    budget_items = [
        {"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()
    ]

    # --- ⑤ 宿泊情報（places.type = 'hotel'） ---
    cur.execute("""
        SELECT name, description, stay_time, access
        FROM places
        WHERE day_plan_id IN (
            SELECT id FROM day_plans WHERE travel_plan_id = %s
        ) AND type = 'hotel'
    """, (plan_id,))
    hotel_info = [
        {"name": h[0], "description": h[1], "stay_time": h[2], "access": h[3]}
        for h in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template(
        "my_travel/travel_schedule.html",
        username=username,
        user_icon=user_icon,
        plan=plan_data,
        days=day_list,
        budget_items=budget_items,
        hotels=hotel_info
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