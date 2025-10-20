# travel_mbti_logic.py

from collections import Counter

def calculate_travel_mbti(form):
    """
    2〜4択の選択式フォーム回答から旅行タイプコード・ラベル・説明を生成します。

    入力（form）は Flask などで受け取った POST データを想定。
    以下の name を持つラジオボタンの value を使用します（mbti.html に合わせる）:
      - q_purpose: S/G/N/E
      - q_priority: EX/FO/BU/CO
      - q_theme: CU/OU/SP/CI/RU
      - q_want: GO_SPOT / LO_LOCAL / RE_EASE / GO_ACTIVE
      - q_avoid: AV_QUEUE / AV_WALK / AV_FOOD / AV_NIGHT
      - q_rhythm: M/L/N/F
      - q_motion: Y_STRONG / Y_MILD / N_NONE
      - q_distance: S/M/ML/L

    戻り値:
      {
        "code": "P-V-T|R-MM",  # 例: "G-FO-CI|N-ML"
        "label": "グルメ都市派（夜型・中長距離可）",
        "description": "話題店巡り、ナイトライフも楽しむ。移動は4~6時間以上も可。",
        "mbti_result": "グルメ都市派",        # テンプレ表示用のタイプ名
        "travel_name": "G-FO-CI|N-ML",       # コード（テンプレで hint として表示可）
        "mbti_description": "上記説明と同じか詳細版"  # 説明文
      }
    """

    # 1) 軸の確定（P, V, T, R, M）
    P = form.get("q_purpose")  # S/G/N/E
    V = form.get("q_priority") # EX/FO/BU/CO
    T = form.get("q_theme")    # CU/OU/SP/CI/RU
    R = form.get("q_rhythm")   # M/L/N/F

    # 移動耐性 M 軸（酔い Y/N + 距離 S/M/L）
    motion_raw = form.get("q_motion")        # Y_STRONG / Y_MILD / N_NONE
    dist_raw = form.get("q_distance")        # S / M / ML / L

    # Y/N 判定
    if motion_raw in ("Y_STRONG", "Y_MILD"):
        M_yn = "Y"
    else:
        M_yn = "N"

    # 距離レンジの正規化（ML は M/L の中庸扱いだがコードは ML をそのまま使う）
    if dist_raw == "S":
        M_dist = "SY"  # 近場派（Short + 酔い耐性記号は別で Y/N 付与するが、一覧に合わせて SY というラベル使用）
    elif dist_raw == "M":
        M_dist = "MN"  # 中距離（~4h）
    elif dist_raw == "ML":
        M_dist = "ML"  # 中長距離（~6h）
    elif dist_raw == "L":
        M_dist = "LL"  # 長距離（6h超）
    else:
        M_dist = "MN"  # 未設定は中距離にフォールバック

    # 2) D軸（GO/LO/RE/AV）のスコアリング
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
    if avoid in ("AV_QUEUE", "AV_WALK", "AV_FOOD", "AV_NIGHT"):
        d_scores["AV"] += 1
        # 補正（説明文でのニュアンス付け。コードには直接載せない）
        # 長歩き回避 → RE をやや補強
        if avoid == "AV_WALK":
            d_scores["RE"] += 0.5
        # 行列回避 → CO（快適/映え）志向の補助とみなす（説明用に反映）
        co_hint = (avoid == "AV_QUEUE")
    else:
        co_hint = False

    # D代表値（GO/LO/REの最大）
    D_rep = "GO"
    if d_scores["LO"] >= d_scores["GO"] and d_scores["LO"] >= d_scores["RE"]:
        D_rep = "LO"
    elif d_scores["RE"] >= d_scores["GO"] and d_scores["RE"] >= d_scores["LO"]:
        D_rep = "RE"

    # 3) タイプコード生成
    # 代表コードは P-V-T|R-M の形式だが、距離側は一覧に合わせて SY/MN/ML/LL を使用
    code = f"{P}-{V}-{T}|{R}-{M_dist}"

    # 4) 代表12タイプ＋周辺タイプのマップ（コード -> タイプ名・説明）
    TYPE_DEFS = {
        # 代表12タイプ
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
        # 周辺（例示）
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

    # 5) コードの補正・近似（代表12タイプに寄せるロジック）
    # - 移動耐性の N/Y をコードに直接含めない代わりに、距離側を SY/MN/ML/LL として表現
    # - 代表定義に存在しないコードは近似にマッピング
    # 近似規則：CI/RU のどちらか、CO/EX の優勢、R はそのまま、距離は ML→MN に丸める場合あり
    normalized_code = code

    # ML を代表定義に寄せたい場合の簡易丸め（必要に応じて）
    if normalized_code.endswith("|M-ML"):
        approx = normalized_code.replace("|M-ML", "|M-MN")
        if approx in TYPE_DEFS:
            normalized_code = approx

    # 定義がなければ、いくつかの代表に寄せるヒューリスティック
    if normalized_code not in TYPE_DEFS:
        # 文化夜活派に寄せる条件例
        if P == "S" and T == "CU" and R == "N":
            normalized_code = "S-EX-CU|N-LL" if M_dist == "LL" else "S-EX-CU|N-LL"
        # グルメ都市派に寄せる
        elif P == "G" and T == "CI" and R == "N":
            normalized_code = "G-FO-CI|N-ML"
        # 癒し温泉派に寄せる
        elif P == "N" and T == "SP" and R == "M":
            normalized_code = "N-CO-SP|M-SN"
        # イベント効率派に寄せる
        elif P == "E" and T == "CI" and R == "M":
            normalized_code = "E-CO-CI|M-SN"
        # 名所＋アウトドア派に寄せる
        elif P == "S" and T == "OU" and R == "M":
            normalized_code = "S-EX-OU|M-NL"
        # 快適都市散策派に寄せる
        elif P == "S" and T == "CI" and R == "F":
            normalized_code = "S-CO-CI|F-SN"

    # 6) ラベル・説明の確定
    if normalized_code in TYPE_DEFS:
        label, desc = TYPE_DEFS[normalized_code]
        mbti_result = label.split("（")[0]  # 括弧前をタイプ名とする
        # 説明補足（CO 行列回避ヒントや D代表値のニュアンス）
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
        # 未定義コードは中庸へフォールバック
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