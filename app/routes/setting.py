from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # ← .envファイルの内容を読み込む

setting_bp = Blueprint("setting", __name__)

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

@setting_bp.route("/setting")
def setting():
    conn = None
    # --- ログインチェック ---
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]

    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- usersテーブルから基本情報を取得 ---
        cur.execute(
            "SELECT u_id, u_name, gmail FROM users WHERE u_id = %s",
            (user_id,)
        )
        user_data = cur.fetchone()

        # --- user_mbtiテーブルから最新の診断結果を取得 ---
        cur.execute(
            """
            SELECT mbti_type, created_at 
            FROM user_mbti 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (user_id,)
        )
        mbti_data = cur.fetchone()

        cur.close()
        conn.close()

        if not user_data:
            flash("ユーザー情報が見つかりません。", "error")
            return redirect(url_for("home.home"))

        # --- データまとめ ---
        user_info = {
            "id": user_data[0],
            "name": user_data[1],
            "email": user_data[2],
            "mbti_type": mbti_data[0] if mbti_data else "未診断",
            "mbti_date": mbti_data[1].strftime("%Y-%m-%d %H:%M:%S") if mbti_data else None
        }

    except Exception as e:
        flash(f"ユーザー情報の取得中にエラーが発生しました: {e}", "error")
        return redirect(url_for("home.home"))

    return render_template("setting/setting.html", user=user_info)
