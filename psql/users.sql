CREATE TABLE users (
u_id SERIAL PRIMARY KEY,                -- ユーザーID
u_name TEXT NOT NULL,                   -- ユーザー名
gmail TEXT UNIQUE NOT NULL,             -- Gmail（ユニーク制約推奨）
password TEXT NOT NULL,                 -- パスワード（将来はハッシュ化推奨）
);