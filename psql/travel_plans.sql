--生成した旅行の内容の大元を表示させる
CREATE TABLE travel_plans (
  id SERIAL PRIMARY KEY,
  request_id INTEGER REFERENCES travel_requests(id) ON DELETE CASCADE,
  title VARCHAR(200),
  summary TEXT,
  budget_transport INT,
  budget_lodging INT,
  budget_food INT,
  budget_activities INT,
  budget_other INT,
  total_budget INT,
  rationale JSONB,
  raw_response JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE public.travel_plans (
    id                  SERIAL PRIMARY KEY,
    request_id          INTEGER REFERENCES public.travel_requests(id) ON DELETE CASCADE,
    title               VARCHAR(200),
    summary             TEXT,
    budget_transport    INTEGER,
    budget_lodging      INTEGER,
    budget_food         INTEGER,
    budget_activities   INTEGER,
    budget_other        INTEGER,
    total_budget        INTEGER,
    rationale           JSONB,
    raw_response        JSONB,
    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    overview            TEXT,
    return_trip         JSONB,
    lodging_suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    saved               BOOLEAN NOT NULL DEFAULT false
);


UPDATE travel_plans
SET saved = TRUE;
