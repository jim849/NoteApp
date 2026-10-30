"""Regression checks for Class 7 JWT verification; no database is required."""
import hashlib
import hmac
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import app as application


class JWTTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"user_id": 6, "username": "alice", "role": "student"}
        self.key_patch = patch.object(application, "JWT_SECRET", "isolated-test-key-" * 4)
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    def signed(self, header, payload=None, key=None, digest=hashlib.sha256):
        h = application._b64url(json.dumps(header).encode())
        p = application._b64url(json.dumps(self.payload if payload is None else payload).encode())
        message = f"{h}.{p}"
        signature = hmac.new((key or application.JWT_SECRET).encode(), message.encode(), digest).digest()
        return f"{message}.{application._b64url(signature)}"

    def test_genuine_token_works(self):
        self.assertEqual(application.verify_jwt(application.make_jwt(self.payload)), self.payload)

    def test_none_and_other_algorithms_are_rejected_even_with_matching_hmac(self):
        for algorithm in ("none", "None", "hs256", "HS384", "HS512", "RS256", "", None):
            with self.subTest(algorithm=algorithm):
                self.assertIsNone(application.verify_jwt(self.signed({"alg": algorithm})))
        self.assertIsNone(application.verify_jwt(self.signed({"typ": "JWT"})))
        self.assertIsNone(application.verify_jwt(self.signed({"alg": "none"}).rsplit(".", 1)[0] + "."))
        self.assertIsNone(application.verify_jwt(self.signed({"alg": "HS512"}, digest=hashlib.sha512)))

    def test_old_secret_forgery_is_rejected(self):
        teacher = dict(self.payload, role="teacher")
        self.assertIsNone(application.verify_jwt(self.signed({"alg": "HS256"}, teacher, key="s3cr3t")))

    def test_payload_tampering_and_missing_signature_are_rejected(self):
        token = application.make_jwt(self.payload)
        h, p, signature = token.split(".")
        teacher = application._b64url(json.dumps(dict(self.payload, role="teacher")).encode())
        self.assertIsNone(application.verify_jwt(f"{h}.{teacher}.{signature}"))
        self.assertIsNone(application.verify_jwt(f"{h}.{p}."))

    def test_malformed_tokens_and_non_object_json_are_rejected(self):
        for token in (None, 123, "", "a.b", "a.b.c.d", "!.!.!", "bm90LWpzb24.e30.x",
                      "e30.e30.中文", self.signed([]), self.signed(None),
                      self.signed({"alg": "HS256"}, payload=[]),
                      self.signed({"alg": "HS256"}, payload="alice")):
            with self.subTest(token=token):
                self.assertIsNone(application.verify_jwt(token))

    def test_rejected_bearer_without_cookies_returns_unauthorized(self):
        client = application.app.test_client(use_cookies=False)
        for token in (self.signed({"alg": "none"}).rsplit(".", 1)[0] + ".",
                      self.signed({"alg": "HS256"}, key="s3cr3t"), "a.b.c"):
            with self.subTest(token=token), patch.object(application, "get_db") as database:
                response = client.get("/api/notes/3", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json, {"error": "unauthorized"})
                database.assert_not_called()

    def test_startup_requires_a_secret(self):
        env = dict(os.environ)
        env.pop("JWT_SECRET", None)
        result = subprocess.run([sys.executable, "-c", "import app"], env=env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("JWT_SECRET", result.stderr)


if __name__ == "__main__":
    unittest.main()
