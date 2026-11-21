"""Exercise CSRF checks through the Flask app with isolated database and ping calls."""
import re
import unittest
from unittest.mock import Mock, patch

import app as application


class CsrfTests(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        database = patch.object(application, "get_db")
        ping = patch.object(application.subprocess, "run")
        self.database = database.start()
        self.ping = ping.start()
        self.addCleanup(database.stop)
        self.addCleanup(ping.stop)
        self.cursor = self.database.return_value.cursor.return_value
        self.cursor.fetchall.return_value = []

    def sign_in(self, role):
        with self.client.session_transaction() as session:
            session.update(user_id=1, username=role, role=role)

    def form_token(self, path, count):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        tokens = re.findall(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        self.assertEqual(len(tokens), count)
        self.assertEqual(len(set(tokens)), 1)
        return tokens[0]

    def test_invalid_tokens_are_rejected_before_side_effects(self):
        self.sign_in("admin")
        foreign_token = self.form_token("/admin", 2)
        self.client = application.app.test_client()
        self.sign_in("admin")
        self.form_token("/admin", 2)
        self.database.reset_mock()
        for path in ("/admin/users", "/admin/ping", "/grades"):
            if path == "/grades":
                self.sign_in("teacher")
            for fields in ({}, {"csrf_token": "invalid"}, {"csrf_token": "é"},
                           {"csrf_token": foreign_token}):
                with self.subTest(path=path, fields=fields):
                    response = self.client.post(path, data=fields)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(b"CSRF token missing or wrong", response.data)
        self.database.assert_not_called()
        self.ping.assert_not_called()
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], 1)

    def test_login_without_token_and_grade_request_without_session_token(self):
        self.cursor.fetchone.return_value = {
            "id": 1, "username": "teacher", "role": "teacher", "password": "$argon2-test",
        }
        with patch.object(application, "ph", Mock(verify=Mock(return_value=True))):
            response = self.client.post("/login", data={
                "username": "teacher", "password": "test-password",
            })
        self.assertEqual(response.status_code, 302)
        self.assertIn("SameSite=Lax", response.headers["Set-Cookie"])
        self.database.reset_mock()
        self.assertEqual(self.client.post("/grades", data={}).status_code, 400)
        self.database.assert_not_called()
        self.form_token("/teacher", 1)

    def test_teacher_can_create_and_update_grades_with_session_token(self):
        self.sign_in("teacher")
        token = self.form_token("/teacher", 1)
        self.cursor.reset_mock()
        fields = {"csrf_token": token, "student_id": "1", "class_id": "1", "grade": "15"}
        self.assertEqual(self.client.post("/grades", data=fields).status_code, 302)
        self.assertIn("INSERT INTO notes", self.cursor.execute.call_args.args[0])
        fields["note_id"] = "1"
        self.assertEqual(self.client.post("/grades", data=fields).status_code, 302)
        self.assertIn("UPDATE notes", self.cursor.execute.call_args.args[0])

    def test_admin_can_submit_protected_forms(self):
        self.sign_in("admin")
        self.cursor.fetchall.side_effect = [[{"id": 2, "username": "student", "role": "student"}], []]
        token = self.form_token("/admin", 3)
        self.cursor.fetchall.side_effect = None
        fields = {"csrf_token": token, "username": "new", "password": "test-password", "action": "create"}
        self.assertEqual(self.client.post("/admin/users", data=fields).status_code, 302)
        self.assertIn("INSERT INTO users", self.cursor.execute.call_args.args[0])
        fields = {"csrf_token": token, "user_id": "2", "action": "delete"}
        self.assertEqual(self.client.post("/admin/users", data=fields).status_code, 302)
        self.assertIn("DELETE FROM users", self.cursor.execute.call_args.args[0])
        self.ping.return_value.stdout = "ping result"
        self.ping.return_value.stderr = ""
        response = self.client.post("/admin/ping", data={"csrf_token": token, "host": "127.0.0.1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ping result", response.data)
        self.ping.assert_called_once()

    def test_valid_token_does_not_grant_teacher_access(self):
        self.sign_in("teacher")
        token = self.form_token("/teacher", 1)
        self.sign_in("student")
        self.database.reset_mock()
        response = self.client.post("/grades", data={"csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/login")
        self.database.assert_not_called()
