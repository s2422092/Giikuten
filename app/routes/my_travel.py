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
    user_icon = get_user_icon(user_id)

    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- 1) 「保存済み（saved = TRUE）」の旅行の中で、最も近い開始日のプランを取得 ---
        cur.execute("""
            SELECT tp.id
            FROM travel_plans tp
            JOIN travel_requests tr ON tp.request_id = tr.id
            WHERE tr.user_id = %s
              AND tp.saved = TRUE               -- ★ 追加部分
              AND tr.start_date >= CURRENT_DATE
            ORDER BY tr.start_date ASC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()

        # --- 2) 保存済みの中で未来旅行がなければ、過去の保存済み旅行の中で最も近いものを取得 ---
        if not row:
            cur.execute("""
                SELECT tp.id
                FROM travel_plans tp
                JOIN travel_requests tr ON tp.request_id = tr.id
                WHERE tr.user_id = %s
                  AND tp.saved = TRUE            -- ★ 追加部分
                  AND tr.start_date < CURRENT_DATE
                ORDER BY tr.start_date DESC
                LIMIT 1
            """, (user_id,))
            row = cur.fetchone()

        # --- 3) 保存済み旅行が1件もない場合 ---
        if not row:
            flash("保存された旅行プランがありません。", "info")
            return render_template("my_travel/travel_details.html", username=username, user_icon=user_icon, plan=None)

        plan_id = row[0]

        # --- 4) travel_schedule() と同じ情報を取得（saved は含めなくてもOK） ---
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
            flash("指定された旅行プランが見つかりません。", "warning")
            return redirect(url_for("setting.setting"))

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

        # --- 日別プラン ---
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
                    CASE 
                        WHEN time ~ '^[0-9]{1,2}:[0-9]{2}$' THEN to_timestamp(time, 'HH24:MI')
                        ELSE NULL
                    END ASC,
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
                    hotels.append({
                        "id": p[0],
                        "day_plan_id": day_id,
                        "name": p[2] or "",
                        "description": p[3] or "",
                        "stay_time": p[4] or "",
                        "access": p[5] or "",
                        "map_url": p[6] or "",
                        "cost_estimate": p[7] if p[7] is not None else None
                    })

            day_plans.append(day_data)

        # --- 予算項目 ---
        cur.execute("""
            SELECT category, amount, description
            FROM budget_items
            WHERE travel_plan_id = %s
            ORDER BY id
        """, (plan_id,))
        budget_items = [{"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()]

    except Exception as e:
        print("ERROR in travel_details:", e)
        flash("旅行データの読み込み中にエラーが発生しました。", "error")
        return redirect(url_for("setting.setting"))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # --- テンプレートに渡す ---
    return render_template(
        "my_travel/travel_details.html",
        username=username,
        user_icon=user_icon,
        plan=plan,
        day_plans=day_plans,
        budget_items=budget_items,
        hotels=hotels
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

        # --- 旅行プラン情報 ---
        cur.execute("""
            SELECT 
                tp.id, tp.title, tp.summary, tp.total_budget,
                tp.budget_transport, tp.budget_lodging, tp.budget_food, tp.budget_activities, tp.budget_other,
                tp.saved,
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
            "saved": bool(plan_row[9]),
            "trip_name": plan_row[10],
            "start_date": plan_row[11],
            "end_date": plan_row[12],
            "region": plan_row[13],
            "prefecture": plan_row[14],
            "city": plan_row[15],
            "departure": plan_row[16],
            "transport_pref": plan_row[17],
            "must_visit": plan_row[18],
            "notes": plan_row[19],
        }

        # --- 各日程情報 ---
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

            cur.execute("""
                SELECT id, time, name, description, stay_time, access, map_url, cost_estimate, type
                FROM places
                WHERE day_plan_id = %s
                ORDER BY id
            """, (day_id,))
            places_rows = cur.fetchall()
            for p in places_rows:
                day_data["places"].append({
                    "id": p[0],
                    "time": p[1] or "",
                    "name": p[2] or "",
                    "description": p[3] or "",
                    "stay_time": p[4] or "",
                    "access": p[5] or "",
                    "map_url": p[6] or "",
                    "cost_estimate": p[7],
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
        budget_items = [{"category": b[0], "amount": b[1], "description": b[2]} for b in cur.fetchall()]

        # --- 宿泊情報（budget_itemsから遡る） ---
        cur.execute("""
            SELECT name, description, stay_time, access, map_url, cost_estimate
            FROM places
            WHERE type IN ('hotel', '宿泊', 'ホテル', 'lodging', 'inn', '宿')
              AND day_plan_id IN (
                  SELECT id FROM day_plans WHERE travel_plan_id = %s
              )
        """, (plan_id,))
        hotels = [
            {
                "name": h[0] or "",
                "description": h[1] or "",
                "stay_time": h[2] or "",
                "access": h[3] or "",
                "map_url": h[4] or "",
                "cost_estimate": h[5] or 0
            }
            for h in cur.fetchall()
        ]

        # 宿泊費をbudget_itemsから探して対応づけ
        for b in budget_items:
            if b["category"] == "宿泊費":
                b["hotels"] = hotels

    except Exception as e:
        print("ERROR in travel_schedule:", e)
        flash("旅行データの読み込み中にエラーが発生しました。", "error")
        return redirect(url_for("setting.setting"))
    finally:
        if cur: cur.close()
        if conn: conn.close()

    return render_template(
        "my_travel/travel_schedule.html",
        username=username,
        user_icon=user_icon,
        plan=plan,
        day_plans=day_plans,
        budget_items=budget_items
    )

from flask import jsonify, request

@my_travel_bp.route("/travel_plans/<int:plan_id>/toggle_saved", methods=["POST"])
def toggle_saved(plan_id):
    # ログインチェック
    if "user_id" not in session:
        return jsonify({"error": "login_required"}), 401

    user_id = session["user_id"]

    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # 所有者チェック：travel_requests.user_id と一致するか
        cur.execute("""
            SELECT tr.user_id, tp.saved
            FROM travel_plans tp
            JOIN travel_requests tr ON tp.request_id = tr.id
            WHERE tp.id = %s
        """, (plan_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "not_found"}), 404

        owner_id = row["user_id"]
        current_saved = bool(row["saved"])

        if owner_id != user_id:
            return jsonify({"error": "forbidden"}), 403

        # トグル（反転）
        new_saved = not current_saved
        cur.execute("""
            UPDATE travel_plans
            SET saved = %s
            WHERE id = %s
        """, (new_saved, plan_id))
        conn.commit()

        return jsonify({"ok": True, "plan_id": plan_id, "saved": new_saved}), 200

    except Exception as e:
        print("ERROR in toggle_saved:", e)
        if conn:
            conn.rollback()
        return jsonify({"error": "internal_error", "detail": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@my_travel_bp.route("/budget")
def budget():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")

    try:
        user_icon = get_user_icon(user_id)
    except Exception:
        user_icon = url_for("static", filename="img/default_user.png")

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # --- (1) まず最も近い旅行プランを取得（未来優先、なければ過去の最近） ---
    cur.execute("""
        SELECT tp.id AS plan_id, tr.start_date
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tr.user_id = %s
        AND tp.saved = TRUE  -- ← ここを追加
        ORDER BY 
            CASE 
                WHEN tr.start_date >= CURRENT_DATE THEN 0 ELSE 1 
            END, 
            ABS(EXTRACT(EPOCH FROM (tr.start_date::timestamp - CURRENT_DATE::timestamp))) ASC
        LIMIT 1
    """, (user_id,))


    nearest = cur.fetchone()

    if not nearest:
        flash("表示できる旅行プランがありません。", "warning")
        return redirect(url_for("home.home"))

    plan_id = nearest["plan_id"]

    # --- (2) 以下は travel_budget() と同様 ---
    cur.execute("""
        SELECT tp.*, tr.trip_name, tr.start_date, tr.end_date
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tp.id = %s
    """, (plan_id,))
    plan = cur.fetchone()
    if plan is None:
        flash("旅行プランが見つかりません。", "error")
        return redirect(url_for("home.home"))

    # --- 日別行程 ---
    cur.execute("""
        SELECT dp.*
        FROM day_plans dp
        WHERE dp.travel_plan_id = %s
        ORDER BY dp.day_number ASC
    """, (plan_id,))
    day_rows = cur.fetchall()
    days = []
    for d in day_rows:
        cur.execute("""
            SELECT p.id, p.time, p.name, p.description, p.stay_time, p.cost_estimate, p.type
            FROM places p
            WHERE p.day_plan_id = %s
            ORDER BY p.time NULLS LAST
        """, (d["id"],))
        places = cur.fetchall()
        day_obj = {
            "id": d["id"],
            "day_number": d["day_number"],
            "theme": d.get("theme"),
            "route_summary": d.get("route_summary"),
            "total_time": d.get("total_time"),
            "estimated_cost": d.get("estimated_cost") or 0,
            "places": [dict(p) for p in places]
        }
        days.append(day_obj)

    # --- 予算カテゴリ別 ---
    cur.execute("""
        SELECT category, SUM(amount) AS amount, array_agg(description) AS descriptions
        FROM budget_items
        WHERE travel_plan_id = %s
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (plan_id,))
    budget_rows = cur.fetchall()
    budget_items = []
    total_budget_from_items = 0
    for b in budget_rows:
        amt = int(b["amount"] or 0)
        total_budget_from_items += amt
        budget_items.append({
            "category": b["category"],
            "amount": amt,
            "descriptions": b["descriptions"] or []
        })

    total_budget = plan.get("total_budget") or total_budget_from_items
    chart_labels = [bi["category"] for bi in budget_items]
    chart_amounts = [bi["amount"] for bi in budget_items]
    day_total_sum = sum(d["estimated_cost"] for d in days)

    context = {
        "username": username,
        "user_icon": user_icon,
        "plan": dict(plan),
        "days": days,
        "budget_items": budget_items,
        "total_budget": int(total_budget or 0),
        "budget_from_items_total": int(total_budget_from_items),
        "day_total_sum": int(day_total_sum),
        "chart": {
            "labels": chart_labels,
            "amounts": chart_amounts
        }
    }

    cur.close()
    conn.close()

    # --- (3) 同じデータ構造で budget.html に渡す ---
    return render_template("my_travel/budget.html", **context)


@my_travel_bp.route("/travel_budget/<int:plan_id>")
def travel_budget(plan_id):
    # ログインチェック
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = None
    try:
        user_icon = get_user_icon(user_id)  # プロジェクト内の関数を利用
    except Exception:
        user_icon = url_for("static", filename="img/default_user.png")

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 1) travel_plans（大元）
    cur.execute("""
        SELECT tp.* , tr.trip_name, tr.start_date, tr.end_date
        FROM travel_plans tp
        JOIN travel_requests tr ON tp.request_id = tr.id
        WHERE tp.id = %s
    """, (plan_id,))
    plan = cur.fetchone()
    if plan is None:
        # 404 代わりにトップへリダイレクト（要調整）
        return redirect(url_for("home.home"))

    # 2) day_plans（1日ごとの行程）
    cur.execute("""
        SELECT dp.*
        FROM day_plans dp
        WHERE dp.travel_plan_id = %s
        ORDER BY dp.day_number ASC
    """, (plan_id,))
    day_rows = cur.fetchall()
    days = []
    for d in day_rows:
        # その日の場所一覧を取得（任意）
        cur.execute("""
            SELECT p.id, p.time, p.name, p.description, p.stay_time, p.cost_estimate, p.type
            FROM places p
            WHERE p.day_plan_id = %s
            ORDER BY p.time NULLS LAST
        """, (d["id"],))
        places = cur.fetchall()
        # 辞書化してテンプレートで扱いやすくする
        day_obj = {
            "id": d["id"],
            "day_number": d["day_number"],
            "theme": d.get("theme"),
            "route_summary": d.get("route_summary"),
            "total_time": d.get("total_time"),
            "estimated_cost": d.get("estimated_cost") or 0,
            "places": [dict(p) for p in places]
        }
        days.append(day_obj)

    # 3) budget_items（カテゴリ別）
    cur.execute("""
        SELECT category, SUM(amount) AS amount, array_agg(description) AS descriptions
        FROM budget_items
        WHERE travel_plan_id = %s
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (plan_id,))
    budget_rows = cur.fetchall()
    budget_items = []
    total_budget_from_items = 0
    for b in budget_rows:
        amt = int(b["amount"] or 0)
        total_budget_from_items += amt
        budget_items.append({
            "category": b["category"],
            "amount": amt,
            "descriptions": b["descriptions"] or []
        })

    # 4) 総合予算値（travel_plans.total_budget が優先。なければ合計から計算）
    total_budget = plan.get("total_budget") or total_budget_from_items

    # 5) チャート用データ（ラベルと金額配列）
    chart_labels = [bi["category"] for bi in budget_items]
    chart_amounts = [bi["amount"] for bi in budget_items]

    # 6) 日別合計が無ければ day.estimated_cost の合計
    day_total_sum = sum(d["estimated_cost"] for d in days)

    # 7) prepare context
    context = {
        "username": username,
        "user_icon": user_icon,
        "plan": dict(plan),
        "days": days,
        "budget_items": budget_items,
        "total_budget": int(total_budget or 0),
        "budget_from_items_total": int(total_budget_from_items),
        "day_total_sum": int(day_total_sum),
        "chart": {
            "labels": chart_labels,
            "amounts": chart_amounts
        }
    }

    cur.close()
    return render_template("my_travel/travel_budget.html", **context)
