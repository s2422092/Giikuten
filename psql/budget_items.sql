CREATE TABLE budget_items (
  id SERIAL PRIMARY KEY,
  travel_plan_id INTEGER REFERENCES travel_plans(id) ON DELETE CASCADE,
  category VARCHAR(50) NOT NULL,    -- "交通費" "宿泊費" "食費" など
  amount INT NOT NULL,
  description TEXT
);
