CREATE TABLE user_mbti (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(u_id) ON DELETE CASCADE,
    mbti_type TEXT NOT NULL,             -- 診断結果（例: "ENFP"）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
