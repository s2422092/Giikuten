--1日ごとの行程↓
CREATE TABLE day_plans (
  id SERIAL PRIMARY KEY,
  travel_plan_id INTEGER REFERENCES travel_plans(id) ON DELETE CASCADE,
  day_number INT NOT NULL,
  theme VARCHAR(255),
  route_summary TEXT,
  total_time INT,             -- 当日の総行動時間（分）
  estimated_cost INT          -- 当日の想定支出
);

