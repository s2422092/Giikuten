# app/services/itinerary.py
from __future__ import annotations
import os, json, re
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class Budget(BaseModel):
    transport: int = 0
    lodging: int = 0
    food: int = 0
    activities: int = 0
    other: int = 0


class DayPlan(BaseModel):
    day: int
    am: str
    pm: str
    night: str


class Plan(BaseModel):
    title: str
    summary: str
    budget_breakdown: Budget
    daily_plan: List[DayPlan]
    rationale: List[str]
    # 画面でLLMの生出力を見られるように（任意）
    raw_response: Dict[str, Any] | None = None


def _extract_json(text: str) -> str:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("LLM出力にJSONが見つかりません")
    return m.group(0)


def generate_itinerary(user: dict, req: dict) -> Dict:
    schema_str = json.dumps(Plan.model_json_schema(), ensure_ascii=False, indent=2)

    sys = (
        "あなたは日本国内の旅行プランナーです。"
        "出力は必ず**有効なJSONのみ**（前後に説明文やマークダウン禁止）。"
        "各日の AM/PM/night は**具体的な施設・スポット名**と**移動手段**を必ず含める。"
        "例: 'AM: 東京駅→新幹線で京都駅へ（のぞみ75号）/ 清水寺見学' のように、"
        "移動の起点/終点、代表的な列車・路線・バス・飛行機・車移動の記述を試みる。"
        "予算配分は総額を超えない整数円。'rationale' は3〜6件の短文。"
    )
    usr = f"""
user_profile:
  name: {user.get('name')}
  mbti: {user.get('mbti')}
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
  transport_pref: {req.get('transport_pref')}   # 'auto' | 'train' | 'plane' | 'car' | 'bus' | 'mixed'
  budget_jpy: {req.get('budget')}
  notes:      {req.get('notes','')}
"""
    fmt = (
        "以下の **JSONスキーマ** に厳密準拠して出力。JSON以外は出力不可：\n"
        + schema_str
        + "\n"
        "制約:\n"
        "- 'title' は簡潔に（地名と日数が分かる）。\n"
        "- 'daily_plan' の各 'am' 'pm' 'night' は、"
        "  具体的スポット/施設名と移動手段（例: JR○○線/徒歩/市バス/レンタカー/飛行機 など）を含める。\n"
        "- 出発地（departure）や transport_pref がある場合は出来る限り尊重。"
    )

    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.6,
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
        # 画面でデバッグ表示できるよう生出力を添付
        plan_dict["raw_response"] = {
            "model": MODEL,
            "content": raw,
        }
        return plan_dict
    except ValidationError as e:
        raise RuntimeError(f"LLM出力の検証に失敗: {e}")
