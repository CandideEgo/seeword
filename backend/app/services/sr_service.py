"""Spaced repetition interval calculators.

Two algorithms live side by side here:

1. ``calculate_review_interval`` (S6, DEC-057) — the product's review
   scheduling. Error counts decide the next interval directly; the band
   table lives in the constants below (round/hard/clean/error ladders and the
   wrong-count cap).
   Consumed by ``vocabulary_service.apply_review``, the single writer of a
   word's review state. ``ease_factor`` no longer participates in scheduling.

2. ``calculate_next_review`` — frozen SM-2. Kept verbatim only because the
   legacy practice-submit path (``practice_service.submit_practice_results``)
   still calls it; do not extend it or wire new paths to it.
"""

MIN_EASE_FACTOR = 1.3

# --- S6 (DEC-057): error-count banded intervals -----------------------------
# 本轮内/复习时答错 → 次日。
ROUND_INTERVAL_DAYS = 1
# 三档自评里的「模糊」：记得但不牢，2 天后再来；不计入 wrong_count，
# 也不占用「不认识」的次日档，否则三档评分在调度上无法区分。
HARD_INTERVAL_DAYS = 2
# 全对且 wrong_count = 0 的间隔阶梯：3 → 7 → 16 → 35（35 天封顶）。
CLEAN_LADDER = (3, 7, 16, 35)
# 全对但 wrong_count ≥ 1 的间隔阶梯：2 → 5 → 12 → 25（比干净词短一档）。
ERROR_LADDER = (2, 5, 12, 25)
# wrong_count 达到该值后，间隔上限压到 WRONG_INTERVAL_CAP 天（老大难反复出现）。
WRONG_COUNT_CAP = 3
WRONG_INTERVAL_CAP = 7


def _next_ladder_step(ladder: tuple[int, ...], current_interval_days: int) -> int:
    """First rung strictly above the current interval; the top rung repeats."""
    for step in ladder:
        if step > current_interval_days:
            return step
    return ladder[-1]


def calculate_review_interval(
    *,
    correct: bool,
    wrong_count: int,
    interval_days: int,
    wrong_recent: bool,
    hard: bool = False,
) -> int:
    """Next review interval in days after one answer (S6, DEC-057).

    Parameters
    ----------
    correct : bool
        Whether the current answer was right (quality >= 3).
    wrong_count : int
        Cumulative wrong answers recorded *before* this answer.
    interval_days : int
        Interval currently stored on the word (0 for never-scheduled words).
    wrong_recent : bool
        Whether the word was answered wrong within the current learning
        round — approximated by the caller as "a wrong answer happened
        within the last 24h" (see ``vocabulary_service.WRONG_RECENT_WINDOW``).
    hard : bool
        The three-level self-rating's middle option ("模糊"): remembered, but
        not confidently. Schedules two days out without touching
        ``wrong_count``, so it stays distinct from both 认识 and 不认识.

    Returns
    -------
    int
        Interval in days until the next review.
    """
    # 答错（无论本轮内还是复习时）→ 回到次日；本轮内曾答错、其后答对的词也
    # 必须次日重现，wrong_recent 就是那个信号。
    if not correct or wrong_recent:
        return ROUND_INTERVAL_DAYS
    if hard:
        return HARD_INTERVAL_DAYS
    if wrong_count >= WRONG_COUNT_CAP:
        return min(_next_ladder_step(ERROR_LADDER, interval_days), WRONG_INTERVAL_CAP)
    if wrong_count >= 1:
        return _next_ladder_step(ERROR_LADDER, interval_days)
    return _next_ladder_step(CLEAN_LADDER, interval_days)


def calculate_next_review(
    quality: int,
    review_count: int,
    ease_factor: float = 2.5,
    interval_days: int = 0,
) -> tuple[int, float, int]:
    """Calculate the next review interval using SM-2 (frozen legacy path).

    Only ``practice_service.submit_practice_results`` still uses this. The
    product's scheduling went through ``calculate_review_interval`` (DEC-057);
    this function must not drift while that legacy caller exists.

    Parameters
    ----------
    quality : int
        User's recall quality (0-5).
    review_count : int
        Number of times the item has been reviewed.
    ease_factor : float
        Current ease factor (default 2.5 for new items).
    interval_days : int
        Current interval between reviews in days.

    Returns
    -------
    tuple[int, float, int]
        (next_interval_days, new_ease_factor, new_review_count)
    """
    if not 0 <= quality <= 5:
        raise ValueError("Quality must be between 0 and 5")

    # Update ease factor
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ef < MIN_EASE_FACTOR:
        new_ef = MIN_EASE_FACTOR

    # If quality < 3, reset to the beginning
    if quality < 3:
        new_review_count = 0
        new_interval = 1
    else:
        new_review_count = review_count + 1
        if new_review_count == 1:
            new_interval = 1
        elif new_review_count == 2:
            new_interval = 6
        else:
            new_interval = round(interval_days * new_ef)

    return new_interval, new_ef, new_review_count
