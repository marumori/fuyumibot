import socket
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests.ui.make_fixture import make

pytestmark = pytest.mark.ui
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    out = tmp_path_factory.mktemp("ui") / "site"
    make(out)

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(out)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_browser_checks(server):
    r = subprocess.run(["node", str(ROOT / "tests/ui/run.mjs"), server], capture_output=True, text=True, timeout=600)
    print(r.stdout[-6000:], r.stderr[-2000:])
    assert r.returncode == 0, r.stdout[-6000:] + r.stderr[-2000:]
