CREATE TABLE place_movements (
  id SERIAL PRIMARY KEY,
  from_place_id INTEGER REFERENCES places(id) ON DELETE CASCADE,
  to_place_id INTEGER REFERENCES places(id) ON DELETE CASCADE,
  transport_mode VARCHAR(50),       -- "徒歩" "バス" "新幹線" など
  duration_min INT,                 -- 移動時間（分）
  cost INT,                         -- 移動費（円）
  notes TEXT
);