CREATE TABLE IF NOT EXISTS mbti (
  id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 自動採番される数値ID
  code TEXT UNIQUE NOT NULL,             -- ユニークなタイプコード
  name TEXT NOT NULL,                    -- 日本語タイプ名
  description TEXT NOT NULL              -- 詳細説明（長文）
);