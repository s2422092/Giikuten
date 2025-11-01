from flask import Blueprint, render_template,request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
from app.user_icon import get_user_icon

load_dotenv()  # ← .envファイルの内容を読み込む

setting_bp = Blueprint("setting", __name__)

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


@setting_bp.route("/setting")
def setting():
    # --- ログインチェック ---
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- usersテーブルから基本情報を取得 ---
        cur.execute(
            "SELECT u_id, u_name, gmail FROM users WHERE u_id = %s",
            (user_id,)
        )
        user_data = cur.fetchone()
        print("DEBUG: user_data =", user_data)

        # --- user_mbtiテーブルから最新の診断結果を取得 ---
        cur.execute("""
            SELECT code, name, description
            FROM user_mbti
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
        mbti_data = cur.fetchone()
        print("DEBUG: mbti_data =", mbti_data)

        # --- user_iconsテーブルから最新のアイコンを取得 ---
        cur.execute("""
            SELECT icon_base64
            FROM user_icons
            WHERE user_id = %s
            ORDER BY uploaded_at DESC
            LIMIT 1
        """, (user_id,))
        icon_data = cur.fetchone()
        icon_base64 = icon_data[0] if icon_data else None
        print("DEBUG: icon_base64 =", icon_base64)
        # --- travel_requests と travel_plans を結合してユーザーの全プランを取得 ---
        # --- travel_requests と travel_plans を結合してユーザーの全プランを取得 ---
        cur.execute("""
            SELECT 
                tr.id AS request_id,
                tr.trip_name,
                tr.start_date,
                tr.end_date,
                tr.region,
                tr.prefecture,
                tr.city,
                tr.departure,
                tr.transport_pref,
                tr.budget AS request_budget,
                tr.must_visit,
                tr.notes,
                tp.id AS plan_id,
                tp.title,
                tp.summary,
                tp.budget_transport,
                tp.budget_lodging,
                tp.budget_food,
                tp.budget_activities,
                tp.budget_other,
                tp.total_budget,
                tp.rationale,
                tp.raw_response
            FROM travel_requests tr
            LEFT JOIN travel_plans tp ON tp.request_id = tr.id
            WHERE tr.user_id = %s
            AND tp.saved = TRUE              -- ←★ 追加部分（保存済みのみ表示）
            ORDER BY tr.id DESC, tp.id DESC
        """, (user_id,))
        travel_rows = cur.fetchall()


        # --- travel_plansをリスト形式に整形 ---
        travel_plans = []
        for row in travel_rows:
            if row[12]:  # plan_idが存在する場合のみ追加
                travel_plans.append({
                    "request_id": row[0],
                    "trip_name": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "region": row[4],
                    "prefecture": row[5],
                    "city": row[6],
                    "departure": row[7],
                    "transport_pref": row[8],
                    "request_budget": row[9],
                    "must_visit": row[10],
                    "notes": row[11],
                    "id": row[12],
                    "title": row[13],
                    "summary": row[14],
                    "budget_transport": row[15],
                    "budget_lodging": row[16],
                    "budget_food": row[17],
                    "budget_activities": row[18],
                    "budget_other": row[19],
                    "total_budget": row[20],
                    "rationale": row[21],
                    "raw_response": row[22],
                    # 表示用の簡易項目
                    "destination": f"{row[4]} {row[5]} {row[6]}",  # region + prefecture + city
                    "people_count": "未設定"  # 後で人数を追加可能
                })

        print("DEBUG: travel_plans =", travel_plans)

        cur.close()
        conn.close()

        # --- データまとめ ---
        user_info = {
            "id": user_data[0],
            "name": user_data[1],
            "email": user_data[2],
            "mbti_type": mbti_data[0] if mbti_data else "未診断",
            "mbti_name": mbti_data[1] if mbti_data else None,
            "mbti_description": mbti_data[2] if mbti_data else None,
            "icon_base64": icon_base64,
            "travel_plans": travel_plans  # ←ここをループ用にリストで渡す
        }


    except Exception as e:
        print("DEBUG: Exception =", e)
        flash(f"ユーザー情報の取得中にエラーが発生しました: {e}", "error")
        return redirect(url_for("home.home"))

    return render_template("setting/setting.html", user=user_info)



# =========================
# 🔹 個人設定ページ（/personal_setting）
# =========================
@setting_bp.route("/personal_setting")
def personal_setting():
    # --- ログインチェック ---
    if "user_id" not in session:
        return redirect(url_for("index.login"))

    user_id = session["user_id"]
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # --- usersテーブルから基本情報を取得 ---
        cur.execute(
            "SELECT u_id, u_name, gmail FROM users WHERE u_id = %s",
            (user_id,)
        )
        user_data = cur.fetchone()

        # --- user_mbtiテーブルから最新の診断結果を取得 ---
        cur.execute(
            """
            SELECT code, name, description
            FROM user_mbti
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )
        mbti_data = cur.fetchone()

        # --- user_iconsテーブルから最新のアイコンを取得 ---
        cur.execute(
            """
            SELECT icon_base64
            FROM user_icons
            WHERE user_id = %s
            ORDER BY uploaded_at DESC
            LIMIT 1
            """,
            (user_id,)
        )
        icon_data = cur.fetchone()
        icon_base64 = icon_data[0] if icon_data else None

        cur.close()
        conn.close()

        if not user_data:
            flash("ユーザー情報が見つかりません。", "error")
            return redirect(url_for("home.home"))

        # --- データまとめ ---
        user_info = {
            "id": user_data[0],
            "name": user_data[1],
            "email": user_data[2],
            "mbti_type": mbti_data[0] if mbti_data else "未診断",
            "mbti_name": mbti_data[1] if mbti_data else None,
            "mbti_description": mbti_data[2] if mbti_data else None,
            "icon_base64": icon_base64
        }

    except Exception as e:
        flash(f"ユーザー情報の取得中にエラーが発生しました: {e}", "error")
        return redirect(url_for("home.home"))

    # --- 取得データをテンプレートに渡す ---
    return render_template("setting/personal_setting.html", user=user_info)


