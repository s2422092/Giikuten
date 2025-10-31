# app/services/itinerary.py
from __future__ import annotations
import os, json, re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ValidationError
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =============================
# 🎯 JSON構造定義
# =============================


class Place(BaseModel):
    name: str  # 観光地・施設名
    description: str  # 短い説明（観光の見どころ）
    time: str  # 開始時刻（例: "9:00"）
    stay_time: str  # 滞在時間（例: "90分"）
    access: str  # 交通手段＋移動時間（例: "徒歩5分", "バス20分"）
    map_url: Optional[str]  # Google Mapsリンクなど（任意）
    cost_estimate: Optional[int] = None
    type: Optional[str] = None
    fun_fact: Optional[str] = None
    leave_time: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    theme: str  # 当日の目的・雰囲気
    route_summary: str  # 1日のルート概要（例: "京都駅→清水寺→祇園→ホテル"）
    places: List[Place]  # 訪問場所のリスト


class Budget(BaseModel):
    transport: int
    lodging: int
    food: int
    activities: int
    other: int


class LodgingSuggestion(BaseModel):
    name: str  # 宿名（例: ホテル名・旅館名）
    area: Optional[str] = None  # エリア（例: 京都駅周辺 / 嵐山）
    address: Optional[str] = None  # 住所
    nearest_station: Optional[str] = None  # 最寄駅（例: JR京都駅）
    access: Optional[str] = None  # 最寄からのアクセス（徒歩●分／バス●分など）
    price_per_night: Optional[str] = None  # 1泊あたりの目安（例: 8,000〜12,000円/室）
    room_type: Optional[str] = None  # シングル/ツイン/和室など
    capacity: Optional[int] = None  # 定員
    breakfast_included: Optional[bool] = None
    cancellation_policy: Optional[str] = None
    checkin: Optional[str] = None
    checkout: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    pros: Optional[List[str]] = None  # 良い点
    cons: Optional[List[str]] = None  # 留意点
    selection_reason: Optional[str] = None  # この宿を選んだ理由


class Plan(BaseModel):
    title: str
    summary: str
    budget_breakdown: Budget
    daily_plan: List[DayPlan]
    overview: str
    lodging_suggestions: Optional[List[LodgingSuggestion]] = None
    return_trip: Optional[Dict[str, Any]] = None
    rationale: List[str] = []
    raw_response: Dict[str, Any] | None = None


# =============================
# 🧠 GPT処理
# =============================


def _extract_json(text: str) -> str:
    """LLM出力から最初のJSONブロックを抽出"""
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("LLM出力にJSONが見つかりません")
    return m.group(0)


