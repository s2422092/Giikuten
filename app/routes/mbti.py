from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
from app.travel_mbti_logic import (
    calculate_travel_mbti,
)  # ← 判定関数（別ファイル化推奨）

mbti_bp = Blueprint("mbti", __name__)

## DB接続
DB_CONFIG = {
    "host": "localhost",
    "dbname": "giikuten",
    "user": "yugo_suzuki",
    "password": "mypassword123",  # 先ほど設定したパスワード
    "port": "5432",
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# travel_mbti_questions.py

QUESTIONS = [
    {"id": 1, "text": "旅行先では予定をきっちり立てたい"},
    {"id": 2, "text": "知らない土地で新しい人と出会うのが好き"},
    {"id": 3, "text": "一人旅の方が落ち着く"},
    {"id": 4, "text": "旅行前の準備は早めに済ませたい"},
    {"id": 5, "text": "旅行中もSNSで発信したい"},
    {"id": 6, "text": "旅の途中で予定変更があっても気にしない"},
    {"id": 7, "text": "旅先で地元の人と話すのが楽しい"},
    {"id": 8, "text": "ホテルは快適さより価格重視"},
    {"id": 9, "text": "グループ旅行より少人数の方が好き"},
    {"id": 10, "text": "写真を撮ることが好き"},
    {"id": 11, "text": "旅先では観光地を全部回りたい"},
    {"id": 12, "text": "旅行中に人と深く話すのが楽しい"},
    {"id": 13, "text": "休暇の予定を細かく立てるタイプ"},
    {"id": 14, "text": "感覚的に行動する方が性に合う"},
    {"id": 15, "text": "宿泊施設は雰囲気より実用性を重視"},
    {"id": 16, "text": "旅先では静かに過ごしたい"},
    {"id": 17, "text": "現地で友達を作ることに抵抗はない"},
    {"id": 18, "text": "予定が崩れると不安になる"},
    {"id": 19, "text": "旅行先の文化に深く触れたい"},
    {"id": 20, "text": "グループをまとめるのは得意"},
    {"id": 21, "text": "旅先でトラブルがあっても楽しめる"},
    {"id": 22, "text": "感情で行動することが多い"},
    {"id": 23, "text": "直感的に目的地を決めることがある"},
    {"id": 24, "text": "旅行ではリラックス重視"},
    {"id": 25, "text": "旅先での買い物が好き"},
    {"id": 26, "text": "旅行計画は人に任せたい"},
    {"id": 27, "text": "スケジュール管理は得意"},
    {"id": 28, "text": "新しいアクティビティに挑戦したい"},
    {"id": 29, "text": "食事はその場の気分で決める"},
    {"id": 30, "text": "旅行の写真や記録を残すのが好き"},
    {"id": 31, "text": "予定外のハプニングを楽しめる"},
    {"id": 32, "text": "旅行の後で反省点を振り返る"},
    {"id": 33, "text": "一人でも知らない国に行ける"},
    {"id": 34, "text": "旅行の予算は厳密に決める"},
    {"id": 35, "text": "旅先でアートや建築に興味を持つ"},
    {"id": 36, "text": "旅の目的はリフレッシュより刺激"},
    {"id": 37, "text": "団体旅行の方が安心できる"},
    {"id": 38, "text": "現地の食文化を体験するのが好き"},
    {"id": 39, "text": "旅先で予定をコロコロ変えがち"},
    {"id": 40, "text": "旅行から帰った後、次の旅をすぐ計画したくなる"},
]


# MBTIタイプ分類（例: 12種類）
TRAVEL_TYPES = {
    "ESTJ": "計画的アドベンチャラー",
    "INFP": "感性派トラベラー",
    "ENFP": "ひらめき旅人",
    "ISTP": "孤高の探検家",
    "ESFP": "盛り上げ上手な旅仲間",
    "ISFJ": "安心重視の保守派",
    "ENTJ": "リーダーシップ旅行者",
    "INTJ": "戦略家タイプの旅人",
    "ESFJ": "社交的ホストタイプ",
    "ISTJ": "完璧主義な旅プランナー",
    "ENTP": "自由奔放なトリッキー旅行者",
    "INFJ": "哲学的ロマンチスト",
}


@mbti_bp.route("/mbti", methods=["GET", "POST"])
def mbti():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")

    if request.method == "POST":
        # --- 回答を取得 ---
        answers = [
            int(request.form.get(f"q{i}", 3)) for i in range(1, len(QUESTIONS) + 1)
        ]

        # --- 診断ロジックを呼び出し ---
        mbti_result = calculate_travel_mbti(answers)

        # ★ セッションに保存
        session["mbti_type"] = mbti_result

        # --- DBに保存 ---
        user_id = session["user_id"]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_mbti (user_id, mbti_type) VALUES (%s, %s)",
            (user_id, mbti_result),
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("診断結果を保存しました！", "success")
        return render_template(
            "mbti/mbti_result.html", mbti_result=mbti_result, username=username
        )

    # --- 初回アクセス時：質問を表示 ---
    return render_template("mbti/mbti.html", questions=QUESTIONS, username=username)


@mbti_bp.route("/mbti_result")
def mbti_result():
    # --- ログインチェック ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    user_id = session["user_id"]

    # --- DBからMBTI結果を取得 ---
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT mbti_type FROM user_mbti WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        mbti_result = result[0]
        description = TRAVEL_TYPES.get(
            mbti_result, "あなたにぴったりの旅行タイプです！"
        )
        # ★ 結果ページ表示時にもセッションへ同期（直アクセス対策）
        session["mbti_type"] = mbti_result

    else:
        mbti_result = "未診断"
        description = "まだ診断を受けていません。"

    # --- 結果ページを表示 ---
    return render_template(
        "mbti/mbti_result.html", mbti_result=mbti_result, description=description
    )
