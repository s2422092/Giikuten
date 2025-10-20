CREATE TABLE travel_survey (
    survey_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    q_purpose VARCHAR(5) NOT NULL,
    q_priority VARCHAR(5) NOT NULL,
    q_theme VARCHAR(5) NOT NULL,
    q_want VARCHAR(20) NOT NULL,
    q_avoid VARCHAR(20) NOT NULL,
    q_rhythm VARCHAR(2) NOT NULL,
    q_motion VARCHAR(10) NOT NULL,
    q_distance VARCHAR(5) NOT NULL,
    mbti_result VARCHAR(20),
    label VARCHAR(50),
    description TEXT,
    code VARCHAR(10),
    travel_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
