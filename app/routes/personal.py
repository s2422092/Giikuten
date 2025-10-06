from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2

personal_bp = Blueprint("personal", __name__)
## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "kazino",
    "user": "yugo_suzuki",
    "password": "your_password",  # 環境に合わせて修正
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@personal_bp.route("/personal")
def personal():
    if "user_id" not in session:
        # 未ログインならログインページへ
        return redirect(url_for("index.login"))
    username = session.get("username", "ゲスト")
    return render_template("personal/personal.html", username=username)