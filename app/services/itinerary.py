# app/services/itinerary.py
from __future__ import annotations
import os, json, re
from typing import List
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


def _extract_json(text: str) -> str:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("LLM出力にJSONが見つかりません")
    return m.group(0)


def generate_itinerary(user: dict, req: dict) -> Plan:
    schema_str = json.dumps(Plan.model_json_schema(), ensure_ascii=False, indent=2)

    sys = (
        "あなたは旅行プランナーです。必ず有効なJSONのみを返し、説明文は出力しないでください。"
        "予算を超えないように配分し、各日のAM/PM/nightを必ず埋めてください。"
        "根拠は'rationale'に短文配列で。金額は日本円整数。"
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
  budget_jpy: {req.get('budget')}
  notes:      {req.get('notes','')}
"""
    fmt = "次のJSONスキーマに厳密準拠。JSON以外は出力不可：\n" + schema_str

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
        return Plan.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"LLM出力の検証に失敗: {e}")
