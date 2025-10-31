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

    # --- 旅行プラン情報 ---
    cur.execute("""
        SELECT 
            tp.id, tp.title, tp.summary, tp.total_budget,
            tp.budget_transport, tp.budget_lodging, tp.budget_food, tp.budget_activities, tp.budget_other,
            tr.trip_name, tr.start_date, tr.end_date, tr.region, tr.prefecture, tr.city, tr.departure, tr.transport_pref,
            tr.must_visit, tr.notes
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tp.id = %s AND tr.user_id = %s
    """, (plan_id, user_id))
    plan_row = cur.fetchone()
    if not plan_row:
        cur.close()
        conn.close()
        return "指定された旅行プランが見つかりません。", 404

    plan = {
        "id": plan_row[0],
        "title": plan_row[1],
        "summary": plan_row[2],
        "total_budget": plan_row[3],
        "budget_transport": plan_row[4],
        "budget_lodging": plan_row[5],
        "budget_food": plan_row[6],
        "budget_activities": plan_row[7],
        "budget_other": plan_row[8],
        "trip_name": plan_row[9],
        "start_date": plan_row[10],
        "end_date": plan_row[11],
        "region": plan_row[12],
        "prefecture": plan_row[13],
        "city": plan_row[14],
        "departure": plan_row[15],
        "transport_pref": plan_row[16],
        "must_visit": plan_row[17],
        "notes": plan_row[18],
    }

    # --- 1日ごとの行程 ---
    cur.execute("""
        SELECT id, day_number, theme, route_summary, total_time, estimated_cost
        FROM day_plans
        WHERE travel_plan_id = %s
        ORDER BY day_number
    """, (plan_id,))
    day_plans_rows = cur.fetchall()

    day_plans = []
    for day in day_plans_rows:
        day_id = day[0]
        day_data = {
            "id": day_id,
            "day_number": day[1],
            "theme": day[2],
            "route_summary": day[3],
            "total_time": day[4],
            "estimated_cost": day[5],
            "places": []
        }

        # --- その日の観光地・レストランなど ---
        cur.execute("""
            SELECT time, name, description, stay_time, access, map_url, cost_estimate, type
            FROM places
            WHERE day_plan_id = %s
            ORDER BY time
        """, (day_id,))
        places_rows = cur.fetchall()
        day_data["places"] = [
            {
                "time": p[0],
                "name": p[1],
                "description": p[2],
                "stay_time": p[3],
                "access": p[4],
                "map_url": p[5],
                "cost_estimate": p[6],
                "type": p[7]
            }
            for p in places_rows
        ]

        day_plans.append(day_data)

    # --- 予算情報 ---
    cur.execute("""
        SELECT category, amount, description
        FROM budget_items
        WHERE travel_plan_id = %s
    """, (plan_id,))
    budget_items = [{"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template(
        "my_travel/travel_schedule.html",
        username=username,
        user_icon=user_icon,
        plan=plan,
        day_plans=day_plans,
        budget_items=budget_items
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