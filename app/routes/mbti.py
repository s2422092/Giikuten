from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2

mbti_bp = Blueprint("mbti", __name__)

## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "giikuten",
    "user": "yugo_suzuki",
    "password": "mypassword123",  # 先ほど設定したパスワード
    "port": "5432"
}
def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@mbti_bp.route("/mbti", methods=["GET", "POST"])
def mbti():
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    if request.method == "POST":
        mbti_result = request.form.get("mbti_result")  # 例: "ENFP"
        user_id = session["user_id"]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_mbti (user_id, mbti_type) VALUES (%s, %s)",
            (user_id, mbti_result)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("診断結果を保存しました！", "success")
        return redirect(url_for("home.home"))

    return render_template("mbti/mbti.html")
