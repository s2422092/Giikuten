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

    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- travel_plan 情報 ---
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

        # --- 日ごとの行程取得 ---
        cur.execute("""
            SELECT id, day_number, theme, route_summary, total_time, estimated_cost
            FROM day_plans
            WHERE travel_plan_id = %s
            ORDER BY day_number
        """, (plan_id,))
        day_plans_rows = cur.fetchall()

        day_plans = []
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

            # --- places（時間順）---
            cur.execute("""
                SELECT id, time, name, description, stay_time, access, map_url, cost_estimate, type
                FROM places
                WHERE day_plan_id = %s
                ORDER BY 
                    (CASE WHEN time IS NULL OR time = '' THEN 1 ELSE 0 END),
                    CASE 
                        WHEN time ~ '^[0-9]{1,2}:[0-9]{2}$' THEN to_timestamp(time, 'HH24:MI')
                        ELSE NULL
                    END ASC,
                    id
            """, (day_id,))
            for p in cur.fetchall():
                day_data["places"].append({
                    "id": p[0],
                    "time": p[1] or "",
                    "name": p[2] or "",
                    "description": p[3] or "",
                    "stay_time": p[4] or "",
                    "access": p[5] or "",
                    "map_url": p[6] or "",
                    "cost_estimate": p[7] if p[7] is not None else None,
                    "type": p[8] or ""
                })
            day_plans.append(day_data)

        # --- 予算情報 ---
        cur.execute("""
            SELECT category, amount, description
            FROM budget_items
            WHERE travel_plan_id = %s
            ORDER BY id
        """, (plan_id,))
        budget_items = [
            {"category": b[0], "amount": b[1], "description": b[2]}
            for b in cur.fetchall()
        ]

        # ✅ --- travel_plan_id からホテル情報を取得 ---
        cur.execute("""
            SELECT p.name, p.cost_estimate
            FROM places p
            JOIN day_plans d ON p.day_plan_id = d.id
            WHERE d.travel_plan_id = %s
            AND LOWER(COALESCE(p.type, '')) IN ('hotel', '宿泊', 'lodging', 'inn', '旅館', '宿')
            ORDER BY p.id
        """, (plan_id,))
        hotel_rows = cur.fetchall()

        # --- 宿泊情報構築 ---
        lodging_items = []
        if hotel_rows:
            for name, cost in hotel_rows:
                lodging_items.append({
                    "hotel_name": name or "宿泊施設",
                    "hotel_cost": cost or 0
                })
        else:
            lodging_items.append({
                "hotel_name": "宿泊施設情報が登録されていません。",
                "hotel_cost": 0
            })

        # --- 宿泊費カテゴリに統合 ---
        for b in budget_items:
            if b["category"] == "宿泊費":
                for l in lodging_items:
                    b["hotel_name"] = l["hotel_name"]
                    b["hotel_cost"] = l["hotel_cost"]
                break
        else:
            budget_items.append({
                "category": "宿泊費",
                "amount": 0,
                "description": "宿泊費未設定",
                "hotel_name": lodging_items[0]["hotel_name"],
                "hotel_cost": lodging_items[0]["hotel_cost"]
            })

        # --- ✅ ターミナル出力（確認用） ---
        print("===== 宿泊費カテゴリ（travel_plan_id 検索） =====")
        print(f"travel_plan_id = {plan_id}")
        for b in budget_items:
            if b["category"] == "宿泊費":
                print(f"宿泊施設: {b.get('hotel_name')} / 金額: {b.get('hotel_cost')}円 / 記述: {b.get('description')}")

    except Exception as e:
        print("ERROR in travel_schedule:", e)
        flash("旅行データの読み込み中にエラーが発生しました。", "error")
        return redirect(url_for("setting.setting"))
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
        budget_items=budget_items,
        lodging_items=lodging_items
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