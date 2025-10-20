
--- 旅行mbti回答保存用テーブル ---
CREATE TABLE travel_survey (
    survey_id SERIAL PRIMARY KEY,               -- 回答ID（自動採番）
    user_id INTEGER,                            -- 回答者ユーザーID（ログイン連携がある場合）
    q_purpose VARCHAR(5) NOT NULL,              -- 1. 旅行の目的
    q_priority VARCHAR(5) NOT NULL,             -- 2. 重視ポイント
    q_theme VARCHAR(5) NOT NULL,                -- 3. 旅のテーマ
    q_want VARCHAR(20) NOT NULL,                -- 4. 絶対にしたいこと
    q_avoid VARCHAR(20) NOT NULL,               -- 5. 絶対に避けたいこと
    q_rhythm VARCHAR(2) NOT NULL,               -- 6. 活動リズム
    q_motion VARCHAR(10) NOT NULL,              -- 7. 乗り物酔い
    q_distance VARCHAR(5) NOT NULL,             -- 8. 旅行中の移動時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 登録日時
);