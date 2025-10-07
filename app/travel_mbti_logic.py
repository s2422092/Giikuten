def calculate_travel_mbti(answers):
    plan = sum(answers[i] for i in [0, 3, 10, 12, 18, 27, 34]) / 7  # 計画性
    social = sum(answers[i] for i in [1, 6, 11, 17, 19, 20]) / 6   # 社交性
    spontaneity = sum(answers[i] for i in [5, 14, 23, 28, 31, 39]) / 6  # 自由度
    relaxation = sum(answers[i] for i in [16, 24, 29, 37]) / 4  # リラックス志向

    if plan > 3.5 and social > 3.5:
        return "アクティブプランナー"
    elif plan > 3.5 and social <= 3.5:
        return "静寂プランナー"
    elif plan <= 3.5 and spontaneity > 3.5:
        return "自由気ままトラベラー"
    elif social > 3.5 and relaxation > 3.5:
        return "社交的リゾート派"
    elif plan < 2.5 and relaxation > 3.5:
        return "癒し系リラクサー"
    elif social < 2.5 and plan > 3.5:
        return "研究家トラベラー"
    elif social < 2.5 and spontaneity > 3.5:
        return "孤高の冒険者"
    elif plan > 4 and spontaneity < 2.5:
        return "堅実派オーガナイザー"
    elif plan < 2.5 and spontaneity > 4:
        return "直感型ノマド"
    elif social > 4 and relaxation < 2.5:
        return "パーティーエクスプローラー"
    elif relaxation > 4:
        return "スローライフトラベラー"
    else:
        return "バランスタイプ"
