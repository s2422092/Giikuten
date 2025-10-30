# app/routes/index.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()  # ← .envファイルの内容を読み込む

index_bp = Blueprint("index", __name__)

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

@index_bp.route("/")
def index():
    
    return render_template("index/index.html")


# --- ログインページ ---
from flask import render_template, request, session, flash, redirect, url_for
from werkzeug.security import check_password_hash

@index_bp.route("/login", methods=["GET", "POST"])
def login():
    conn = None

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
            cur.execute("SELECT u_id, u_name, password FROM users WHERE u_name = %s", (username,))
            user = cur.fetchone()

            if not user:
                flash("そのユーザーは存在しません。", "error")
                cur.close()
                conn.close()
                return render_template("index/login.html")

            db_password = user[2]

            # 🔹 PostgreSQLなどではbytes型の場合がある
            if isinstance(db_password, bytes):
                db_password = db_password.decode("utf-8")

            print(f"DEBUG: DB Password = {repr(db_password)}")

            # ✅ ハッシュ・平文対応チェック
            login_success = False

            try:
                # 1️⃣ ハッシュ化パスワード（scrypt または pbkdf2）対応
                if ":" in db_password:  # ← どちらの形式にも対応
                    if check_password_hash(db_password, password):
                        login_success = True
                # 2️⃣ 平文対応
                elif db_password == password:
                    login_success = True
            except Exception as e:
                print(f"DEBUG: check_password_hash error: {e}")

            # ❌ ログイン失敗時
            if not login_success:
                flash("パスワードが間違っています。", "error")
                cur.close()
                conn.close()
                return render_template("index/login.html")

            # ✅ ログイン成功
            session["user_id"] = user[0]
            session["username"] = user[1]

            # 🔹 MBTI診断済みか確認
            cur.execute("SELECT 1 FROM user_mbti WHERE user_id = %s", (user[0],))
            mbti_result = cur.fetchone()

            cur.close()
            conn.close()

            if mbti_result:
                flash("ログインに成功しました！", "success")
                return redirect(url_for("home.home"))
            else:
                flash("まずMBTI診断を行ってください。", "info")
                return redirect(url_for("mbti.mbti"))

        except Exception as e:
            if conn:
                conn.close()
            flash(f"ログイン中にエラーが発生しました: {e}", "error")
            return render_template("index/login.html")

    # GET時（フォーム表示）
    return render_template("index/login.html")




# --- 新規登録ページ ---
@index_bp.route("/registration", methods=["GET", "POST"])
def registration():
    conn = None

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # --- 入力チェック ---
        if not all([username, email, password, confirm_password]):
            flash("全ての項目を入力してください。", "error")
            return render_template("index/registration.html")

        # --- 文字数制限チェック ---
        if len(username) > 32:
            flash("ユーザー名は32文字以内で入力してください。", "error")
            return render_template("index/registration.html")

        if len(email) > 64:
            flash("メールアドレスは64文字以内で入力してください。", "error")
            return render_template("index/registration.html")

        if len(password) > 32 or len(confirm_password) > 32:
            flash("パスワードは32文字以内で入力してください。", "error")
            return render_template("index/registration.html")

        # --- パスワード一致チェック ---
        if password != confirm_password:
            flash("パスワードが一致しません。", "error")
            return render_template("index/registration.html")

        try:
            conn = get_conn()
            cur = conn.cursor()

            # --- 🔽 既存ユーザー確認（メール・ユーザー名両方） ---
            cur.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE u_name = %s OR gmail = %s
                """,
                (username, email)
            )
            count = cur.fetchone()[0]
            if count > 0:
                flash("このユーザー名またはメールアドレスは既に登録されています。", "error")
                cur.close()
                conn.close()
                return render_template("index/registration.html")
            # ハッシュ化
            hashed_password = generate_password_hash(password)
            # --- 🔽 新規登録処理 ---
            cur.execute(
                """
                INSERT INTO users (u_name, gmail, password)
                VALUES (%s, %s, %s)
                """,
                (username, email, hashed_password)
            )
            conn.commit()

            cur.close()
            conn.close()

            flash("登録が完了しました！", "success")
            return redirect(url_for("index.login"))

        except Exception as e:
            flash(f"登録中にエラーが発生しました: {e}", "error")
            if conn:
                conn.rollback()
                cur.close()
                conn.close()
            return render_template("index/registration.html")

    # --- GETメソッド時（フォーム表示） ---
    return render_template("index/registration.html")

@index_bp.route("/hash_passwords")
def hash_passwords():
    try:
        conn = get_conn()
        cur = conn.cursor()

        # まだハッシュ化されていないユーザーを取得（仮にpasswordが平文と仮定）
        cur.execute("SELECT u_id, password FROM users")
        users = cur.fetchall()

        updated = 0
        for u_id, plain_pw in users:
            # すでにハッシュ済みかどうか簡易判定（$pbkdf2が含まれているか）
            if not plain_pw.startswith("pbkdf2:sha256"):
                hashed_pw = generate_password_hash(plain_pw)
                cur.execute("UPDATE users SET password = %s WHERE u_id = %s", (hashed_pw, u_id))
                updated += 1

        conn.commit()
        cur.close()
        conn.close()

        return f"{updated}件のパスワードをハッシュ化しました。"

    except Exception as e:
        return f"エラー: {e}"
