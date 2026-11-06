"""Aggregated profile/discover overview response schema (BE-07)."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.vocabulary import VocabularyStatsResponse


class OverviewUser(BaseModel):
    id: str
    name: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None


class OverviewStreak(BaseModel):
    current: int
    longest: int
    last_active_date: date | None = None


class OverviewLearning(BaseModel):
    days_studied: int
    total_minutes: int
    estimated_level: str | None = None


class OverviewDaily(BaseModel):
    date: str
    minutes: int
    active: bool


class OverviewWeek(BaseModel):
    start_date: str
    minutes: int
    days_active: int
    daily: list[OverviewDaily]


class OverviewVideos(BaseModel):
    started: int
    completed: int


class OverviewExams(BaseModel):
    attempts: int
    month_completed: int
    avg_score: float | None = None
    answered: int
    correct: int
    last_submitted_at: datetime | None = None


class OverviewLibrary(BaseModel):
    favorite_videos: int
    favorite_sentences: int
    notes: int


class OverviewResponse(BaseModel):
    user: OverviewUser
    streak: OverviewStreak
    learning: OverviewLearning
    this_week: OverviewWeek
    words: VocabularyStatsResponse
    videos: OverviewVideos
    exams: OverviewExams
    library: OverviewLibrary
