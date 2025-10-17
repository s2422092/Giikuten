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
    ブラウザで表示可能な形式のdata URIに変換して返す
    """
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
            # ブラウザで使える形式に変換
            return f"data:image/png;base64,{result[0]}"
        return None  # アイコン未設定の場合

    except Exception as e:
        print(f"アイコン取得エラー: {e}")
        return None
    finally:
        if conn:
            conn.close()


@my_travel_bp.route("/my_travel")
def my_travel():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")

    # アイコン取得
    user_icon_base64 = get_user_icon(user_id)

    return render_template(
        "my_travel/my_travel.html",
        username=username,
        user_icon_base64=user_icon_base64
    )
