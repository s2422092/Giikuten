CREATE TABLE users (
u_id SERIAL PRIMARY KEY,                -- ユーザーID
u_name TEXT NOT NULL,                   -- ユーザー名
gmail TEXT UNIQUE NOT NULL,             -- Gmail（ユニーク制約推奨）
password TEXT NOT NULL                -- パスワード（将来はハッシュ化推奨）
);

ALTER TABLE user_mbti
ADD CONSTRAINT user_mbti_user_id_key UNIQUE (user_id);

これで、user_id に「重複禁止（UNIQUE）」制約が付きます。
その後、Flaskアプリを再起動すれば、あなたのコードはそのまま動作します 🎯