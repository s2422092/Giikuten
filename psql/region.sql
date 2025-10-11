CREATE TABLE region (
    r_id SERIAL PRIMARY KEY,
    r_name VARCHAR(255) NOT NULL
);

INSERT INTO region (r_name) VALUES
('北海道'),
('東北'),
('北関東'),
('首都圏'),
('甲信越'),
('北陸'),
('東海'),
('近畿'),
('山陽・山陰'),
('四国'),
('九州'),
('沖縄');