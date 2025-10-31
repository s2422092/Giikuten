from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from app.travel_mbti_logic import (
    calculate_travel_mbti,
)  # ← 判定関数（別ファイル化推奨）

load_dotenv()  # ← .envファイルの内容を読み込む

mbti_bp = Blueprint("mbti", __name__)

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


@mbti_bp.route("/mbti", methods=["GET", "POST"])
def mbti():
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    user_id = session["user_id"]

    if request.method == "POST":
        # --- フォーム入力値取得 ---
        q_purpose = request.form.get("q_purpose")
        q_priority = request.form.get("q_priority")
        q_theme = request.form.get("q_theme")
        q_want = request.form.get("q_want")
        q_avoid = request.form.get("q_avoid")
        q_rhythm = request.form.get("q_rhythm")
        q_motion = request.form.get("q_motion")
        q_distance = request.form.get("q_distance")

        if not all([q_purpose, q_priority, q_theme, q_want, q_avoid, q_rhythm, q_motion, q_distance]):
            flash("全ての質問に回答してください。", "danger")
            return redirect(url_for("mbti.mbti"))

        # --- 診断結果を取得 ---
        result = calculate_travel_mbti(request.form)
        # result["code"], result["mbti_result"], result["label"], などが入っている想定

        conn = get_conn()
        cur = conn.cursor()

        # --- MBTIテーブルから一致する診断タイプを「名前」で検索 ---
        print("DEBUG: 計算されたMBTIタイプ名 →", result["name"])

        # DBに登録されているMBTI名一覧を確認
        cur.execute("SELECT name FROM mbti")
        all_names = [row[0] for row in cur.fetchall()]
        print("DEBUG: DBに登録されているMBTI名一覧 →", all_names)

        # 実際の検索
        cur.execute("""
            SELECT id, code, description
            FROM mbti
            WHERE name = %s OR name LIKE %s
        """, (result["name"], f"%{result['name']}%"))

        # 検索結果をすべて取得
        rows = cur.fetchall()

        # 結果を確認
        if not rows:
            print("DEBUG: 🔴 一致するMBTIタイプ名が見つかりませんでした。")
        else:
            print(f"DEBUG: 🟢 {len(rows)}件ヒットしました。")
            for r in rows:
                print(f"  → id={r[0]}, code={r[1]}, description={r[2][:30]}...")  # 長文は冒頭だけ表示

        # 最初の1件を使用
        mbti_row = rows[0] if rows else None



        if not mbti_row:
            flash("該当する診断タイプがデータベースに存在しません。", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("mbti.mbti"))

        mbti_id, mbti_name, mbti_description = mbti_row

        # --- user_mbti に保存 ---
        cur.execute("""
            INSERT INTO user_mbti (user_id, mbti_id, code, name, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            mbti_id,
            result["code"],
            mbti_name,
            mbti_description
        ))

        conn.commit()
        cur.close()
        conn.close()

        flash("旅行タイプ診断の回答を保存しました！", "success")

        # --- 結果ページへ ---
        return render_template(
            "mbti/mbti_result.html",
            username=username,
            mbti_id=mbti_id,                   # ← DB上のIDを表示
            mbti_name=mbti_name,               # ← テーブルのname
            mbti_description=mbti_description, # ← テーブルのdescription
            mbti_code=result["code"],          # ← 診断コード
            label=result.get("label", ""),     # ← ラベル（任意）
            travel_name=result.get("travel_name", "")
        )

    # --- 初回アクセス時 ---
    return render_template("mbti/mbti.html", username=username)



@mbti_bp.route("/mbti_result")
def mbti_result():
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")
    user_id = session["user_id"]

    # 最新の診断結果をDBから取得
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            um.id,
            um.user_id,
            um.mbti_id,
            um.created_at,
            um.code,
            um.name AS mbti_result, -- 表示用（タイプ名）
            um.description AS mbti_description
        FROM user_mbti AS um
        WHERE um.user_id = %s
        ORDER BY um.created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        mbti_result, label, description, code, travel_name, mbti_description = row
    else:
        flash("診断結果が見つかりません。", "warning")
        return redirect(url_for("mbti.mbti"))

    return render_template(
        "mbti/mbti_result.html",
        username=username,
        mbti_result=mbti_result,
        label=label,
        description=description,
        code=code,
        travel_name=travel_name,
        mbti_description=mbti_description,
    )