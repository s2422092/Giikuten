CREATE TABLE IF NOT EXISTS user_mbti (
  id SERIAL PRIMARY KEY,             -- 自動採番ID
  user_id INTEGER NOT NULL,          -- ユーザーID
  mbti_id INTEGER NOT NULL,          -- mbtiテーブルのID
  code TEXT NOT NULL,                -- MBTIコード
  name TEXT NOT NULL,                -- 表示名
  description TEXT NOT NULL,         -- 詳細説明
  FOREIGN KEY (mbti_id) REFERENCES mbti (id) ON DELETE CASCADE
);
