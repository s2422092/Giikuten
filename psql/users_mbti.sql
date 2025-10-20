
CREATE TABLE travel_survey (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    q_purpose TEXT,
    q_priority TEXT,
    q_theme TEXT,
    q_want TEXT,
    q_avoid TEXT,
    q_rhythm TEXT,
    q_motion TEXT,
    q_distance TEXT,
    mbti_result TEXT,
    label TEXT,
    description TEXT,
    code TEXT,
    travel_name TEXT,
    mbti_description TEXT,  -- ← 追加
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
