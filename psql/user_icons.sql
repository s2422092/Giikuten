CREATE TABLE user_icons (
    icon_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(u_id) ON DELETE CASCADE,
    icon_base64 TEXT NOT NULL,           -- Base64形式で画像データを保存
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);