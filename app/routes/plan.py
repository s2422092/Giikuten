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
import os
from dotenv import load_dotenv

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
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_latest_mbti(user_id: int) -> str | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT mbti_type FROM user_mbti WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


# ---------- ここから 3階層セレクト用API ----------
@plan_bp.get("/api/regions")
def api_regions():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT region FROM locations WHERE region IS NOT NULL ORDER BY region"
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"ok": True, "items": rows})
    except Exception as e:
        # フロント側でフォールバックするので簡潔に返す
        return jsonify({"ok": False, "error": str(e)}), 500


@plan_bp.get("/api/prefectures")
def api_prefectures():
    region = request.args.get("region", "").strip()
    if not region:
        return jsonify({"ok": False, "error": "region is required"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT prefecture
            FROM locations
            WHERE region = %s AND prefecture IS NOT NULL
            ORDER BY prefecture
        """,
            (region,),
        )
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"ok": True, "items": rows})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@plan_bp.get("/api/cities")
def api_cities():
    pref = request.args.get("prefecture", "").strip()
    if not pref:
        return jsonify({"ok": False, "error": "prefecture is required"}), 400
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT city
            FROM locations
            WHERE prefecture = %s AND city IS NOT NULL
            ORDER BY city
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
    mbti_type = session.get("mbti_type")
    if not mbti_type:
        mbti_type = get_latest_mbti(session["user_id"]) or "バランスタイプ"
        session["mbti_type"] = mbti_type

    if request.method == "GET":
        return render_template("plan/form.html", username=username, mbti=mbti_type)

    # --- POST: 旅行条件 + 場所選択を受け取り LLM 提案 ---
    try:
        # 基本条件
        trip_name = request.form.get("trip_name", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        headcount = int(request.form.get("headcount", "1"))
        budget = int(request.form.get("budget", "0"))
        notes = request.form.get("notes", "").strip()

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

        user = {"name": username, "mbti": mbti_type}
        req = {
            "trip_name": trip_name,
            "start_date": start_date,
            "end_date": end_date,
            "headcount": headcount,
            "budget": budget,
            "notes": notes,
            # 新フィールド（LLMへのヒントとして渡す）
            "region": region,
            "prefecture": prefecture,
            "city": city,
            # 既存の互換用（表示にも使える）
            "area": area_label,
        }

        plan_obj = generate_itinerary(user, req)  # LLM呼び出し

        return render_template("plan/result.html", plan=plan_obj, username=username)

    except Exception as e:
        flash(f"提案生成に失敗しました: {e}", "error")
        return redirect(url_for("plan.plan"))
