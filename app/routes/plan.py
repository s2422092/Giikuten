# app/routes/plan.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
import psycopg2
from datetime import datetime
from ..services.itinerary import generate_itinerary
from psycopg2.extras import Json
import os
from dotenv import load_dotenv
from app.user_icon import get_user_icon
import json
from typing import Dict, Any, Optional, List

load_dotenv()

plan_bp = Blueprint(
    "plan", __name__, url_prefix="/plan", template_folder="../../templates"
)

# DB接続設定を環境変数から取得
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


def fetch_user_mbti(conn, user_id: int) -> Optional[Dict[str, Any]]:
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


def insert_travel_request(conn, user_id: int, req: Dict[str, Any]) -> int:
    """travel_requests に保存してIDを返す"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO travel_requests
              (user_id, trip_name, start_date, end_date, region, prefecture, city,
               departure, transport_pref, budget, must_visit, notes, suggest_final_lodging)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                user_id,
                req["trip_name"],
                req["start_date"],
                req["end_date"],
                req["region"],
                req.get("prefecture"),
                req.get("city"),
                req.get("departure"),
                req.get("transport_pref"),
                req.get("budget"),
                req.get("must_visit"),
                req.get("notes"),
                bool(req.get("suggest_final_lodging", False)),
            ),
        )
        rid = cur.fetchone()[0]
    conn.commit()
    return rid


def insert_travel_plan_hierarchy(conn, request_id: int, plan: Dict[str, Any]) -> int:
    """受け取った plan(JSON相当) を travel_plans / day_plans / places / budget_items に正規化保存"""
    bd = plan.get("budget_breakdown") or {}
    total_budget = sum(
        int(bd.get(k, 0) or 0)
        for k in ["transport", "lodging", "food", "activities", "other"]
    )
    rationale_json = json.dumps(plan.get("rationale", []), ensure_ascii=False)
    raw_json = json.dumps(plan.get("raw_response", {}), ensure_ascii=False)

    with conn.cursor() as cur:
        # travel_plans
        cur.execute(
            """
            INSERT INTO travel_plans
              (request_id, title, summary,
               budget_transport, budget_lodging, budget_food, budget_activities, budget_other,
               total_budget, overview, lodging_suggestions, return_trip, rationale, raw_response)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb)
            RETURNING id
            """,
            (
                request_id,
                plan.get("title"),
                plan.get("summary"),
                int(bd.get("transport", 0) or 0),
                int(bd.get("lodging", 0) or 0),
                int(bd.get("food", 0) or 0),
                int(bd.get("activities", 0) or 0),
                int(bd.get("other", 0) or 0),
                int(total_budget),
                plan.get("overview"),
                json.dumps(plan.get("lodging_suggestions", []), ensure_ascii=False),
                json.dumps(plan.get("return_trip", {}), ensure_ascii=False),
                rationale_json,
                raw_json,
            ),
        )
        travel_plan_id = cur.fetchone()[0]

        # budget_items（将来の明細拡張用）
        for key, label in [
            ("transport", "交通費"),
            ("lodging", "宿泊費"),
            ("food", "食費"),
            ("activities", "アクティビティ"),
            ("other", "その他"),
        ]:
            amt = int(bd.get(key, 0) or 0)
            if amt > 0:
                cur.execute(
                    "INSERT INTO budget_items (travel_plan_id, category, amount, description) VALUES (%s,%s,%s,%s)",
                    (travel_plan_id, label, amt, None),
                )

        # day_plans / places
        for day in plan.get("daily_plan") or []:
            cur.execute(
                """
                INSERT INTO day_plans (travel_plan_id, day_number, theme, route_summary, total_time, estimated_cost)
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    travel_plan_id,
                    int(day.get("day", 0) or 0),
                    day.get("theme"),
                    day.get("route_summary"),
                    None,  # total_time: 後で集計更新
                    None,  # estimated_cost: 後で集計更新
                ),
            )
            day_id = cur.fetchone()[0]

            for p in day.get("places") or []:
                cur.execute(
                    """
                    INSERT INTO places
                      (day_plan_id, time, name, description, stay_time, access, map_url,
                       cost_estimate, type, fun_fact, leave_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        day_id,
                        p.get("time"),
                        p.get("name"),
                        p.get("description"),
                        p.get("stay_time"),
                        p.get("access"),
                        p.get("map_url"),
                        p.get("cost_estimate"),
                        p.get("type"),
                        p.get("fun_fact"),
                        p.get("leave_time"),
                    ),
                )
    conn.commit()
    return travel_plan_id


def get_latest_mbti_code(user_id: int) -> Optional[str]:
    """互換用：最新のMBTIコードだけ欲しい場合に使用"""
    conn = get_conn()
    try:
        info = fetch_user_mbti(conn, user_id)
        return info["code"] if info else None
    finally:
        conn.close()


# ---------- ここから 3階層セレクト用API ----------
@plan_bp.get("/api/region")
def api_region():
    try:
        conn = get_conn()
        cur = conn.cursor()
        # region テーブルから地域名を取得
        cur.execute("SELECT r_name FROM region ORDER BY r_id")
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"ok": True, "items": rows})
    except Exception as e:
        # フロント側でフォールバックするので簡潔に返す
        return jsonify({"ok": False, "error": str(e)}), 500


@plan_bp.get("/api/prefecture")
def api_prefecture():
    region = request.args.get("region", "").strip()
    if not region:
        return jsonify({"ok": False, "error": "region is required"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        # region → prefecture の結合で都道府県名を取得
        cur.execute(
            """
            SELECT p.p_name
            FROM prefecture AS p
            JOIN region AS r ON p.r_id = r.r_id
            WHERE r.r_name = %s
            ORDER BY p.p_id
            """,
            (region,),
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"ok": True, "items": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@plan_bp.get("/api/area")
def api_area():
    pref = request.args.get("prefecture", "").strip()
    if not pref:
        return jsonify({"ok": False, "error": "prefecture is required"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        # prefecture → area の結合で市区町村/エリア名を取得
        cur.execute(
            """
            SELECT a.a_name
            FROM area AS a
            JOIN prefecture AS p ON a.p_id = p.p_id
            WHERE p.p_name = %s
            ORDER BY a.a_id
            """,
            (pref,),
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"ok": True, "items": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- 3階層セレクト用API ここまで ----------


@plan_bp.route("/", methods=["GET", "POST"])
def plan():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(session["user_id"])  # ←ここでアイコン取得
    # 最新のMBTI情報を取得（なければデフォルト）
    conn_for_mbti = get_conn()
    try:
        mbti_info = fetch_user_mbti(conn_for_mbti, session["user_id"])
    finally:
        conn_for_mbti.close()
    # 表示・後続のためにコード文字列をセッションへ
    mbti_code = (mbti_info or {}).get("code") or "バランスタイプ"
    session["mbti_type"] = mbti_code

    if request.method == "GET":
        return render_template(
            "plan/form.html", username=username, mbti=mbti_code, user_icon=user_icon
        )

    # --- POST: 旅行条件  場所選択を受け取り LLM 提案 ---
    try:
        # 基本条件
        trip_name = request.form.get("trip_name", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        headcount = int(request.form.get("headcount", "1"))
        budget = int(request.form.get("budget", "0"))
        notes = request.form.get("notes", "").strip()
        must_visit = request.form.get("must_visit", "").strip()
        departure = request.form.get("departure", "").strip() or None
        transport_pref = request.form.get("transport_pref", "auto").strip() or "auto"
        suggest_final_lodging = bool(request.form.get("suggest_final_lodging"))
        suggest_nearby = bool(request.form.get("suggest_nearby"))

        # 場所（3階層）
        region = request.form.get("region", "").strip()
        prefecture = request.form.get("prefecture", "").strip() or None  # 任意
        city = request.form.get("city", "").strip() or None  # 任意

        # 必須チェック
        if (
            not trip_name
            or not start_date
            or not end_date
            or headcount <= 0
            or budget <= 0
        ):
            flash("未入力の必須項目があります。", "error")
            return redirect(url_for("plan.plan"))

        if not region:
            flash("地域は必須です。", "error")
            return redirect(url_for("plan.plan"))

        # 期間の妥当性
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
            if ed < sd:
                flash("終了日が開始日より前になっています。", "error")
                return redirect(url_for("plan.plan"))
        except ValueError:
            flash("日付の形式が不正です（YYYY-MM-DD）。", "error")
            return redirect(url_for("plan.plan"))

        # 既存LLMサービスが "area" を見る想定があるため、見栄えのラベルも作る
        area_label = " / ".join([p for p in [region, prefecture, city] if p])

        user = {"name": username, "mbti": mbti_code}
        req = {
            "trip_name": trip_name,
            "start_date": start_date,
            "end_date": end_date,
            "headcount": headcount,
            "budget": budget,
            "notes": notes,
            "must_visit": must_visit,
            "region": region,
            "prefecture": prefecture,
            "city": city,
            "departure": departure,
            "transport_pref": transport_pref,
            "area": area_label,
            "suggest_final_lodging": suggest_final_lodging,
            "suggest_nearby": suggest_nearby,
        }

        # DB接続開始
        conn = get_conn()
        # 1) リクエスト保存
        request_id = insert_travel_request(conn, session["user_id"], req)
        # 2) LLM実行
        plan_obj = generate_itinerary(user, req, mbti_info=mbti_info)
        # 3) 正規化保存
        _ = insert_travel_plan_hierarchy(conn, request_id, plan_obj)
        # テンプレで生JSONを見せたい場合に使う
        plan_json = json.dumps(plan_obj, ensure_ascii=False, indent=2)
        conn.close()

        # ←← ここで必ずレスポンスを返す
        return render_template(
            "plan/result.html",
            plan=plan_obj,
            plan_json=plan_json,  # テンプレで生JSONを見せたい場合に使用
            username=username,
        )

    except Exception as e:
        import traceback

        # サーバのコンソールに完全なスタックを出す（どのテンプレ/関数で url_for が呼ばれたか一発で分かる）
        print("=== DEBUG plan(): exception ===")
        print("type:", type(e).__name__)
        traceback.print_exc()
        print("=== /DEBUG ===")
        flash(f"提案生成に失敗しました: {type(e).__name__}: {e}", "error")
        return redirect(url_for("plan.plan"))
