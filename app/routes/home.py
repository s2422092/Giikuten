# app/routes/index.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from app.user_icon import get_user_icon


load_dotenv()  # ← .envファイルの内容を読み込む

home_bp = Blueprint("home", __name__)

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




@home_bp.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    user_icon = get_user_icon(user_id)  # アイコン取得

    # --- DB接続 ---
    conn = get_conn()
    cur = conn.cursor()

    # 1. MBTI取得
    cur.execute("""
        SELECT code, name, description 
        FROM user_mbti 
        WHERE user_id = %s
    """, (user_id,))
    mbti_result = cur.fetchone()

    if not mbti_result:
        cur.close()
        conn.close()
        return redirect(url_for("mbti.mbti"))

    mbti_code = mbti_result[0]

    # 2. 同MBTIユーザーの旅行情報取得
    cur.execute("""
        SELECT tr.id, tr.user_id, tr.trip_name, tr.start_date, tr.end_date,
               tr.region, tr.prefecture, tr.city, tr.departure, tr.transport_pref,
               tr.budget, tr.must_visit, tr.notes
        FROM travel_requests tr
        JOIN user_mbti um ON tr.user_id = um.user_id
        WHERE um.code = %s
        ORDER BY tr.created_at DESC
        LIMIT 15
    """, (mbti_code,))
    similar_travels = cur.fetchall()

    # 3. 人気の旅行先を取得（city × prefecture）追加
    cur.execute("""
        SELECT prefecture, city, COUNT(*) AS count
        FROM travel_requests
        WHERE prefecture IS NOT NULL AND city IS NOT NULL
        GROUP BY prefecture, city
        ORDER BY count DESC
        LIMIT 3
    """)
    popular_destinations = cur.fetchall()


    cur.close()
    conn.close()

    # --- ホーム画面にレンダリング ---
    return render_template(
        "home/home.html",
        username=username,
        mbti=mbti_code,
        user_icon=user_icon,
        similar_travels=similar_travels,
        popular_destinations=popular_destinations
    )


@home_bp.route("/information")
def information():
    conn = None
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    return render_template("home/information.html", username=username)

@home_bp.route("/logout")
def logout():
    session.clear()
    print("ログアウトしました。") 
    return redirect(url_for("index.index"))