-- Job Market Heatmap — initial schema

CREATE TABLE IF NOT EXISTS raw_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    adzuna_id       TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    company         TEXT,
    location_city   TEXT,
    location_region TEXT,
    location_lat    REAL,
    location_lon    REAL,
    salary_min      REAL,
    salary_max      REAL,
    salary_is_estimated INTEGER DEFAULT 0,
    description     TEXT NOT NULL,
    canonical_role  TEXT,
    source          TEXT DEFAULT 'adzuna',
    fetched_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_canonical_role ON raw_jobs(canonical_role);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_location_city ON raw_jobs(location_city);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_fetched_at ON raw_jobs(fetched_at);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_salary_min ON raw_jobs(salary_min);

CREATE TABLE IF NOT EXISTS job_skills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL REFERENCES raw_jobs(id) ON DELETE CASCADE,
    skill_raw   TEXT NOT NULL,
    skill_norm  TEXT NOT NULL,
    confidence  REAL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill_norm ON job_skills(skill_norm);
CREATE INDEX IF NOT EXISTS idx_job_skills_job_id ON job_skills(job_id);

CREATE TABLE IF NOT EXISTS skill_cooccurrence (
    skill_a     TEXT NOT NULL,
    skill_b     TEXT NOT NULL,
    count       INTEGER DEFAULT 0,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_a, skill_b)
);

CREATE TABLE IF NOT EXISTS sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    jobs_fetched    INTEGER DEFAULT 0,
    jobs_inserted   INTEGER DEFAULT 0,
    jobs_skipped    INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'running',
    error_message   TEXT
);
