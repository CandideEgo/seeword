"""Tests for admin subtitle editing endpoints (PATCH /videos/admin/{id}/subtitles)."""

from httpx import AsyncClient

from app.models.subtitle import Subtitle
from app.models.video import Video, VideoSource, VideoStatus
from tests.conftest import TestSessionLocal


async def _seed_video_with_subtitles() -> tuple[str, list[str]]:
    """Create a ready video with three subtitle rows; return (video_id, subtitle_ids)."""
    async with TestSessionLocal() as db:
        v = Video(
            title="Subtitle Edit Test",
            source_url="https://youtu.be/subedittest",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            is_official=True,
        )
        db.add(v)
        await db.flush()
        subs = [
            Subtitle(
                video_id=v.id, start_time=0.0, end_time=2.0, text_en="hello world", text_zh="你好世界", sentence_index=0
            ),
            Subtitle(
                video_id=v.id, start_time=2.0, end_time=4.0, text_en="running fast", text_zh="跑得快", sentence_index=1
            ),
            Subtitle(
                video_id=v.id, start_time=4.0, end_time=6.0, text_en="good morning", text_zh="早上好", sentence_index=2
            ),
        ]
        for s in subs:
            db.add(s)
        await db.commit()
        return v.id, [s.id for s in subs]


class TestSubtitleUpdateAuth:
    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=auth_headers,
            json={"text_zh": "x"},
        )
        assert resp.status_code == 403


class TestSubtitleUpdate:
    async def test_edit_text_zh(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"text_zh": "润色后的翻译"},
        )
        assert resp.status_code == 200
        assert resp.json()["text_zh"] == "润色后的翻译"
        # English untouched.
        assert resp.json()["text_en"] == "hello world"

    async def test_edit_text_en_recomputes_word_levels(self, client: AsyncClient, admin_headers: dict):
        """Editing the English text resets word_levels to the ECDICT baseline,
        overwriting any manual override on that line."""
        vid, sids = await _seed_video_with_subtitles()
        # Seed a bogus manual override that should be wiped by the recompute.
        async with TestSessionLocal() as db:
            sub = await db.get(Subtitle, sids[1])
            sub.word_levels = {"running": ["gre"]}  # bogus — run is cet4/cet6, not gre
            await db.commit()

        # Change the English text (different from original) to trigger recompute.
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[1]}",
            headers=admin_headers,
            json={"text_en": "walking slowly"},
        )
        assert resp.status_code == 200
        levels = resp.json()["word_levels"]
        # The bogus "running" override must be gone — recompute rebuilt word_levels
        # from the new text. With ECDICT present it'd carry "walking"'s levels; in CI
        # (no DB) it's None. Either way "running":["gre"] must no longer exist.
        assert not levels or levels.get("running") != ["gre"]

    async def test_edit_text_en_invalidates_word_timestamps(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        async with TestSessionLocal() as db:
            sub = await db.get(Subtitle, sids[0])
            sub.words = [{"word": "hello", "start": 0.0, "end": 0.8}, {"word": "world", "start": 1.0, "end": 1.8}]
            await db.commit()

        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"text_en": "greetings world"},
        )

        assert resp.status_code == 200
        assert resp.json()["words"] is None

    async def test_edit_timing(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        # [0.5, 1.5] stays within the original [0, 2] slot — no overlap with the
        # next subtitle (starts at 2.0), so the adjacency check passes.
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"start_time": 0.5, "end_time": 1.5},
        )
        assert resp.status_code == 200
        assert resp.json()["start_time"] == 0.5
        assert resp.json()["end_time"] == 1.5

    async def test_invalid_timing_rejected(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"start_time": 5.0, "end_time": 1.0},  # start >= end
        )
        assert resp.status_code == 422

    async def test_overlap_with_next_rejected(self, client: AsyncClient, admin_headers: dict):
        """Editing a subtitle's end_time into the next subtitle's slot is an
        overlap and must be rejected (400) — the service-level adjacency check."""
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"start_time": 0.0, "end_time": 2.5},  # next starts at 2.0 → overlap
        )
        assert resp.status_code == 400

    async def test_empty_text_rejected(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"text_en": "   "},
        )
        assert resp.status_code == 422

    async def test_nonexistent_subtitle_404(self, client: AsyncClient, admin_headers: dict):
        vid, _ = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/nope",
            headers=admin_headers,
            json={"text_zh": "x"},
        )
        assert resp.status_code == 404

    async def test_cross_video_edit_400(self, client: AsyncClient, admin_headers: dict):
        """A subtitle id belonging to another video must be rejected (400, not silently edited)."""
        _, sids_a = await _seed_video_with_subtitles()
        vid_b, _ = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid_b}/subtitles/{sids_a[0]}",  # sub of A, path says B
            headers=admin_headers,
            json={"text_zh": "x"},
        )
        assert resp.status_code == 400


class TestSubtitleBatchUpdate:
    async def test_batch_edits_multiple(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles",
            headers=admin_headers,
            json={
                "updates": [
                    {"id": sids[0], "text_zh": "翻译一"},
                    {"id": sids[2], "text_zh": "翻译三"},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        zh_by_id = {item["id"]: item["text_zh"] for item in data}
        assert zh_by_id[sids[0]] == "翻译一"
        assert zh_by_id[sids[2]] == "翻译三"

    async def test_batch_edit_text_en_invalidates_word_timestamps(self, client: AsyncClient, admin_headers: dict):
        vid, sids = await _seed_video_with_subtitles()
        async with TestSessionLocal() as db:
            sub = await db.get(Subtitle, sids[0])
            sub.words = [{"word": "hello", "start": 0.0, "end": 0.8}, {"word": "world", "start": 1.0, "end": 1.8}]
            await db.commit()

        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles",
            headers=admin_headers,
            json={"updates": [{"id": sids[0], "text_en": "greetings world"}]},
        )

        assert resp.status_code == 200
        assert resp.json()[0]["words"] is None

    async def test_batch_rejects_cross_video(self, client: AsyncClient, admin_headers: dict):
        vid_a, sids_a = await _seed_video_with_subtitles()
        _, sids_b = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid_a}/subtitles",
            headers=admin_headers,
            json={"updates": [{"id": sids_a[0], "text_zh": "ok"}, {"id": sids_b[0], "text_zh": "bad"}]},
        )
        assert resp.status_code == 400

    async def test_empty_batch_returns_empty(self, client: AsyncClient, admin_headers: dict):
        vid, _ = await _seed_video_with_subtitles()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles",
            headers=admin_headers,
            json={"updates": []},
        )
        assert resp.status_code == 200
        assert resp.json() == []
