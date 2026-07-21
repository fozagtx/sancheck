import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer


class MiddlewareHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"middleware test page"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class MiddlewareCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), MiddlewareHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:%d/page" % cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def run_gate(self, stdin_payload, *args):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "seccheck",
                "middleware",
                "--no-threat-intel",
                "--no-domain-age",
                *args,
            ],
            input=stdin_payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_middleware_allows_json_payload_when_policy_passes(self):
        result = self.run_gate(json.dumps({"messages": [{"content": "open %s" % self.url}]}), "--allow-private")
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["allowed"])
        self.assertEqual(payload["decision"], "allow")
        self.assertEqual(payload["mode"], "middleware")
        self.assertEqual(payload["url_count"], 1)

    def test_middleware_blocks_private_url_by_default(self):
        result = self.run_gate("open %s" % self.url)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertFalse(payload["allowed"])
        self.assertEqual(payload["decision"], "block")
        self.assertEqual(payload["blocked_urls"], [self.url])


if __name__ == "__main__":
    unittest.main()
