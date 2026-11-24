from pipeline.merge import clip_id, merge
from pipeline.model import Clip, Source


def clip(date, songs=(), program=None, performers=("坂本冬美",), title="t", sources=None):
    c = Clip(id="", broadcast_date=date, date_source="title", program=program, songs=list(songs),
             performers=list(performers), title_raw=title,
             sources=sources or [Source("x", title + date, "u", uploaded_at=f"{date}T10:00:00Z")])
    c.id = clip_id(c)
    return c


def test_clip_id_format():
    c = clip("2025-12-31", songs=["yozakura-oshichi"], title="夜桜お七 20251231")
    assert c.id.startswith("2025-12-31-yozakura-oshichi-") and len(c.id.split("-")[-1]) == 6
    assert clip("2025-12-31").id.startswith("2025-12-31-talk-")


def test_merge_never_on_empty_song():
    a = clip("2026-04-03", program="うたコン", title="a")
    b = clip("2026-04-03", program="うたコン", title="b")
    assert len(merge([a], [b])) == 2


def test_merge_same_song_needs_program_or_performer():
    a = clip("2025-01-01", songs=["iwaizake"], program="紅白", performers=["坂本冬美"], title="a")
    b = clip("2025-01-01", songs=["iwaizake"], program="うたコン", performers=["伍代夏子"], title="b")
    assert len(merge([a], [b])) == 2


def test_merge_same_song_same_performer_merges_sources():
    a = clip("2025-01-01", songs=["iwaizake"], title="a")
    b = clip("2025-01-01", songs=["iwaizake"], title="b",
             sources=[Source("bilibili", "BV1", "u")])
    out = merge([a], [b])
    assert len(out) == 1 and {s.platform for s in out[0].sources} == {"x", "bilibili"}


def test_same_source_id_updates_not_duplicates():
    a = clip("2025-01-01", songs=["iwaizake"], title="a")
    assert len(merge([a], [clip("2025-01-01", songs=["iwaizake"], title="a")])) == 1


def test_duplicate_x_posts_minutes_apart_collapse():
    t = "雪深深 藤あや子 20260120"
    a = clip("2026-01-20", songs=["yuki-shinshin"], performers=["藤あや子"], title=t,
             sources=[Source("x", "1", "u1", uploaded_at="2026-01-20T15:37:00Z")])
    b = clip("2026-01-20", songs=["yuki-shinshin"], performers=["藤あや子"], title=t,
             sources=[Source("x", "2", "u2", uploaded_at="2026-01-20T15:43:00Z")])
    out = merge([a], [b])
    assert len(out) == 1 and len(out[0].sources) == 2


def test_same_title_far_apart_talk_not_collapsed():
    t = "（無曲名） 藤あや子 20250112"
    a = clip("2025-01-12", title=t, sources=[Source("x", "1", "u", uploaded_at="2025-01-12T07:24:00Z")])
    b = clip("2025-01-12", title=t, sources=[Source("x", "2", "u", uploaded_at="2025-01-13T06:45:00Z")])
    assert len(merge([a], [b])) == 2
