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

    # タイプ定義（既存の辞書をそのまま利用）
    TYPE_DEFS = {
        "S-EX-CU|M-NM": ("スポット制覇派（文化特化・朝型・中距離）",
                         "名所を効率よく回す。博物館・歴史建築が好き。午前から動き、4~6時間の移動も許容。"),
        "S-CO-CI|F-SN": ("快適都市散策派（柔軟・短距離）",
                         "街歩き＋写真映え重視。混雑回避や移動負担を抑え、近場の都市で計画。"),
        "G-FO-CI|N-ML": ("グルメ都市派（夜型・中長距離可）",
                         "話題店巡り、ナイトライフも楽しむ。移動は4~6時間以上も可。"),
        "G-BU-CI|L-SY": ("節約グルメ派（昼型・短距離＋酔いやすい）",
                         "コスパ重視でローカル食堂や市場。乗り物酔いあり、近場中心。"),
        "N-CO-SP|M-SN": ("癒し温泉派（朝型・短距離志向）",
                         "温泉・スパでのんびり。移動負担を抑え、朝活で健康的に。"),
        "N-EX-OU|F-ML": ("自然満喫アクティブ派（柔軟・中長距離可）",
                         "ハイキングや海山アクティビティ。距離のある自然スポットも狙う。"),
        "E-CO-CI|M-SN": ("イベント効率派（朝型・短距離志向）",
                         "ライブ/スポーツ/親族訪問などを中心に、動線最適化で負担軽減。"),
        "S-EX-OU|M-NL": ("名所＋アウトドア派（朝型・長距離強）",
                         "観光と自然の両取り。遠方・乗り継ぎもこなす計画派。"),
        "G-FO-RU|L-MN": ("ローカル食×田舎派（昼型・中距離/酔いなし）",
                         "郷土料理や市場、のんびり滞在。公共交通＋短めドライブ程度可。"),
        "N-RE-SP|M-SY": ("究極リラックス派（朝型・短距離＋酔いやすい）",
                         "ホテル・温泉中心、アクティビティは最小限。近場で負担軽く。"),
        "S-EX-CU|N-LL": ("文化夜活派（夜型・長距離強）",
                         "展覧会や夜間イベントも。遠方都市へも積極的に。"),
        "E-BU-CI|F-MS": ("予算管理イベント派（柔軟・中距離）",
                         "イベント参加に合わせて費用最適化。中距離までなら問題なし。"),
        "S-CO-CI|N-SN": ("夜景キュレーター（都市映え重視）",
                         "都市夜景と映えを重視。夕方以降の撮影・散策中心。"),
        "S-EX-CU|M-LL": ("史跡ハンター（長距離文化遠征）",
                         "遠方の史跡も攻める長距離派。交通最適化と余白計画が鍵。"),
        "S-EX-OU|M-ML": ("季節追い（旬の絶景狙い）",
                         "花見・紅葉など季節の見頃を追う。天候チェックが重要。"),
        "S-CO-OU|F-LL": ("絶景ハンター（映え自然・長距離可）",
                         "映える自然景観を長距離で狙う。予備日でベストショット。"),
        "G-FO-CI|L-SN": ("屋台ハンター（ライト都市食）",
                         "屋台やB級グルメを気軽に。昼型で無理なく食べ歩き。"),
        "G-FO-CI|M-SN": ("予約主義者（名店確実派）",
                         "予約で確実に名店を押さえる。時間管理が得意。"),
        "G-FO-CI|N-SN": ("ナイトグルマー（夜型・近場）",
                         "夜営業も活用しつつ、距離は控えめ。"),
        "G-LO-RU|M-SN": ("農泊テイスター（食体験中心）",
                         "農家民宿で地産地消を体験。ゆったり滞在。"),
        "N-CO-OU|M-SY": ("高原ピクニッカー（軽アクティビティ）",
                         "高地で軽めのアクティビティ。負担少なく爽やかに。"),
        "N-RE-OU|L-SN": ("海風スロー派（海辺で何もしない）",
                         "海辺でのんびり過ごす贅沢。連泊でゆるり。"),
        "N-EX-OU|M-LL": ("オーロラ追跡者（遠征絶景狙い）",
                         "遠征もいとわず絶景を狙う。時期選定が重要。"),
        "E-CO-CI|F-MS": ("タイムテーブラー（イベント最適化）",
                         "予算と時間を綿密管理。スケジュール精度が武器。"),
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