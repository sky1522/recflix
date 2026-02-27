# ruff: noqa: T201
"""Team Draft Interleaving — 두 추천 리스트를 공정하게 섞어 비교."""
from __future__ import annotations

import math
import random


def team_draft_interleave(
    list_a: list[int],
    list_b: list[int],
    k: int = 20,
) -> tuple[list[int], set[int], set[int]]:
    """Team Draft Interleaving.

    Args:
        list_a: 모델 A의 movie_id 리스트 (순위순)
        list_b: 모델 B의 movie_id 리스트 (순위순)
        k: 최대 반환 수

    Returns:
        - interleaved: 섞인 리스트 (최대 k개)
        - team_a: 모델 A 소속 movie_id set
        - team_b: 모델 B 소속 movie_id set
    """
    interleaved: list[int] = []
    team_a: set[int] = set()
    team_b: set[int] = set()
    seen: set[int] = set()
    ptr_a = 0
    ptr_b = 0

    while len(interleaved) < k and (ptr_a < len(list_a) or ptr_b < len(list_b)):
        # 팀 크기가 작은 쪽 우선, 같으면 랜덤
        a_turn = len(team_a) < len(team_b) or (
            len(team_a) == len(team_b) and random.random() < 0.5
        )

        if a_turn:
            while ptr_a < len(list_a) and list_a[ptr_a] in seen:
                ptr_a += 1
            if ptr_a < len(list_a):
                mid = list_a[ptr_a]
                interleaved.append(mid)
                team_a.add(mid)
                seen.add(mid)
                ptr_a += 1
            else:
                # A 소진 → B에서 가져옴
                while ptr_b < len(list_b) and list_b[ptr_b] in seen:
                    ptr_b += 1
                if ptr_b < len(list_b):
                    mid = list_b[ptr_b]
                    interleaved.append(mid)
                    team_b.add(mid)
                    seen.add(mid)
                    ptr_b += 1
        else:
            while ptr_b < len(list_b) and list_b[ptr_b] in seen:
                ptr_b += 1
            if ptr_b < len(list_b):
                mid = list_b[ptr_b]
                interleaved.append(mid)
                team_b.add(mid)
                seen.add(mid)
                ptr_b += 1
            else:
                # B 소진 → A에서 가져옴
                while ptr_a < len(list_a) and list_a[ptr_a] in seen:
                    ptr_a += 1
                if ptr_a < len(list_a):
                    mid = list_a[ptr_a]
                    interleaved.append(mid)
                    team_a.add(mid)
                    seen.add(mid)
                    ptr_a += 1

    return interleaved, team_a, team_b


def compute_interleaving_result(
    team_a: set[int],
    team_b: set[int],
    clicked_ids: set[int],
) -> str:
    """클릭된 영화의 팀 귀속으로 승자 결정.

    Returns: "A", "B", or "tie"
    """
    score_a = len(clicked_ids & team_a)
    score_b = len(clicked_ids & team_b)
    if score_a > score_b:
        return "A"
    if score_b > score_a:
        return "B"
    return "tie"


def compute_win_rate(results: list[str]) -> dict:
    """세션별 승패 리스트 → 승률 + 95% CI (binomial).

    Returns:
        {a_wins, b_wins, ties, total, b_win_rate, ci_lower, ci_upper}
    """
    a_wins = results.count("A")
    b_wins = results.count("B")
    ties = results.count("tie")
    total = len(results)
    contested = a_wins + b_wins

    if contested == 0:
        return {
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
            "total": total,
            "b_win_rate": 0.5,
            "ci_lower": 0.0,
            "ci_upper": 1.0,
        }

    p = b_wins / contested
    # Wilson score interval
    z = 1.96
    n = contested
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    ci_lower = max(0.0, centre - margin)
    ci_upper = min(1.0, centre + margin)

    return {
        "a_wins": a_wins,
        "b_wins": b_wins,
        "ties": ties,
        "total": total,
        "b_win_rate": round(p, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
    }
