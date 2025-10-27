--生成した旅行の内容の大元を表示させる
CREATE TABLE travel_plans (
  id SERIAL PRIMARY KEY,
  request_id INTEGER REFERENCES travel_requests(id) ON DELETE CASCADE,
  title VARCHAR(200),
  summary TEXT,
  budget_transport INT,
  budget_lodging INT,
  budget_food INT,
  budget_activities INT,
  budget_other INT,
  rationale JSONB,     -- ["混雑回避のため朝活重視", ...]
  raw_response JSONB,   -- GPTの元出力を保存
  created_at TIMESTAMP DEFAULT NOW()
);