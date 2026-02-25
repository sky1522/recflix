"""
A/B Test Statistical Utilities

Z-test for proportions, Wilson score confidence intervals.
No scipy dependency — uses math.erf for normal CDF.
"""
import math
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def normal_cdf(x: float) -> float:
    """Standard normal CDF using built-in math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def z_test_proportions(
    successes_a: int, n_a: int, successes_b: int, n_b: int,
) -> tuple[float | None, float | None]:
    """Two-proportion Z-test (two-tailed).

    Returns (z_statistic, p_value) or (None, None) if sample < 30.
    """
    if n_a < 30 or n_b < 30:
        return None, None
    p_a = successes_a / n_a
    p_b = successes_b / n_b
    p_pool = (successes_a + successes_b) / (n_a + n_b)
    if p_pool <= 0.0 or p_pool >= 1.0:
        return None, None
    se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_a + 1.0 / n_b))
    if se == 0.0:
        return None, None
    z = (p_a - p_b) / se
    p_value = 2.0 * (1.0 - normal_cdf(abs(z)))
    return round(z, 4), round(p_value, 6)


def proportion_ci(successes: int, n: int) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.96
    p_hat = successes / n
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2.0 * n)) / denom
    margin = (
        z * math.sqrt((p_hat * (1.0 - p_hat) + z * z / (4.0 * n)) / n) / denom
    )
    return round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)


# ---------------------------------------------------------------------------
# Additional metric SQL queries
# ---------------------------------------------------------------------------

def query_rec_avg_rating(db: Session, since: datetime) -> dict[str, float]:
    """Average rating for movies accessed from recommendation sections."""
    rows = db.execute(text("""
        SELECT
            COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
            AVG((metadata->>'rating')::float) AS avg_rating
        FROM user_events
        WHERE created_at >= :since
          AND event_type = 'rating'
          AND metadata->>'source_section' IS NOT NULL
          AND metadata->>'source_section' != 'direct'
        GROUP BY exp_group
    """), {"since": since}).fetchall()
    return {r[0]: round(r[1], 4) for r in rows if r[1] is not None}


def query_return_rate(db: Session, since: datetime) -> dict[str, float]:
    """Return rate: fraction of users with events on 2+ distinct days."""
    rows = db.execute(text("""
        SELECT exp_group,
               COUNT(*) FILTER (WHERE active_days >= 2)::float
               / NULLIF(COUNT(*), 0) AS return_rate
        FROM (
            SELECT
                COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
                user_id,
                COUNT(DISTINCT DATE(created_at)) AS active_days
            FROM user_events
            WHERE created_at >= :since AND user_id IS NOT NULL
            GROUP BY exp_group, user_id
        ) sub
        GROUP BY exp_group
    """), {"since": since}).fetchall()
    return {r[0]: round(r[1], 4) if r[1] else 0.0 for r in rows}


def query_avg_session_events(db: Session, since: datetime) -> dict[str, float]:
    """Average number of events per session per group."""
    rows = db.execute(text("""
        SELECT exp_group, AVG(event_count) AS avg_events
        FROM (
            SELECT
                COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
                session_id,
                COUNT(*) AS event_count
            FROM user_events
            WHERE created_at >= :since AND session_id IS NOT NULL
            GROUP BY exp_group, session_id
        ) sub
        GROUP BY exp_group
    """), {"since": since}).fetchall()
    return {r[0]: round(r[1], 2) for r in rows if r[1] is not None}


def query_daily_active_users(db: Session, since: datetime) -> dict[str, dict[str, int]]:
    """Daily unique active users per group."""
    rows = db.execute(text("""
        SELECT
            COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
            DATE(created_at)::text AS day,
            COUNT(DISTINCT user_id) AS unique_users
        FROM user_events
        WHERE created_at >= :since AND user_id IS NOT NULL
        GROUP BY exp_group, day
        ORDER BY exp_group, day
    """), {"since": since}).fetchall()

    result: dict[str, dict[str, int]] = {}
    for exp_group, day, count in rows:
        if exp_group not in result:
            result[exp_group] = {}
        result[exp_group][day] = count
    return result
