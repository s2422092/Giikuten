# app/routes/index.py
from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2

index_bp = Blueprint("index", __name__)

# DB接続設定
DB_CONFIG = {
    "host": "localhost",
    "dbname": "giikuten",
    "user": "yugo_suzuki",
    "password": "mypassword123",  # 先ほど設定したパスワード
    "port": "5432"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@index_bp.route("/")
def index():
    return render_template("index/index.html")


# --- ログインページ ---
@index_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # ✅ 入力チェック
        if not username or not password:
            flash("ユーザー名とパスワードを入力してください。", "error")
            return render_template("index/login.html")

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT u_id, u_name, password FROM users WHERE u_name = %s",
                (username,)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and user[2] == password:
                session["user_id"] = user[0]
                session["username"] = user[1]
                flash("ログインに成功しました！", "success")
                return redirect(url_for("home.home"))
            else:
                flash("ユーザー名またはパスワードが間違っています。", "error")
                return render_template("index/login.html")

        except Exception as e:
            flash(f"ログイン中にエラーが発生しました: {e}", "error")
            return render_template("index/login.html")

    return render_template("index/login.html")

# --- 新規登録ページ ---
@index_bp.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # 入力チェック
        if not all([username, email, password, confirm_password]):
            flash("全ての項目を入力してください。", "error")
            return render_template("index/registration.html")

        if password != confirm_password:
            flash("パスワードが一致しません。", "error")
            return render_template("index/registration.html")

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users (u_name, gmail, password)
                VALUES (%s, %s, %s)
                """,
                (username, email, password)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("登録が完了しました！", "success")
            return redirect(url_for("index.login"))
        except psycopg2.errors.UniqueViolation:
            flash("このメールアドレスは既に登録されています。", "error")
            conn.rollback()
            cur.close()
            conn.close()
            return render_template("index/registration.html")
        except Exception as e:
            flash(f"登録中にエラーが発生しました: {e}", "error")
            return render_template("index/registration.html")

    return render_template("index/registration.html")