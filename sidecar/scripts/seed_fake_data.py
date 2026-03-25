#!/usr/bin/env python3
"""Seed fake job data for development — run from sidecar/ directory."""

import random
import sqlite3
import sys
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import get_db  # noqa: E402

CITIES: list[tuple[str, str, float, float]] = [
    ("San Francisco", "California", 37.7749, -122.4194),
    ("New York", "New York", 40.7128, -74.0060),
    ("Seattle", "Washington", 47.6062, -122.3321),
    ("Austin", "Texas", 30.2672, -97.7431),
    ("Chicago", "Illinois", 41.8781, -87.6298),
    ("Boston", "Massachusetts", 42.3601, -71.0589),
    ("Denver", "Colorado", 39.7392, -104.9903),
    ("Los Angeles", "California", 34.0522, -118.2437),
]

ROLES: list[str] = [
    "Software Engineer",
    "Senior Software Engineer",
    "DevOps / Platform Engineer",
    "Data Engineer",
    "Data Scientist",
    "Security Engineer",
    "IT Support / SysAdmin",
    "Engineering Manager",
    "Product Manager",
]

ROLE_WEIGHTS: list[int] = [25, 20, 12, 10, 8, 5, 8, 5, 7]

ROLE_SKILLS: dict[str, list[str]] = {
    "Software Engineer": [
        "Python", "JavaScript", "TypeScript", "React", "Node.js",
        "Git", "SQL", "REST APIs", "Docker", "PostgreSQL",
    ],
    "Senior Software Engineer": [
        "Python", "Java", "Kubernetes", "AWS", "System design",
        "Code review", "CI/CD", "Microservices", "PostgreSQL", "Redis",
    ],
    "DevOps / Platform Engineer": [
        "Kubernetes", "Docker", "Terraform", "AWS", "CI/CD",
        "Linux", "Ansible", "Prometheus", "Grafana", "Python",
    ],
    "Data Engineer": [
        "Python", "SQL", "Apache Spark", "Apache Airflow", "AWS",
        "ETL", "PostgreSQL", "Apache Kafka", "Snowflake", "dbt",
    ],
    "Data Scientist": [
        "Python", "Machine learning", "TensorFlow", "SQL", "Statistics",
        "Deep learning", "Natural language processing", "Pandas", "R",
        "Data visualization",
    ],
    "Security Engineer": [
        "Network security", "Python", "Linux", "AWS", "Penetration testing",
        "OWASP", "Encryption", "Docker", "Compliance", "SIEM",
    ],
    "IT Support / SysAdmin": [
        "Linux", "Windows", "Active Directory", "Networking", "PowerShell",
        "Help desk", "TCP/IP", "DNS", "Virtualization", "Troubleshooting",
    ],
    "Engineering Manager": [
        "Agile methodology", "Project management", "Python", "System design",
        "Code review", "CI/CD", "AWS", "Leadership", "Scrum",
        "Technical writing",
    ],
    "Product Manager": [
        "Agile methodology", "Product strategy", "Data analysis", "SQL",
        "Project management", "User research", "Scrum", "A/B testing",
        "Roadmapping", "Stakeholder management",
    ],
}

COMPANIES: list[str | None] = [
    "Acme Corp", "TechStart Inc", "DataFlow Systems", "CloudNine Labs",
    "SecureNet", "BuildFast", "ScaleUp", "CodeCraft", "InnovateTech",
    "DigitalForge", None,
]

SALARY_RANGES: dict[str, tuple[int, int]] = {
    "Software Engineer": (90_000, 160_000),
    "Senior Software Engineer": (140_000, 220_000),
    "DevOps / Platform Engineer": (100_000, 175_000),
    "Data Engineer": (100_000, 180_000),
    "Data Scientist": (95_000, 170_000),
    "Security Engineer": (100_000, 180_000),
    "IT Support / SysAdmin": (55_000, 100_000),
    "Engineering Manager": (150_000, 250_000),
    "Product Manager": (120_000, 210_000),
}

