from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import session   


home_bp = Blueprint("home", __name__)

## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "kazino",
    "user": "yugo_suzuki",
    "password": "your_password",  # 環境に合わせて修正
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)


@home_bp.route("/home")
def home():
    if "user_id" not in session:
        # 未ログインならログインページへ
        return redirect(url_for("index.login"))
    username = session.get("username", "ゲスト")
    return render_template("home/home.html", username=username)

@home_bp.route("/logout")
def logout():
    session.clear()
    print("ログアウトしました。") 
    return redirect(url_for("index.index"))