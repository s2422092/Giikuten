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


def fetch_user_mbti(conn, user_id: int) :
    """
    user_mbti テーブルから当該ユーザーの最新タイプを取得。
    返却: {"code": str, "name": str, "description": str}
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT code, name, description
            FROM user_mbti
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"code": row[0], "name": row[1], "description": row[2]}


@my_travel_bp.route("/travel_schedule/<int:plan_id>")
def travel_schedule(plan_id):
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)

    conn = get_conn()
    try:
        # 最新のMBTI情報取得
        mbti_info = fetch_user_mbti(conn, user_id)
        mbti_code = (mbti_info or {}).get("code") or "バランスタイプ"

        # --- 旅行プラン情報 ---
        with conn.cursor() as cur:
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
            hotels = []
            for day_row in day_plans_rows:
                day_id = day_row[0]
                day_data = {
                    "id": day_id,
                    "day_number": day_row[1],
                    "theme": day_row[2],
                    "route_summary": day_row[3],
                    "total_time": day_row[4],
                    "estimated_cost": day_row[5],
                    "places": []
                }

                cur.execute("""
                    SELECT id, time, name, description, stay_time, access, map_url, cost_estimate, type
                    FROM places
                    WHERE day_plan_id = %s
                    ORDER BY
                        (CASE WHEN time IS NULL OR time = '' THEN 1 ELSE 0 END),
                        CASE WHEN time ~ '^[0-9]{1,2}:[0-9]{2}$' THEN to_timestamp(time, 'HH24:MI') ELSE NULL END ASC,
                        id
                """, (day_id,))
                places_rows = cur.fetchall()

                for p in places_rows:
                    place = {
                        "id": p[0],
                        "time": p[1] or "",
                        "name": p[2] or "",
                        "description": p[3] or "",
                        "stay_time": p[4] or "",
                        "access": p[5] or "",
                        "map_url": p[6] or "",
                        "cost_estimate": p[7] if p[7] is not None else None,
                        "type": p[8] or ""
                    }
                    day_data["places"].append(place)

                    t = (p[8] or "").strip().lower()
                    if t in ("hotel", "宿泊", "ホテル", "lodging", "inn", "宿"):
                        hotels.append(place)

                day_plans.append(day_data)

            # --- 予算情報 ---
            cur.execute("""
                SELECT category, amount, description
                FROM budget_items
                WHERE travel_plan_id = %s
                ORDER BY id
            """, (plan_id,))
            budget_items = [{"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()]

    finally:
        conn.close()

    # --- テンプレートに渡す ---
    return render_template(
        "my_travel/travel_schedule.html",
        username=username,
        user_icon=user_icon,
        mbti=mbti_code,
        plan=plan,
        day_plans=day_plans,
        budget_items=budget_items,
        hotels=hotels
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