NUM_JOBS = 400
WEEKS_BACK = 6


def _random_fetched_at() -> str:
    """Random datetime within the last WEEKS_BACK weeks."""
    now = datetime.now()
    offset_days = random.randint(0, WEEKS_BACK * 7)
    offset_seconds = random.randint(0, 86_400)
    dt = now - timedelta(days=offset_days, seconds=offset_seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def seed() -> None:
    """Generate and insert seed data."""
    db = get_db()

    # Clean previous seed data
    db.execute("DELETE FROM job_skills WHERE job_id IN (SELECT id FROM raw_jobs WHERE source = 'seed')")
    db.execute("DELETE FROM raw_jobs WHERE source = 'seed'")
    db.commit()

    jobs_inserted = 0
    skills_inserted = 0

    for i in range(NUM_JOBS):
        city, region, lat, lon = random.choice(CITIES)
        role = random.choices(ROLES, weights=ROLE_WEIGHTS, k=1)[0]
        company = random.choice(COMPANIES)

        # 30% chance of NULL salary
        salary_min: float | None = None
        salary_max: float | None = None
        salary_is_estimated = 0
        if random.random() > 0.3:
            low, high = SALARY_RANGES[role]
            salary_min = round(random.uniform(low, high * 0.8), -3)
            salary_max = round(salary_min + random.uniform(10_000, 40_000), -3)
        else:
            salary_is_estimated = 1

        fetched_at = _random_fetched_at()

        cursor: sqlite3.Cursor = db.execute(
            """
            INSERT INTO raw_jobs (
                adzuna_id, title, company, location_city, location_region,
                location_lat, location_lon, salary_min, salary_max,
                salary_is_estimated, description, canonical_role, source, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'seed', ?)
            """,
            (
                f"seed-{i}",
                role,
                company,
                city,
                region,
                lat,
                lon,
                salary_min,
                salary_max,
                salary_is_estimated,
                f"Seed job posting for {role} at {company or 'Unknown'}.",
                role,
                fetched_at,
            ),
        )
        job_id: int = cursor.lastrowid  # type: ignore[assignment]
        jobs_inserted += 1

        # 3-6 random skills from this role's skill list
        role_skill_pool = ROLE_SKILLS[role]
        num_skills = random.randint(3, min(6, len(role_skill_pool)))
        selected_skills = random.sample(role_skill_pool, num_skills)

        for skill in selected_skills:
            db.execute(
                """
                INSERT INTO job_skills (job_id, skill_raw, skill_norm, confidence)
                VALUES (?, ?, ?, ?)
                """,
                (job_id, skill, skill, round(random.uniform(0.7, 1.0), 2)),
            )
            skills_inserted += 1

    db.commit()

    # Rebuild skill_cooccurrence table
    db.execute("DELETE FROM skill_cooccurrence")

    # For each job, generate all unique skill pairs and count them
    job_rows = db.execute(
        "SELECT id FROM raw_jobs WHERE source = 'seed'"
    ).fetchall()

    pair_counts: dict[tuple[str, str], int] = {}
    for job_row in job_rows:
        skill_rows = db.execute(
            "SELECT skill_norm FROM job_skills WHERE job_id = ?",
            (job_row["id"],),
        ).fetchall()
        skill_names = sorted({s["skill_norm"] for s in skill_rows})
        for a, b in combinations(skill_names, 2):
            key = (a, b)
            pair_counts[key] = pair_counts.get(key, 0) + 1

    for (skill_a, skill_b), count in pair_counts.items():
        db.execute(
            """
            INSERT INTO skill_cooccurrence (skill_a, skill_b, count, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (skill_a, skill_b, count),
        )

    db.commit()

    cooccurrence_pairs = len(pair_counts)

    print(f"Seed complete:")
    print(f"  Jobs inserted:        {jobs_inserted}")
    print(f"  Skills inserted:      {skills_inserted}")
    print(f"  Co-occurrence pairs:  {cooccurrence_pairs}")


if __name__ == "__main__":
    seed()
