from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from app.travel_mbti_logic import (
    calculate_travel_mbti_safe,
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

        # --- 診断結果を取得（完全安全版） ---
        result = calculate_travel_mbti_safe(request.form)
        code = result["code"]

        conn = get_conn()
        cur = conn.cursor()

        # --- DBに存在する MBTI コード一覧取得 ---
        cur.execute("SELECT id, code FROM mbti")
        mbti_rows = cur.fetchall()
        db_codes = [r[1] for r in mbti_rows]

        # --- 近似マッチ ---
        if code in db_codes:
            mbti_row = next(r for r in mbti_rows if r[1] == code)
        else:
            # DBに存在しない場合は最も近いコードを選択（簡易マッチ）
            def similarity_score(c1, c2):
                return sum(a == b for a, b in zip(c1, c2))
            mbti_row = max(mbti_rows, key=lambda r: similarity_score(code, r[1]))
            print(f"DEBUG: 🔴 DBに存在しないため近似選択 → {mbti_row[1]}")

        mbti_id, mbti_code_db = mbti_row

        # --- TYPE_DEFS から正式 name/description を取得 ---
        TYPE_DEFS = {
            'S-EX-CU|M-NM': ('スポット制覇派', 'このタイプは文化的な名所を効率よく巡るのが得意です。博物館や歴史的建築への関心が高く、午前から活動して時間を有効に使います。片道4~6時間程度の中距離移動も許容できるため、都市をまたぐプランでも無理なく組み立てられます。混雑が予想されるスポットは事前予約や早い時間帯の訪問を取り入れると、より快適に見学できます。'),
            'S-CO-CI|F-SN': ('快適都市散策派', '街歩きと写真映えをバランスよく楽しむタイプです。行程は柔軟に調整し、混雑や移動負担を抑えることで快適さを重視します。近場の都市を中心に、カフェやフォトスポットを織り交ぜた散策が向いています。'),
            'G-FO-CI|N-ML': ('グルメ都市派', '話題のレストラン巡りやナイトライフを積極的に楽しむタイプです。行動は夜型で、片道4~6時間以上の移動もこなせるため、広域にわたって名店を目指す遠征プランにも適性があります。人気店は予約やオフピークの来店で快適度が上がります。'),
            'G-BU-CI|L-SY': ('節約グルメ派', 'コスパにこだわり、ローカル食堂や市場での食体験を楽しむタイプです。昼型で計画を立て、乗り物酔いには配慮して近場中心の移動にすることで、無理なく満足度を高められます。'),
            'N-CO-SP|M-SN': ('癒し温泉派', '温泉やスパを中心に、心身のリラックスを大切にするタイプです。朝から穏やかなスケジュールで過ごし、移動負担を抑えた近場滞在型の計画が向いています。人気時間帯は予約を活用するとなお快適です。'),
            'N-EX-OU|F-ML': ('自然満喫アクティブ派', 'ハイキングや海・山のアクティビティを取り入れて、自然の中で能動的に楽しむタイプです。行程は柔軟に調整しつつ、距離のある自然スポットにも遠征できる体力と意欲があります。天候や装備の準備が充実度を左右します。'),
            'E-CO-CI|M-SN': ('イベント効率派', 'ライブやスポーツ観戦、親族訪問などイベント中心に予定を組み、動線最適化で負担を抑えるタイプです。朝型で短距離の移動を基本に、タイムテーブルと移動計画の工夫で快適に過ごします。'),
            'S-EX-OU|M-NL': ('名所＋アウトドア派', '定番観光スポットと自然体験の両方を欲張りに楽しむタイプです。朝から活動的に動き、遠方や乗り継ぎを伴う長距離移動にも耐性があります。余裕を持った行程設計が満足度を高めます。'),
            'G-FO-RU|L-MN': ('ローカル食×田舎派', '郷土料理や市場での食体験をメインに、田舎でゆったり滞在するタイプです。昼型のリズムで、公共交通や短めのドライブを組み合わせながら中距離まで足を伸ばします。土地の暮らしに触れる時間が旅の質を高めます。'),
            'N-RE-SP|M-SY': ('究極リラックス派', 'ホテルや温泉を中心に、アクティビティを最小限にして徹底的に休むことを重視するタイプです。近場で移動負担を抑え、静かな環境でゆっくり過ごすと満足度が高まります。'),
            'S-EX-CU|N-LL': ('文化夜活派', '展覧会や文化施設を楽しみつつ、夜間イベントやライトアップも取り入れるタイプです。夜型の行動パターンで、遠方都市への長距離移動にも積極的に挑みます。会期や営業時間の事前確認が鍵になります。'),
            'E-BU-CI|F-MS': ('予算管理イベント派', 'イベント参加を軸に、費用対効果を意識した計画を立てるタイプです。柔軟なスケジュール運用で中距離まで対応し、宿や交通費の最適化が満足度に直結します。'),
            'S-CO-CI|N-SN': ('夜景キュレーター', '都市の夜景と写真映えを重視して、夕方以降の撮影や散策を楽しむタイプです。光の演出やビュースポットの選定が重要で、近場中心の計画でも十分に魅力を引き出せます。'),
            'S-EX-CU|M-LL': ('史跡ハンター', '歴史的な史跡を目的地に据え、長距離の遠征も辞さないタイプです。移動と見学のメリハリをつけ、交通手段の最適化と余白のある行程設計で充実度を高めます。'),
            'S-EX-OU|M-ML': ('季節追い', '桜や紅葉など季節の見頃を追いかけるタイプです。天候や混雑の変動に備え、予備日や時間帯の工夫でベストコンディションを狙います。中長距離の移動も視野に入ります。'),
            'S-CO-OU|F-LL': ('絶景ハンター', '映える自然景観を求めて長距離でも遠征するタイプです。光や天候の条件を見極め、予備日や現地滞在を厚めに取ることで、理想の一枚に近づけます。'),
            'G-FO-CI|L-SN': ('屋台ハンター', '屋台やB級グルメを気軽に楽しむタイプです。昼型で無理のないペースを保ち、近場中心の食べ歩きで満足度を高めます。'),
            'G-FO-CI|M-SN': ('予約主義者', '人気店を確実に押さえるため、予約と時間管理を徹底するタイプです。移動負担は抑えつつ、確度の高い食体験を組み立てます。'),
            'G-FO-CI|N-SN': ('ナイトグルマー', '夜営業の店も積極的に活用し、近場中心でグルメを楽しむタイプです。時間帯選びと移動の簡素化で快適さを保ちます。'),
            'G-LO-RU|M-SN': ('農泊テイスター', '農家民宿での滞在を通じて地産地消を体験するタイプです。ゆったりしたスケジュールで、地域の食文化と暮らしに触れる時間を重視します。'),
            'N-CO-OU|M-SY': ('高原ピクニッカー', '高地や高原で軽めのアクティビティを楽しむタイプです。負担の少ない計画で、爽やかな環境を満喫します。'),
            'N-RE-OU|L-SN': ('海風スロー派', '海辺でのんびり過ごすこと自体を目的にするタイプです。連泊を取り入れて、何もしない贅沢を味わいます。'),
            'N-EX-OU|M-LL': ('オーロラ追跡者', '遠征をいとわず、特別な絶景を追い求めるタイプです。時期や場所の選定が成否を分けるため、準備と余裕を持った計画が重要です。'),
            'E-CO-CI|F-MS': ('タイムテーブラー', '予算と時間を綿密に管理してイベント参加を最適化するタイプです。移動経路や滞在時間の調整で、中距離の行程でも安定感のある旅になります.'),
        }

        mbti_name, mbti_description = TYPE_DEFS.get(mbti_code_db, (mbti_code_db, "説明なし"))

        # --- user_mbti に保存（再診断対応：存在すれば UPDATE） ---
        cur.execute("SELECT id FROM user_mbti WHERE user_id=%s", (user_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE user_mbti
                SET mbti_id=%s, code=%s, name=%s, description=%s
                WHERE user_id=%s
            """, (mbti_id, mbti_code_db, mbti_name, mbti_description, user_id))
        else:
            cur.execute("""
                INSERT INTO user_mbti (user_id, mbti_id, code, name, description, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (user_id, mbti_id, mbti_code_db, mbti_name, mbti_description))

        conn.commit()
        cur.close()
        conn.close()

        flash("旅行タイプ診断の回答を保存しました！", "success")

        return render_template(
            "mbti/mbti_result.html",
            username=username,
            mbti_id=mbti_id,
            mbti_name=mbti_name,
            mbti_description=mbti_description,
            mbti_code=mbti_code_db,
            label=result.get("label", ""),
            travel_name=result.get("travel_name", "")
        )

    # --- 初回アクセス ---
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