# app/services/itinerary.py
from __future__ import annotations
import os, json, re
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
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
    """返答に前後説明が付いた場合でも、最初の JSON ブロックだけ抜く"""
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("LLM出力にJSONが見つかりません")
    return m.group(0)


def build_messages(user: Dict[str, Any], req: Dict[str, Any]) -> list[dict]:
    schema = Plan.model_json_schema()
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)

    system = (
        "あなたは旅行プランナーです。必ず**有効なJSONのみ**を出力してください。"
        "予算を超えないように配分し、各日のAM/PM/nightを必ず埋めてください。"
        "根拠は'rationale'に短文で列挙。数値は日本円の整数。"
    )

    user_block = f"""
user_profile:
  name: {user.get('name')}
  mbti: {user.get('mbti')}
trip_request:
  trip_name: {req.get('trip_name')}
  start_date: {req.get('start_date')}   # YYYY-MM-DD
  end_date:   {req.get('end_date')}     # YYYY-MM-DD
  headcount:  {req.get('headcount')}
  area:       {req.get('area')}
  budget_jpy: {req.get('budget')}
  notes:      {req.get('notes','')}
"""

    format_block = (
        "出力は次のJSONスキーマに**厳密に**一致させ、JSON以外の文字は出力しないこと。\n"
        + schema_str
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_block},
        {"role": "user", "content": format_block},
    ]


def generate_itinerary(user: Dict[str, Any], req: Dict[str, Any]) -> Plan:
    messages = build_messages(user, req)
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.6
    )
    raw = resp.choices[0].message.content or ""
    json_text = _extract_json(raw)
    data = json.loads(json_text)
    try:
        return Plan.model_validate(data)
    except ValidationError as e:
        # 失敗時は例外で上位に通知（フロントでflash表示）
        raise RuntimeError(f"LLM出力の検証に失敗: {e}")
