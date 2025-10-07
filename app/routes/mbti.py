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

# 旅行MBTI診断用の質問データ
QUESTIONS = [
    {"text": "旅行先では予定を立てて行動したい？", "option_a": "はい、計画を立てるのが好き", "option_b": "いいえ、気分で動きたい"},
    {"text": "旅行中に知らない人と話すのは？", "option_a": "楽しいと思う", "option_b": "できれば避けたい"},
    {"text": "観光よりもグルメを重視する？", "option_a": "観光重視！", "option_b": "グルメ重視！"},
    # ...このように40問まで拡張可能
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
    # --- ログインしていなければログインページへ ---
    if "user_id" not in session:
        flash("ログインしてください。", "warning")
        return redirect(url_for("index.login"))

    username = session.get("username", "ゲスト")  # ← ここに移動！

    if request.method == "POST":
        # すべての回答を取得
        answers = [request.form.get(f"q{i+1}") for i in range(len(QUESTIONS))]

        # --- 簡易ロジック例 ---
        # Aが多ければ外向的、Bが多ければ内向的 などの仮判定
        count_a = answers.count("A")
        count_b = answers.count("B")

        if count_a > count_b:
            mbti_result = "ENFP"
        else:
            mbti_result = "ISTJ"

        # --- DBに保存 ---
        user_id = session["user_id"]
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_mbti (user_id, mbti_type) VALUES (%s, %s)",
            (user_id, mbti_result)
        )
        
        cur.execute(
            "SELECT u_id, u_name, password FROM users WHERE u_name = %s",
            (username,)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("診断結果を保存しました！", "success")
        return render_template("mbti/mbti_result.html",
                               mbti_result=mbti_result,
                               description=TRAVEL_TYPES.get(mbti_result, "不明"))

    # 初回アクセス時：質問リストを渡す
    return render_template("mbti/mbti.html", questions=QUESTIONS, username=username)