# travel_mbti_logic_safe.py
from collections import Counter

def calculate_travel_mbti_safe(form):
    """
    完全安全版：必ず近似分類を返す
    """

    # --- 回答取得と初期化 ---
    P = form.get("q_purpose", "N")       # S/G/N/E
    V = form.get("q_priority", "EX")     # EX/FO/BU/CO
    T = form.get("q_theme", "CU")        # CU/OU/SP/CI/RU
    R = form.get("q_rhythm", "N")        # M/L/N/F
    motion_raw = form.get("q_motion", "N_NONE")
    dist_raw = form.get("q_distance", "M")  # S/M/ML/L
    want = form.get("q_want")
    avoid = form.get("q_avoid")

    # D軸スコア（僅差タイブレーク用）
    d_scores = Counter(GO=0, LO=0, RE=0, AV=0)
    if want == "GO_SPOT" or want == "GO_ACTIVE":
        d_scores["GO"] += 1
    elif want == "LO_LOCAL":
        d_scores["LO"] += 1
    elif want == "RE_EASE":
        d_scores["RE"] += 1

    co_hint = False
    if avoid in ("AV_QUEUE", "AV_WALK", "AV_FOOD", "AV_NIGHT"):
        d_scores["AV"] += 1
        if avoid == "AV_WALK":
            d_scores["RE"] += 0.5
        if avoid == "AV_QUEUE":
            co_hint = True

    # 距離正規化
    M_dist = {"S":"SY","M":"MN","ML":"ML","L":"LL"}.get(dist_raw, "MN")

    # D代表
    D_rep = "GO"
    if d_scores["LO"] >= d_scores["GO"] and d_scores["LO"] >= d_scores["RE"]:
        D_rep = "LO"
    elif d_scores["RE"] >= d_scores["GO"] and d_scores["RE"] >= d_scores["LO"]:
        D_rep = "RE"

    # ユーザーコード
    code = f"{P}-{V}-{T}|{R}-{M_dist}"

    # --- TYPE_DEFS 24件完全統合 ---
    TYPE_DEFS = {
        'S-EX-CU|M-NM': ('スポット制覇派', '文化的名所を効率よく巡るタイプです。'),
        'S-CO-CI|F-SN': ('快適都市散策派', '街歩きと写真映えをバランスよく楽しむタイプです。'),
        'G-FO-CI|N-ML': ('グルメ都市派', '話題のレストラン巡りやナイトライフを積極的に楽しむタイプです。'),
        'G-BU-CI|L-SY': ('節約グルメ派', 'コスパ重視でローカル食体験を楽しむタイプです。'),
        'N-CO-SP|M-SN': ('癒し温泉派', '温泉やスパで心身をリラックスさせるタイプです。'),
        'N-EX-OU|F-ML': ('自然満喫アクティブ派', '自然の中で能動的に楽しむタイプです。'),
        'E-CO-CI|M-SN': ('イベント効率派', 'イベント中心に予定を組むタイプです。'),
        'S-EX-OU|M-NL': ('名所＋アウトドア派', '観光スポットと自然体験を両方楽しむタイプです。'),
        'G-FO-RU|L-MN': ('ローカル食×田舎派', '郷土料理や市場をメインに田舎滞在を楽しむタイプです。'),
        'N-RE-SP|M-SY': ('究極リラックス派', 'アクティビティを最小限にして休むタイプです。'),
        'S-EX-CU|N-LL': ('文化夜活派', '夜イベントやライトアップを楽しむタイプです。'),
        'E-BU-CI|F-MS': ('予算管理イベント派', 'イベント参加を軸に費用対効果を重視するタイプです。'),
        'S-CO-CI|N-SN': ('夜景キュレーター', '都市の夜景や撮影を楽しむタイプです。'),
        'S-EX-CU|M-LL': ('史跡ハンター', '歴史的史跡を目的地に長距離移動も辞さないタイプです。'),
        'S-EX-OU|M-ML': ('季節追い', '桜や紅葉など季節の見頃を追いかけるタイプです。'),
        'S-CO-OU|F-LL': ('絶景ハンター', '映える自然景観を求め長距離遠征するタイプです。'),
        'G-FO-CI|L-SN': ('屋台ハンター', '屋台やB級グルメを気軽に楽しむタイプです。'),
        'G-FO-CI|M-SN': ('予約主義者', '人気店を押さえるため予約と時間管理を徹底するタイプです。'),
        'G-FO-CI|N-SN': ('ナイトグルマー', '夜営業の店を積極活用するタイプです。'),
        'G-LO-RU|M-SN': ('農泊テイスター', '農家民宿で地域の食文化と暮らしを体験するタイプです。'),
        'N-CO-OU|M-SY': ('高原ピクニッカー', '高地や高原で軽めのアクティビティを楽しむタイプです。'),
        'N-RE-OU|L-SN': ('海風スロー派', '海辺でのんびり過ごすタイプです。'),
        'N-EX-OU|M-LL': ('オーロラ追跡者', '特別な絶景を追い求めるタイプです。'),
        'E-CO-CI|F-MS': ('タイムテーブラー', '予算と時間を綿密に管理してイベント参加を最適化するタイプです。'),
    }

    # --- 近似分類 ---
    def parse_code(c):
        left, right = c.split("|")
        p, v, t = left.split("-")
        r, m = right.split("-")
        return {"P": p, "V": v, "T": t, "R": r, "M": m}

    W_P, W_V, W_T, W_R, W_M = 3, 2, 3, 2, 2
    user = {"P": P, "V": V, "T": T, "R": R, "M": M_dist}
    best, best_score = [], -1

    for cand_code, (label, desc) in TYPE_DEFS.items():
        parts = parse_code(cand_code)
        score = 0
        score += W_P if parts["P"] == user["P"] else 0
        score += W_V if parts["V"] == user["V"] else 0
        score += W_T if parts["T"] == user["T"] else 0
        score += W_R if parts["R"] == user["R"] else 0
        score += W_M if parts["M"] == user["M"] else 0
        if score > best_score:
            best = [cand_code]
            best_score = score
        elif score == best_score:
            best.append(cand_code)

    # タイブレーク
    normalized_code = best[0]

    label, desc = TYPE_DEFS[normalized_code]
    mbti_result = label

    # 補助ヒント
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

    return {
        "code": code,
        "label": label,
        "description": desc,
        "mbti_result": mbti_result,
        "travel_name": normalized_code,
        "mbti_description": desc
    }
