
-- CREATE TABLE travel_survey (
--     id SERIAL PRIMARY KEY,
--     user_id INTEGER NOT NULL,
--     q_purpose TEXT,
--     q_priority TEXT,
--     q_theme TEXT,
--     q_want TEXT,
--     q_avoid TEXT,
--     q_rhythm TEXT,
--     q_motion TEXT,
--     q_distance TEXT,
--     mbti_result TEXT,
--     label TEXT,
--     description TEXT,
--     code TEXT,
--     travel_name TEXT,
--     mbti_description TEXT,  -- ← 追加
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );



-- 1️⃣ 質問テーブル
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question_code VARCHAR(10) UNIQUE NOT NULL,  -- 例: Q1, Q2, ...
    question_text TEXT NOT NULL
);

-- 2️⃣ 選択肢テーブル
CREATE TABLE options (
    id SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    option_code VARCHAR(10) NOT NULL,          -- 例: Q1_A1, Q1_A2, ...
    option_text TEXT NOT NULL                  
);

--質問データの挿入
-- 質問データ
INSERT INTO questions (question_code, question_text) VALUES
('Q1', '今回の旅行の主な目的は何ですか？'),
('Q2', '旅行で最も重視したいポイントは？'),
('Q3', '旅行のテーマを選ぶとしたら？');

-- Q1の選択肢
INSERT INTO options (question_id, option_code, option_text) VALUES
(1, 'Q1_A1', 'リラックスして癒されたい'),
(1, 'Q1_A2', 'アクティブに観光したい'),
(1, 'Q1_A3', '食を楽しみたい'),
(1, 'Q1_A4', '文化や歴史に触れたい');

-- Q2の選択肢
INSERT INTO options (question_id, option_code, option_text) VALUES
(2, 'Q2_A1', 'コスパ重視'),
(2, 'Q2_A2', '快適さ・宿重視'),
(2, 'Q2_A3', '移動の便利さ重視'),
(2, 'Q2_A4', '体験・アクティビティ重視');

-- Q3の選択肢
INSERT INTO options (question_id, option_code, option_text) VALUES
(3, 'Q3_A1', '自然満喫旅'),
(3, 'Q3_A2', 'グルメ旅'),
(3, 'Q3_A3', '温泉・癒し旅'),
(3, 'Q3_A4', '写真・映え旅'),
(3, 'Q3_A5', '歴史・文化旅');


-- 3️⃣ 回答テーブル
CREATE TABLE answers (
    answer_id SERIAL PRIMARY KEY,           -- 回答ID
    user_id INT REFERENCES users(u_id) ON DELETE CASCADE,  -- ユーザーID（外部キー）
    question_id INT REFERENCES questions(id) ON DELETE CASCADE, -- 質問ID
    option_id INT REFERENCES options(id) ON DELETE CASCADE,     -- 選択肢ID
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP             -- 回答日時
);

-- 🔹 user_id=1（鈴木さん）の回答
INSERT INTO answers (user_id, question_id, option_id) VALUES
(1, 1, 2),  -- 質問1：グルメ・食べ歩き
(1, 2, 1),  -- 質問2：観光の充実
(1, 3, 4),  -- 質問3：都市散策・ショッピング
(1, 4, 3),  -- 質問4：とにかくのんびり
(1, 5, 1),  -- 質問5：行列・混雑を避けたい
(1, 6, 2),  -- 質問6：昼型
(1, 7, 3),  -- 質問7：酔わない
(1, 8, 2);  -- 質問8：移動は4時間までOK

-- 🔹 user_id=2（田中さん）の回答
INSERT INTO answers (user_id, question_id, option_id) VALUES
(2, 1, 1),  -- 観光名所巡り
(2, 2, 2),  -- 食体験
(2, 3, 1),  -- 歴史・文化
(2, 4, 1),  -- 有名スポット制覇
(2, 5, 4),  -- 夜遅い行動を避けたい
(2, 6, 1),  -- 朝型
(2, 7, 2),  -- やや酔う
(2, 8, 1);  -- 移動は2時間以内

-- 4️⃣ 旅行タイプテーブル
CREATE TABLE travel_types (
    id SERIAL PRIMARY KEY,              -- 一意のID
    code TEXT UNIQUE NOT NULL,     -- 診断コード（例：'S-EX-CU|M-NM'）
    name TEXT NOT NULL,            -- タイプ名（例：'スポット制覇派（文化特化・朝型・中距離）'）
    description TEXT NOT NULL           -- タイプの説明文（例："名所を効率よく回す。博物館・歴史建築が好き..."）
);

-- 旅行タイプデータの挿入の例
INSERT INTO travel_types (code, name, description) VALUES
('S-EX-CU|M-NM', 'スポット制覇派（文化特化・朝型・中距離）', '名所を効率よく回す。博物館・歴史建築が好き。午前から動き、4~6時間の移動も許容。'),

-- 5️⃣ 診断結果テーブル
CREATE TABLE user_mbti (
    mbti_id SERIAL PRIMARY KEY,                     -- 結果ID
    user_id INT REFERENCES users(u_id) ON DELETE CASCADE,  -- ユーザー（外部キー）
    name INT REFERENCES travel_types(id) ON DELETE SET NULL, -- 診断タイプ（外部キー）
    code TEXT,                                 -- TYPE_DEFSのコード（例: 'S-EX-CU|M-NM'）
    result_summary TEXT,                              -- 結果の要約（タイプ名など）
    diagnosed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 診断実施日時
);
