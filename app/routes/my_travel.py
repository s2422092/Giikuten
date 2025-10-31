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
# app/routes/my_travel.py
from flask import (
    Blueprint, render_template, session, redirect, url_for, flash
)
import psycopg2
from app.user_icon import get_user_icon
import json
import os

my_travel_bp = Blueprint(
    "my_travel", __name__, url_prefix="/my_travel", template_folder="../../templates"
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@my_travel_bp.route("/travel_schedule/<int:plan_id>")
def travel_schedule(plan_id: int):
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)

    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- 旅行プラン情報 ---
        cur.execute("""
            SELECT id, title, summary, total_budget,
                   budget_transport, budget_lodging, budget_food,
                   budget_activities, budget_other, overview,
                   lodging_suggestions, return_trip
            FROM travel_plans
            WHERE id = %s
        """, (plan_id,))
        row = cur.fetchone()
        if not row:
            flash("指定された旅行プランが見つかりません。", "error")
            return redirect(url_for("home.home"))

        plan = {
            "id": row[0],
            "title": row[1],
            "summary": row[2],
            "total_budget": row[3],
            "budget_transport": row[4],
            "budget_lodging": row[5],
            "budget_food": row[6],
            "budget_activities": row[7],
            "budget_other": row[8],
            "overview": row[9],
            "lodging_suggestions": json.loads(row[10] or "[]"),
            "return_trip": json.loads(row[11] or "{}"),
        }

        # --- budget_items 取得 ---
        cur.execute("""
            SELECT category, amount, description
            FROM budget_items
            WHERE travel_plan_id = %s
            ORDER BY id
        """, (plan_id,))
        budget_items = [{"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()]

        # --- day_plans + places ---
        cur.execute("""
            SELECT id, day_number, theme, route_summary
            FROM day_plans
            WHERE travel_plan_id = %s
            ORDER BY day_number
        """, (plan_id,))
        day_plans_rows = cur.fetchall()
        day_plans = []

        for d in day_plans_rows:
            day_id = d[0]
            day_data = {
                "id": day_id,
                "day_number": d[1],
                "theme": d[2],
                "route_summary": d[3],
                "places": []
            }

            cur.execute("""
                SELECT name, time, description, stay_time, access, map_url, cost_estimate, type, fun_fact, leave_time
                FROM places
                WHERE day_plan_id = %s
                ORDER BY id
            """, (day_id,))

            places_rows = cur.fetchall()
            for p in places_rows:
                place = {
                    "name": p[0],
                    "time": p[1],
                    "description": p[2],
                    "stay_time": p[3],
                    "access": p[4],
                    "map_url": p[5],
                    "cost_estimate": p[6],
                    "type": p[7],
                    "fun_fact": p[8],
                    "leave_time": p[9],
                }
                day_data["places"].append(place)

            day_plans.append(day_data)

        # --- places からホテル情報を取得して budget_items に統合 ---
        cur.execute("""
            SELECT p.name, p.cost_estimate
            FROM places p
            JOIN day_plans d ON p.day_plan_id = d.id
            WHERE d.travel_plan_id = %s AND LOWER(p.type) IN ('hotel','宿泊','ホテル','lodging','inn','宿')
            ORDER BY d.day_number, p.id
        """, (plan_id,))
        hotels = [{"hotel_name": h[0], "hotel_cost": h[1] or 0} for h in cur.fetchall()]

        for item in budget_items:
            if item["category"] == "宿泊費":
                item["lodging_details"] = hotels
                if hotels:
                    item["amount"] = sum(h["hotel_cost"] for h in hotels)
                    item["description"] = ", ".join([h["hotel_name"] for h in hotels])
                else:
                    item["description"] = "（ホテル情報なし）"

    except Exception as e:
        print("ERROR in travel_schedule:", e)
        flash("旅行データの読み込み中にエラーが発生しました。", "error")
        return redirect(url_for("home.home"))
    finally:
        if cur:
            cur.close()
        if conn:
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