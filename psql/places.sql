--観光地や施設のデータ↓
CREATE TABLE places (
  id SERIAL PRIMARY KEY,
  day_plan_id INTEGER REFERENCES day_plans(id) ON DELETE CASCADE,
  time VARCHAR(10),
  name VARCHAR(255),
  description TEXT,
  stay_time VARCHAR(20),
  access TEXT,
  map_url TEXT
);