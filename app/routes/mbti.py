from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from app.travel_mbti_logic import (
    calculate_travel_mbti,
)  # ← 判定関数（別ファイル化推奨）

load_dotenv()  # ← .envファイルの内容を読み込む

mbti_bp = Blueprint("mbti", __name__)

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


@mbti_bp.route("/mbti", methods=["GET", "POST"])
def mbti():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    user_id = session["user_id"]

    if request.method == "POST":
        # フォーム回答取得
        q_purpose = request.form.get("q_purpose")
        q_priority = request.form.get("q_priority")
        q_theme = request.form.get("q_theme")
        q_want = request.form.get("q_want")
        q_avoid = request.form.get("q_avoid")
        q_rhythm = request.form.get("q_rhythm")
        q_motion = request.form.get("q_motion")
        q_distance = request.form.get("q_distance")

        if not all([q_purpose, q_priority, q_theme, q_want, q_avoid, q_rhythm, q_motion, q_distance]):
            flash("全ての質問に回答してください。", "danger")
            return redirect(url_for("mbti.mbti"))

        # --- 診断ロジック ---
        result = calculate_travel_mbti(request.form)

        # --- DB保存 ---
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO travel_survey (
                user_id, q_purpose, q_priority, q_theme, q_want, q_avoid,
                q_rhythm, q_motion, q_distance,
                mbti_result, label, description, code, travel_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, q_purpose, q_priority, q_theme, q_want, q_avoid,
            q_rhythm, q_motion, q_distance,
            result["mbti_result"], result["label"], result["description"],
            result["code"], result["travel_name"]
        ))
        conn.commit()
        cur.close()
        conn.close()

        flash("旅行タイプ診断の回答を保存しました！", "success")

        # --- 結果ページへ ---
        return render_template(
            "mbti/mbti_result.html",
            username=username,
            mbti_result=result["mbti_result"],
            label=result["label"],
            description=result["description"],
            code=result["code"],
            travel_name=result["travel_name"]
        )

    # 初回アクセス：フォーム表示
    return render_template("mbti/mbti.html", username=username)

@mbti_bp.route("/mbti_result")
def mbti_result():
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    user_id = session["user_id"]

    # 最新の診断結果をDBから取得
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT mbti_result, label, description, code, travel_name
        FROM travel_survey
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        mbti_result, label, description, code, travel_name = row
    else:
        flash("診断結果が見つかりません。", "warning")
        return redirect(url_for("mbti.mbti"))

    return render_template(
        "mbti/mbti_result.html",
        username=username,
        mbti_result=mbti_result,
        label=label,
        description=description,
        code=code,
        travel_name=travel_name
    )
