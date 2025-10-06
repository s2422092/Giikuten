from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2

mbti_bp = Blueprint("mbti", __name__)

## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "kazino",
    "user": "yugo_suzuki",
    "password": "your_password",  # 環境に合わせて修正
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@mbti_bp.route("/mbti")
def mbti():
    if "user_id" not in session:
        # 未ログインならログインページへ
        return redirect(url_for("index.login"))
    username = session.get("username", "ゲスト")
    return render_template("mbti/mbti.html", username=username)