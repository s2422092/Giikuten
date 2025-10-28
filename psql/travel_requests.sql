--ここでは旅行プランを生成するためにのSQLクエリを記述します。
CREATE TABLE travel_requests (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(u_id) ON DELETE CASCADE,  -- ✅ 修正ポイント！
  trip_name VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  region VARCHAR(50) NOT NULL,
  prefecture VARCHAR(50),
  city VARCHAR(50),
  departure VARCHAR(100),
  transport_pref VARCHAR(30),
  budget INTEGER,
  must_visit TEXT,       -- 絶対に行きたい場所
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