@setting_bp.route("/upload_icon", methods=["POST"])
def upload_icon():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "error")
        return redirect(url_for("index.login"))

    user_id = session["user_id"]

    # --- アップロードされたファイルを取得 ---
    file = request.files.get("icon")
    if not file or file.filename == "":
        flash("ファイルが選択されていません。", "error")
        return redirect(url_for("setting.setting"))

    try:
        # --- ファイル内容をBase64に変換 ---
        image_bytes = file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        conn = get_conn()
        cur = conn.cursor()

        # --- 既存アイコンの有無チェック ---
        cur.execute("SELECT icon_id FROM user_icons WHERE user_id = %s", (user_id,))
        existing = cur.fetchone()

        if existing:
            # 更新
            cur.execute("""
                UPDATE user_icons
                SET icon_base64 = %s, uploaded_at = %s
                WHERE user_id = %s
            """, (image_base64, datetime.now(), user_id))
        else:
            # 新規挿入
            cur.execute("""
                INSERT INTO user_icons (user_id, icon_base64)
                VALUES (%s, %s)
            """, (user_id, image_base64))

        conn.commit()
        cur.close()
        conn.close()

        flash("プロフィール画像を更新しました。", "success")

    except Exception as e:
        flash(f"画像の保存中にエラーが発生しました: {e}", "error")

    return redirect(url_for("setting.setting"))



# (ファイルの先頭で request をインポート)
#from flask import (
    render_template, redirect, url_for, session, 
    flash, Blueprint, request 
#)
# (get_conn のインポートも必要です)
# from ..db import get_conn  # <-- あなたの環境に合わせて get_conn をインポートしてください

# ... (setting_bp = Blueprint(...) の定義) ...


# (request, flash, redirect, url_for, session, get_conn などのインポートはそのまま)

@setting_bp.route("/update_profile", methods=["POST"])
def update_profile():
    # --- ログインチェック ---
    if "user_id" not in session:
        return redirect(url_for("index.login"))
    
    user_id = session["user_id"]

    # 1. フォームからデータを取得
    new_name = request.form.get("username")
    new_email = request.form.get("email")

    # 2. バリデーション
    if not new_name or not new_email:
        flash("ユーザー名とメールアドレスは必須です。", "error")
        return redirect(url_for("setting.personal_setting"))

    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # 3. Eメールが他のユーザーに使われていないかチェック
        cur.execute(
            "SELECT u_id FROM users WHERE gmail = %s",
            (new_email,)
        )
        existing_user = cur.fetchone()
        
        if existing_user and existing_user[0] != user_id:
            flash("そのメールアドレスは既に使用されています。", "error")
            # ⬇️ ここで処理を中断し、リダイレクトします (finallyは実行されます)
            return redirect(url_for("setting.personal_setting"))

        # 4. データベースを更新 (UPDATE)
        cur.execute(
            """
            UPDATE users 
            SET u_name = %s, gmail = %s 
            WHERE u_id = %s
            """,
            (new_name, new_email, user_id)
        )
        
        # 5. 変更をコミット (保存)
        conn.commit()
        
        # 6. 成功メッセージ
        # ⬇️ 修正点：コミット成功時 (tryブロックの最後) でflashを呼びます
        flash("プロフィールが正常に更新されました。", "success")

    except Exception as e:
        # 7. エラー発生時はロールバック
        if conn:
            conn.rollback()
        
        # 8. エラーメッセージ
        # ⬇️ exceptブロックではエラーのflashのみを呼びます
        flash(f"更新中にエラーが発生しました: {e}", "error")
        
    finally:
        # 9. 接続を閉じる (これは常に実行されます)
        if cur:
            cur.close()
        if conn:
            conn.close()

    # 10. 処理が成功してもエラーでも、最後に設定ページに戻る
    return redirect(url_for("setting.personal_setting"))