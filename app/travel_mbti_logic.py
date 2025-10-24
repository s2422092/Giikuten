# travel_mbti_logic.py

from collections import Counter

def calculate_travel_mbti(form):
    """
    問題数・診断結果（タイプ定義）は変更せず、スコアリングで近似を強化したバージョン。
    """

    # 1) 回答取得
    P = form.get("q_purpose")   # S/G/N/E
    V = form.get("q_priority")  # EX/FO/BU/CO
    T = form.get("q_theme")     # CU/OU/SP/CI/RU
    R = form.get("q_rhythm")    # M/L/N/F

    motion_raw = form.get("q_motion")   # Y_STRONG / Y_MILD / N_NONE
    dist_raw = form.get("q_distance")   # S / M / ML / L

    # D軸スコア（説明補助・僅差のタイブレーク用）
    d_scores = Counter(GO=0, LO=0, RE=0, AV=0)
    want = form.get("q_want")
    if want == "GO_SPOT":
        d_scores["GO"] += 1
    elif want == "LO_LOCAL":
        d_scores["LO"] += 1
    elif want == "RE_EASE":
        d_scores["RE"] += 1
    elif want == "GO_ACTIVE":
        d_scores["GO"] += 1

    avoid = form.get("q_avoid")
    co_hint = False
    if avoid in ("AV_QUEUE", "AV_WALK", "AV_FOOD", "AV_NIGHT"):
        d_scores["AV"] += 1
        if avoid == "AV_WALK":
            d_scores["RE"] += 0.5
        if avoid == "AV_QUEUE":
            co_hint = True

    # 距離カテゴリ（M側）の正規化
    if dist_raw == "S":
        M_dist = "SY"
    elif dist_raw == "M":
        M_dist = "MN"
    elif dist_raw == "ML":
        M_dist = "ML"
    elif dist_raw == "L":
        M_dist = "LL"
    else:
        M_dist = "MN"

    # D代表（説明補足用）
    D_rep = "GO"
    if d_scores["LO"] >= d_scores["GO"] and d_scores["LO"] >= d_scores["RE"]:
        D_rep = "LO"
    elif d_scores["RE"] >= d_scores["GO"] and d_scores["RE"] >= d_scores["LO"]:
        D_rep = "RE"

    # 生コード（ユーザー回答そのまま）
    code = f"{P}-{V}-{T}|{R}-{M_dist}"

    # タイプ定義（既存の辞書をそのまま利用）※説明文を第三者に説明する自然文へ更新
    TYPE_DEFS = {
        "S-EX-CU|M-NM": (
            "スポット制覇派（文化特化・朝型・中距離）",
            "このタイプは文化的な名所を効率よく巡るのが得意です。博物館や歴史的建築への関心が高く、午前から活動して時間を有効に使います。片道4~6時間程度の中距離移動も許容できるため、都市をまたぐプランでも無理なく組み立てられます。混雑が予想されるスポットは事前予約や早い時間帯の訪問を取り入れると、より快適に見学できます。"
        ),
        "S-CO-CI|F-SN": (
            "快適都市散策派（柔軟・短距離）",
            "街歩きと写真映えをバランスよく楽しむタイプです。行程は柔軟に調整し、混雑や移動負担を抑えることで快適さを重視します。近場の都市を中心に、カフェやフォトスポットを織り交ぜた散策が向いています。"
        ),
        "G-FO-CI|N-ML": (
            "グルメ都市派（夜型・中長距離可）",
            "話題のレストラン巡りやナイトライフを積極的に楽しむタイプです。行動は夜型で、片道4~6時間以上の移動もこなせるため、広域にわたって名店を目指す遠征プランにも適性があります。人気店は予約やオフピークの来店で快適度が上がります。"
        ),
        "G-BU-CI|L-SY": (
            "節約グルメ派（昼型・短距離＋酔いやすい）",
            "コスパにこだわり、ローカル食堂や市場での食体験を楽しむタイプです。昼型で計画を立て、乗り物酔いには配慮して近場中心の移動にすることで、無理なく満足度を高められます。"
        ),
        "N-CO-SP|M-SN": (
            "癒し温泉派（朝型・短距離志向）",
            "温泉やスパを中心に、心身のリラックスを大切にするタイプです。朝から穏やかなスケジュールで過ごし、移動負担を抑えた近場滞在型の計画が向いています。人気時間帯は予約を活用するとなお快適です。"
        ),
        "N-EX-OU|F-ML": (
            "自然満喫アクティブ派（柔軟・中長距離可）",
            "ハイキングや海・山のアクティビティを取り入れて、自然の中で能動的に楽しむタイプです。行程は柔軟に調整しつつ、距離のある自然スポットにも遠征できる体力と意欲があります。天候や装備の準備が充実度を左右します。"
        ),
        "E-CO-CI|M-SN": (
            "イベント効率派（朝型・短距離志向）",
            "ライブやスポーツ観戦、親族訪問などイベント中心に予定を組み、動線最適化で負担を抑えるタイプです。朝型で短距離の移動を基本に、タイムテーブルと移動計画の工夫で快適に過ごします。"
        ),
        "S-EX-OU|M-NL": (
            "名所＋アウトドア派（朝型・長距離強）",
            "定番観光スポットと自然体験の両方を欲張りに楽しむタイプです。朝から活動的に動き、遠方や乗り継ぎを伴う長距離移動にも耐性があります。余裕を持った行程設計が満足度を高めます。"
        ),
        "G-FO-RU|L-MN": (
            "ローカル食×田舎派（昼型・中距離/酔いなし）",
            "郷土料理や市場での食体験をメインに、田舎でゆったり滞在するタイプです。昼型のリズムで、公共交通や短めのドライブを組み合わせながら中距離まで足を伸ばします。土地の暮らしに触れる時間が旅の質を高めます。"
        ),
        "N-RE-SP|M-SY": (
            "究極リラックス派（朝型・短距離＋酔いやすい）",
            "ホテルや温泉を中心に、アクティビティを最小限にして徹底的に休むことを重視するタイプです。近場で移動負担を抑え、静かな環境でゆっくり過ごすと満足度が高まります。"
        ),
        "S-EX-CU|N-LL": (
            "文化夜活派（夜型・長距離強）",
            "展覧会や文化施設を楽しみつつ、夜間イベントやライトアップも取り入れるタイプです。夜型の行動パターンで、遠方都市への長距離移動にも積極的に挑みます。会期や営業時間の事前確認が鍵になります。"
        ),
        "E-BU-CI|F-MS": (
            "予算管理イベント派（柔軟・中距離）",
            "イベント参加を軸に、費用対効果を意識した計画を立てるタイプです。柔軟なスケジュール運用で中距離まで対応し、宿や交通費の最適化が満足度に直結します。"
        ),
        "S-CO-CI|N-SN": (
            "夜景キュレーター（都市映え重視）",
            "都市の夜景と写真映えを重視して、夕方以降の撮影や散策を楽しむタイプです。光の演出やビュースポットの選定が重要で、近場中心の計画でも十分に魅力を引き出せます。"
        ),
        "S-EX-CU|M-LL": (
            "史跡ハンター（長距離文化遠征）",
            "歴史的な史跡を目的地に据え、長距離の遠征も辞さないタイプです。移動と見学のメリハリをつけ、交通手段の最適化と余白のある行程設計で充実度を高めます。"
        ),
        "S-EX-OU|M-ML": (
            "季節追い（旬の絶景狙い）",
            "桜や紅葉など季節の見頃を追いかけるタイプです。天候や混雑の変動に備え、予備日や時間帯の工夫でベストコンディションを狙います。中長距離の移動も視野に入ります。"
        ),
        "S-CO-OU|F-LL": (
            "絶景ハンター（映え自然・長距離可）",
            "映える自然景観を求めて長距離でも遠征するタイプです。光や天候の条件を見極め、予備日や現地滞在を厚めに取ることで、理想の一枚に近づけます。"
        ),
        "G-FO-CI|L-SN": (
            "屋台ハンター（ライト都市食）",
            "屋台やB級グルメを気軽に楽しむタイプです。昼型で無理のないペースを保ち、近場中心の食べ歩きで満足度を高めます。"
        ),
        "G-FO-CI|M-SN": (
            "予約主義者（名店確実派）",
            "人気店を確実に押さえるため、予約と時間管理を徹底するタイプです。移動負担は抑えつつ、確度の高い食体験を組み立てます。"
        ),
        "G-FO-CI|N-SN": (
            "ナイトグルマー（夜型・近場）",
            "夜営業の店も積極的に活用し、近場中心でグルメを楽しむタイプです。時間帯選びと移動の簡素化で快適さを保ちます。"
        ),
        "G-LO-RU|M-SN": (
            "農泊テイスター（食体験中心）",
            "農家民宿での滞在を通じて地産地消を体験するタイプです。ゆったりしたスケジュールで、地域の食文化と暮らしに触れる時間を重視します。"
        ),
        "N-CO-OU|M-SY": (
            "高原ピクニッカー（軽アクティビティ）",
            "高地や高原で軽めのアクティビティを楽しむタイプです。負担の少ない計画で、爽やかな環境を満喫します。"
        ),
        "N-RE-OU|L-SN": (
            "海風スロー派（海辺で何もしない）",
            "海辺でのんびり過ごすこと自体を目的にするタイプです。連泊を取り入れて、何もしない贅沢を味わいます。"
        ),
        "N-EX-OU|M-LL": (
            "オーロラ追跡者（遠征絶景狙い）",
            "遠征をいとわず、特別な絶景を追い求めるタイプです。時期や場所の選定が成否を分けるため、準備と余裕を持った計画が重要です。"
        ),
        "E-CO-CI|F-MS": (
            "タイムテーブラー（イベント最適化）",
            "予算と時間を綿密に管理してイベント参加を最適化するタイプです。移動経路や滞在時間の調整で、中距離の行程でも安定感のある旅になります。"
        ),
    }

    # 2) まずそのまま一致があれば採用
    normalized_code = code
    if normalized_code not in TYPE_DEFS:
        # 3) スコアリングで近似タイプを選ぶ

        # 重み（調整可能）
        W_P = 3  # 旅行目的
        W_V = 2  # 優先度
        W_T = 3  # テーマ
        W_R = 2  # リズム
        W_M = 2  # 距離カテゴリ
        # D補助はタイブレーク用

        # ユーザーの要素
        user = {"P": P, "V": V, "T": T, "R": R, "M": M_dist}

        def parse_code(c):
            # "P-V-T|R-M" を分解
            left, right = c.split("|")
            p, v, t = left.split("-")
            r, m = right.split("-")
            return {"P": p, "V": v, "T": t, "R": r, "M": m}

        best = []
        best_score = -1

        for cand_code in TYPE_DEFS.keys():
            parts = parse_code(cand_code)
            score = 0
            # 各要素一致で加点
            if parts["P"] == user["P"]:
                score += W_P
            if parts["V"] == user["V"]:
                score += W_V
            if parts["T"] == user["T"]:
                score += W_T
            if parts["R"] == user["R"]:
                score += W_R
            # 距離カテゴリは近似も許容（ML と MN 近接など）
            if parts["M"] == user["M"]:
                score += W_M
            else:
                # 近接ボーナス（ML と MN、SY と SN、LL と ML は+1）
                near_pairs = {("ML", "MN"), ("MN", "ML"), ("SY", "SN"), ("SN", "SY"), ("LL", "ML"), ("ML", "LL")}
                if (parts["M"], user["M"]) in near_pairs:
                    score += 1  # 近い距離カテゴリ

            if score > best_score:
                best = [cand_code]
                best_score = score
            elif score == best_score:
                best.append(cand_code)

        # タイブレーク（同点多数のとき）
        if len(best) > 1:
            # 1) D代表のニュアンスで選ぶ
            #   GO なら EX/OU/観光系を、LO なら LO/RU/CI（ローカル/田舎/都市散策）を、
            #   RE なら SP/短距離系を優先する簡易規則
            pref = []
            if D_rep == "GO":
                pref = ["EX", "OU", "CU", "CI"]
            elif D_rep == "LO":
                pref = ["LO", "RU", "CI"]
            elif D_rep == "RE":
                pref = ["SP", "SY", "SN"]

            def tie_key(c):
                parts = parse_code(c)
                bonus = 0
                # テーマ優先
                if parts["T"] in pref:
                    bonus += 1
                # CO志向ヒントがある場合は V=CO を微優遇
                if co_hint and parts["V"] == "CO":
                    bonus += 1
                # 夜型なら R=N を微優遇、朝型なら R=M を微優遇
                if R == "N" and parts["R"] == "N":
                    bonus += 1
                if R == "M" and parts["R"] == "M":
                    bonus += 1
                return -bonus  # 小さい方が優先されるため符号反転

            best.sort(key=tie_key)

        normalized_code = best[0]

    # ラベル・説明の確定
    if normalized_code in TYPE_DEFS:
        label, desc = TYPE_DEFS[normalized_code]
        mbti_result = label.split("（")[0]
        hints = []
        if co_hint:
            hints.append("混雑回避志向（事前予約・朝活が有効）")
        if D_rep == "RE":
            hints.append("休息重視（行程少なめ・連泊推奨）")
        elif D_rep == "LO":
            hints.append("ローカル体験重視（市場や路地散策）")
        elif D_rep == "GO":
            hints.append("スポット攻略志向（動線最適化）")
        if hints:
            desc = f"{desc} {' / '.join(hints)}"
    else:
        # ここには基本来ないが保険
        mbti_result = "バランスタイプ"
        label = "バランスタイプ（中庸設定）"
        desc = "目的や優先が拮抗。柔軟に組める万能型。"

    return {
        "code": code,
        "label": label,
        "description": desc,
        "mbti_result": mbti_result,
        "travel_name": normalized_code,
        "mbti_description": desc
    }