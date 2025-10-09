# app/routes/plan.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
from datetime import datetime
from ..services.itinerary import generate_itinerary

plan_bp = Blueprint(
    "plan", __name__, url_prefix="/plan", template_folder="../../templates"
)

# --- DB接続（mbti_bpに合わせる） ---
DB_CONFIG = {
    "host": "localhost",
    "dbname": "giikuten",
    "user": "yugo_suzuki",
    "password": "mypassword123",
    "port": "5432",
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_latest_mbti(user_id: int) -> str | None:
    """セッションにMBTIが無い場合のフォールバック取得"""
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


@plan_bp.route("/", methods=["GET", "POST"])
def plan():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    mbti_type = session.get("mbti_type")  # まずはセッションを信頼
    if not mbti_type:
        # セッションに無ければDBから直近を取得
        mbti_type = get_latest_mbti(session["user_id"]) or "バランスタイプ"
        session["mbti_type"] = mbti_type  # ついでにセッションへ反映

    if request.method == "GET":
        # 入力フォーム表示
        return render_template("plan/form.html", username=username, mbti=mbti_type)

    # --- POST: 旅行条件を受け取り LLM 提案を生成 ---
    try:
        trip_name = request.form.get("trip_name", "").strip()
        start_date = request.form.get("start_date", "").strip()  # YYYY-MM-DD
        end_date = request.form.get("end_date", "").strip()
        headcount = int(request.form.get("headcount", "1"))
        area = request.form.get("area", "").strip()
        budget = int(request.form.get("budget", "0"))
        notes = request.form.get("notes", "").strip()

        # 必須チェック（テンプレ流）
        if (
            not trip_name
            or not start_date
            or not end_date
            or not area
            or headcount <= 0
            or budget <= 0
        ):
            flash("未入力の必須項目があります。", "error")
            return redirect(url_for("plan.plan"))

        # 期間の簡易妥当性（終了日が開始日より前はNG）
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
            if ed < sd:
                flash("終了日が開始日より前になっています。", "error")
                return redirect(url_for("plan.plan"))
        except ValueError:
            flash("日付の形式が不正です（YYYY-MM-DD）。", "error")
            return redirect(url_for("plan.plan"))

        user = {"name": username, "mbti": mbti_type}
        req = {
            "trip_name": trip_name,
            "start_date": start_date,
            "end_date": end_date,
            "headcount": headcount,
            "area": area,
            "budget": budget,
            "notes": notes,
        }

        # ★ OpenAI 呼び出し（services/itinerary.py）
        plan = generate_itinerary(user, req)

        # ここでDB保存したければ plans テーブル等にINSERT（任意）
        # 今回は最速検証のため未保存

        return render_template("plan/result.html", plan=plan, username=username)

    except Exception as e:
        flash(f"提案生成に失敗しました: {e}", "error")
        return redirect(url_for("plan.plan"))