def generate_itinerary(user: dict, req: dict, mbti_info: dict | None = None) -> Dict:
    """LLMを呼び出して旅行プランJSONを生成"""
    schema_str = json.dumps(Plan.model_json_schema(), ensure_ascii=False, indent=2)

    # --- SYSTEM PROMPT ---
    sys = (
        "あなたは日本国内旅行のプロフェッショナルプランナーです。"
        "与えられるユーザーの性格タイプとその説明内の条件を考慮し、"
        "現実的で具体的な観光スポット・施設・交通手段を含む旅行プランを作成してください。"
        "出力は**有効なJSONのみ**で、説明文やマークダウンは禁止です。"
        "金額は整数円、日程や施設は実在する日本のものにしてください。"
    )

    # --- USER PROMPT ---
    usr = f"""
user_profile:
  name: {user.get('name')}
  mbti: {user.get('mbti')}
  mbti_summary: {(mbti_info or {}).get('description','')}
trip_request:
  trip_name: {req.get('trip_name')}
  start_date: {req.get('start_date')}
  end_date:   {req.get('end_date')}
  headcount:  {req.get('headcount')}
  area:       {req.get('area')}
  region:     {req.get('region')}
  prefecture: {req.get('prefecture')}
  city:       {req.get('city')}
  departure:  {req.get('departure')}
  transport_pref: {req.get('transport_pref')}
  budget_jpy: {req.get('budget')}
  notes:      {req.get('notes','')}
must_visit: {req.get('must_visit','')}
suggest_nearby: {req.get('suggest_nearby', False)}
"""

    # --- FORMAT PROMPT（スキーマ＋制約） ---
    fmt = (
        "次のJSONスキーマに厳密準拠。JSON以外は出力禁止。\n"
        "制約:\n"
        "- 各スポットは実在する日本の施設・観光地であること。\n"
        "- 'must_visit' に指定された場所は旅程（daily_plan.places）に極力含めること。物理的・時間的に困難な場合は代替案を明示。\n"
        "- 各timeは24時間表記（例: '9:00', '13:30'）。\n"
        "- accessには具体的な交通手段（徒歩・バス・電車・新幹線など）と**移動所要時間**を必ず含める。\n"
        "- stay_timeには**滞在時間の目安**を必ず記載（例: '90分', '2時間'）。\n"
        "- 各スポットには **leave_time**（出発目安時刻）を追加し、timestay_timeから算出する。\n"
        "- 宿泊施設は、name・address・最寄駅・アクセス・1泊料金・チェックイン/アウトなどの具体情報を含むこと。\n"
        "- 各dayには3〜5スポットを含む。\n"
        "- 各themeは1文で当日の目的・雰囲気を表現。\n"
        "- 出発地（departure）や transport_pref がある場合は出来る限り尊重。\n"
        "- 性格タイプの説明に基づき、活動量・時間配分を調整する。\n"
        "- Day1 では、出発地から目的地の主要駅（例: 京都駅）への**到着を明示**し、\n"
        "  その移動（例: 新幹線・飛行機）の情報を最初のスポットとして記載する。\n"
        "  例: name: '東京駅→京都駅', access: '東海道新幹線で約2時間20分', stay_time: '移動', description: '京都到着後に観光開始'。\n"
        "- 各スポットには 'fun_fact'（豆知識）を1文で付与（歴史・雑学・季節情報など）。\n"
        "- **帰路は必ず含める**。往路と同一手段を優先するが、transport_prefや距離/所要時間を考慮して最適化してよい。\n"
        "- 帰路の概要は 'return_trip' に JSON で格納（例: {'mode':'新幹線','from':'京都駅','to':'東京駅','duration':'約2時間20分'}）。\n"
        "- 宿について：\n"
        "  - req.suggest_final_lodging が true の場合：最終日の目的地周辺に type:'lodging' のスポットを1つ含める。\n"
        "  - lodging_suggestions には以下フィールドを持つオブジェクト配列を出力：\n"
        "    [{\n"
        "      name, area, address, nearest_station, access,\n"
        "      price_per_night, room_type, capacity, breakfast_included,\n"
        "      cancellation_policy, url, phone, checkin, checkout,\n"
        "      pros, cons, selection_reason\n"
        "    }]\n"
        "  - 価格は日本円の範囲表記可（例: '8,000〜12,000円/室'）。\n"
        "  - チェックイン/アウト時刻は日程（daily_plan）の最終/初回スポット時間と整合を取る。\n"
        "  - req.suggest_final_lodging が false の場合も、概要として2〜3件は出力する。\n"
        "- req.suggest_nearby が true の場合：\n"
        "  選択地域（例: 京都市右京区嵐山など）を主軸としつつ、2日目以降は現実的に日帰り可能な**近隣エリア**（例: 東山・祇園など）も含める。\n"
        "  ただし長距離移動は避け、滞在時間が十分確保できる距離に限定する。\n"
        "- 出力例:\n"
        "{\n"
        '  "title": "京都3日間の癒し旅",\n'
        '  "summary": "INFJタイプ向けの静寂と文化体験を中心とした京都プラン。",\n'
        '  "budget_breakdown": {"transport":20000,"lodging":30000,"food":10000,"activities":8000,"other":2000},\n'
        '  "daily_plan": [\n'
        '    {"day":1,"theme":"東山の古都情緒を巡る","route_summary":"東京駅→京都駅→清水寺→祇園→八坂神社",\n'
        '     "places":[\n'
        '       {"time":"8:00","name":"東京駅→京都駅","description":"京都到着後に観光開始。","stay_time":"移動","access":"東海道新幹線で約2時間20分"},\n'
        '       {"time":"10:30","name":"清水寺","description":"舞台からの眺めが絶景。","stay_time":"90分","access":"京都駅からバスで20分","fun_fact":"清水の舞台は釘をほぼ使わない伝統工法で組まれている"}\n'
        "     ]},\n"
        "    ...\n"
        "  ],\n"
        '  "overview": "朝は新幹線で京都へ。混雑前に東山エリアを回り、午後は祇園でゆったり。翌日は嵐山で自然散策中心に配分。",\n'
        '  "lodging_suggestions": [\n'
        "    {\n"
        '      "name":"ホテル京の風", "area":"京都駅周辺", "address":"京都市下京区…",\n'
        '      "nearest_station":"JR京都駅", "access":"京都駅から徒歩6分",\n'
        '      "price_per_night":"8,000〜12,000円/室", "room_type":"ツイン", "capacity":2,\n'
        '      "breakfast_included": true, "cancellation_policy":"前日まで無料/当日100%",\n'
        '      "url":"https://example.com", "phone":"075-xxx-xxxx",\n'
        '      "checkin":"15:00", "checkout":"10:00",\n'
        '      "pros":["駅近で移動が楽","観光拠点に最適"],\n'
        '      "cons":["繁華街に近く夜はやや騒がしい"],\n'
        '      "selection_reason":"京都駅ベースで動く本プランと相性がよいため"\n'
        "    }\n"
        "  ],\n"
        '  "return_trip": {"mode": "新幹線", "from": "京都駅", "to": "東京駅", "duration": "約2時間20分"},\n'
        '  "rationale": ["混雑回避のため朝活重視","徒歩圏内で移動負担軽減"]\n'
        "}\n"
        f"スキーマ:\n{schema_str}"
    )

    # --- GPT呼び出し ---
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": usr},
            {"role": "user", "content": fmt},
        ],
    )

    raw = resp.choices[0].message.content or ""
    data = json.loads(_extract_json(raw))

    try:
        plan = Plan.model_validate(data)
        plan_dict = plan.model_dump()
        plan_dict["raw_response"] = {
            "model": MODEL,
            "content": raw,
        }
        return plan_dict
    except ValidationError as e:
        raise RuntimeError(f"LLM出力の検証に失敗: {e}")
