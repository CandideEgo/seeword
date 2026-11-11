"""Compare the shipped S6 scheduler with the Py-FSRS 6.3.2 candidate.

Run in a scratch environment that has ``fsrs==6.3.2`` plus this repository's
backend dependencies. It reads nothing but the public scheduling function, so it
can run against a checkout without a database:

    python -m venv fsrsvenv && fsrsvenv/Scripts/pip install fsrs==6.3.2 "sqlalchemy[asyncio]"
    cd backend && PYTHONUTF8=1 ../fsrsvenv/Scripts/python fsrs_candidate_eval.py

Ratings: S6 uses 0-5 self-assessment; the candidate maps 0-2 -> Again, 3 -> Hard,
4-5 -> Good. Easy is reserved for a future explicit "轻松记住" rating, as the
roadmap says.
"""

import sys
from datetime import UTC, datetime, timedelta

sys.path.insert(0, ".")
from app.services.sr_service import calculate_review_interval  # noqa: E402
from fsrs import Card, Rating, Scheduler  # noqa: E402


def map_quality(quality: int) -> Rating:
    if quality <= 2:
        return Rating.Again
    if quality == 3:
        return Rating.Hard
    return Rating.Good


def s6_intervals(qualities):
    """Replay S6 through the same helper ``apply_review`` calls."""

    class Word:
        review_count = 0
        correct_count = 0
        wrong_count = 0
        interval_days = 0
        last_wrong_at = None

    word = Word()
    intervals = []
    now = datetime(2026, 1, 1, tzinfo=UTC)
    for quality in qualities:
        correct = quality >= 3
        wrong_recent = word.last_wrong_at is not None and now - word.last_wrong_at < timedelta(hours=24)
        interval = calculate_review_interval(
            correct=correct,
            wrong_count=word.wrong_count,
            interval_days=word.interval_days,
            wrong_recent=wrong_recent,
            hard=quality == 3,
        )
        word.review_count += 1
        word.interval_days = interval
        if correct:
            word.correct_count += 1
        else:
            word.wrong_count += 1
            word.last_wrong_at = now
        intervals.append(interval)
        now += timedelta(days=interval)
    return intervals


def fsrs_intervals(qualities):
    scheduler = Scheduler(
        enable_fuzzing=False,
        learning_steps=(),
        relearning_steps=(),
        maximum_interval=36500,
    )
    card = Card()
    intervals = []
    now = datetime(2026, 1, 1, tzinfo=UTC)
    for quality in qualities:
        card, _ = scheduler.review_card(card, map_quality(quality), review_datetime=now)
        interval = max(1, round((card.due - now).total_seconds() / 86400))
        intervals.append(interval)
        now += timedelta(days=interval)
    return intervals


def replay_is_deterministic(qualities) -> bool:
    return fsrs_intervals(qualities) == fsrs_intervals(qualities)


SEQUENCES = {
    "five correct (5,5,5,5,5)": [5, 5, 5, 5, 5],
    "one wrong then correct (5,1,5,5,5)": [5, 1, 5, 5, 5],
    "all hard (3,3,3,3,3)": [3, 3, 3, 3, 3],
    "all wrong (2,2,2,2,2)": [2, 2, 2, 2, 2],
}

if __name__ == "__main__":
    for label, qualities in SEQUENCES.items():
        print(f"{label:<36} S6 {s6_intervals(qualities)}  FSRS {fsrs_intervals(qualities)}")
    print("candidate replays identically:", replay_is_deterministic(SEQUENCES["one wrong then correct (5,1,5,5,5)"]))
