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
    conn = None
    if "user_id" not in session:
        return redirect(url_for("index.login"))
    user_id = session["user_id"]
    username = session.get("username", "ゲスト")
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT mbti_type FROM user_mbti WHERE user_id = %s", (session["user_id"],))
    mbti_result = cur.fetchone()
    cur.close()
    conn.close()
    user_icon = get_user_icon(user_id) # ←ここでアイコン取得
    
    if not mbti_result:
        # 未診断なら診断ページへリダイレクト
        return redirect(url_for("mbti.mbti"))

    username = session.get("username", "ゲスト")
    return render_template("home/home.html", username=username, mbti=mbti_result[0], user_icon=user_icon)

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