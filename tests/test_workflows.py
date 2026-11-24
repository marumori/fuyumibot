from pathlib import Path

import yaml


def wf(name):
    return yaml.safe_load(Path(f".github/workflows/{name}").read_text("utf-8"))


def on(w):
    return w.get("on", w.get(True))


def steps(w):
    return [s for job in w["jobs"].values() for s in job["steps"]]


def test_daily_schedule_and_timezone():
    w = wf("daily.yml")
    assert on(w)["schedule"][0]["cron"] == "0 20 * * *"
    assert "workflow_dispatch" in on(w)
    assert w["env"]["TZ"] == "Asia/Tokyo"


def test_daily_runs_tests_pipeline_commit_push():
    text = "\n".join(str(s.get("run", "")) + str(s.get("uses", "")) for s in steps(wf("daily.yml")))
    assert "pytest" in text and "python -m pipeline.run daily" in text
    assert "git diff --quiet" in text and "git push" in text
    assert "データ取得エラー" in text


def test_no_cloudflare_token_needed():
    # Cloudflare Pages is connected to the repo (Git integration) and deploys on every push.
    for name in ["daily.yml", "weekly.yml"]:
        text = Path(f".github/workflows/{name}").read_text("utf-8")
        assert "wrangler" not in text and "CF_API_TOKEN" not in text, name


def test_daily_passes_sheet_secrets():
    env = wf("daily.yml")["env"]
    for k in ["SHEET_ADD_CSV", "SHEET_PICK_CSV", "SHEET_REVIEW_CSV", "SITE_URL"]:
        assert k in env


def test_weekly_liveness():
    w = wf("weekly.yml")
    assert on(w)["schedule"][0]["cron"] == "0 21 * * 6"
    assert "python -m pipeline.run weekly" in "\n".join(str(s.get("run", "")) for s in steps(w))


def test_robots_disallow_all():
    assert Path("site/robots.txt").read_text() == "User-agent: *\nDisallow: /\n"


def test_setup_guide_japanese():
    t = Path("docs/setup.md").read_text("utf-8")
    for word in ["GitHub", "Cloudflare", "スプレッドシート", "YT_API_KEY", "非公開", "ビルドの出力ディレクトリ", "site"]:
        assert word in t
