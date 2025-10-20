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
        # --- フォームから回答を取得 ---
        q_purpose = request.form.get("q_purpose")
        q_priority = request.form.get("q_priority")
        q_theme = request.form.get("q_theme")
        q_want = request.form.get("q_want")
        q_avoid = request.form.get("q_avoid")
        q_rhythm = request.form.get("q_rhythm")
        q_motion = request.form.get("q_motion")
        q_distance = request.form.get("q_distance")

        # --- 未入力チェック（念のため） ---
        if not all([q_purpose, q_priority, q_theme, q_want, q_avoid, q_rhythm, q_motion, q_distance]):
            flash("全ての質問に回答してください。", "danger")
            return redirect(url_for("mbti.mbti"))

        try:
            # --- DBに接続 ---
            conn = get_conn()
            cur = conn.cursor()

            # --- travel_surveyテーブルにINSERT ---
            cur.execute("""
                INSERT INTO travel_survey (
                    user_id, q_purpose, q_priority, q_theme, q_want, q_avoid, q_rhythm, q_motion, q_distance
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, q_purpose, q_priority, q_theme, q_want, q_avoid, q_rhythm, q_motion, q_distance
            ))

            conn.commit()
            cur.close()
            conn.close()

            flash("旅行タイプ診断の回答を保存しました！", "success")

            # --- 結果ページへ遷移 ---
            return render_template(
                "mbti/mbti_result.html",
                username=username,
                answers={
                    "目的": q_purpose,
                    "重視ポイント": q_priority,
                    "テーマ": q_theme,
                    "したいこと": q_want,
                    "避けたいこと": q_avoid,
                    "活動リズム": q_rhythm,
                    "乗り物酔い": q_motion,
                    "移動時間": q_distance
                }
            )

        # exceptブロックを削除 → エラーが発生した場合は Flask のデフォルトエラー画面になる


        except Exception as e:
            pass

    # --- 初回アクセス時（質問フォームを表示） ---
    return render_template("mbti/mbti.html", username=username)



@mbti_bp.route("/mbti_result", methods=["POST"])
def mbti_result():
    """
    フォーム回答をDBに保存し、travel_mbti_logic.pyで診断を実行 → 結果表示
    """
    form_data = request.form
    user_id = session.get("user_id")  # ログインユーザーID（なければNone）

    # --- 1️⃣ 診断ロジック実行 ---
    result = calculate_travel_mbti(form_data)

    # --- 2️⃣ DBに保存 ---
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
        user_id,
        form_data.get("q_purpose"),
        form_data.get("q_priority"),
        form_data.get("q_theme"),
        form_data.get("q_want"),
        form_data.get("q_avoid"),
        form_data.get("q_rhythm"),
        form_data.get("q_motion"),
        form_data.get("q_distance"),
        result["mbti_result"],
        result["label"],
        result["description"],
        result["code"],
        result["travel_name"]
    ))

    conn.commit()
    cur.close()
    conn.close()

    # --- 3️⃣ 結果ページを描画 ---
    username = session.get("username", "ゲスト")

    return render_template(
        "mbti_result.html",
        username=username,
        mbti_result=result["mbti_result"],
        label=result["label"],
        description=result["description"],
        code=result["code"],
        travel_name=result["travel_name"],
        mbti_description=result["mbti_description"]
    )