from pipeline.merge import clip_id
from pipeline.model import Appearance, Clip, Source


def mk(date, songs=(), program=None, performers=("坂本冬美",), yt=True, n="", date_source="title", hidden=False):
    srcs = [Source("youtube", f"yt{date}{n}{''.join(songs)}", "u")] if yt else [Source("x", f"x{date}{n}", "u")]
    c = Clip(id="", broadcast_date=date, date_source=date_source, program=program, songs=list(songs),
             performers=list(performers), title_raw=f"{date}{n}{songs}", sources=srcs, hidden=hidden)
    c.id = clip_id(c)
    return c


def app(date, program, broadcaster="BS朝日", note="", time="19:00〜20:54", kind="TV"):
    return Appearance(date, time, broadcaster, program, kind, note)
