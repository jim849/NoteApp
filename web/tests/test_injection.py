"""Dependency-free checks of the real route bodies with isolated collaborators.

Run: python3 -m unittest discover -s web/tests -p test_injection.py -v
These checks do not replace HTTP tests against PostgreSQL and container ping.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


def route(name, **namespace):
    source = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(source.read_text())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == name)
    function.decorator_list = []
    module = ast.Module(body=[function], type_ignores=[])
    exec(compile(module, str(source), "exec"), namespace)
    return namespace[name]


class InjectionTests(unittest.TestCase):
    def login(self, username, password, candidate):
        database = Mock()
        cursor = database.cursor.return_value
        cursor.fetchone.return_value = candidate
        session = {}
        hasher = Mock()
        hasher.verify.return_value = True
        render = Mock(return_value="login page")
        response = route(
            "login", request=SimpleNamespace(method="POST", form={
                "username": username, "password": password}),
            get_db=Mock(return_value=database), session=session, ph=hasher,
            VerificationError=ValueError, render_template=render,
            make_jwt=Mock(return_value="test-token"), log=Mock(),
            redirect=lambda target: target, url_for=lambda name: name,
        )()
        return response, session, cursor, database, hasher, render

    def test_sql_payload_is_separate_data_and_creates_no_session(self):
        for password in ("", "anything"):
            with self.subTest(password=password):
                response, session, cursor, db, _, render = self.login(
                    "admin' -- ", password, None)
                query, params = cursor.execute.call_args.args
                self.assertEqual(params, ("admin' -- ",))
                self.assertNotIn("admin' --", query)
                self.assertIn("WHERE username = %s", query)
                self.assertEqual(session, {})
                self.assertEqual(response, "login page")
                self.assertEqual(render.call_args.kwargs["error"], "Invalid credentials.")
                db.close.assert_called_once()

    def test_real_login_uses_argon2_and_sets_identity(self):
        response, session, _, _, hasher, _ = self.login("alice", "alicepw", {
            "id": 6, "username": "alice", "password": "$argon2-test",
            "role": "student"})
        hasher.verify.assert_called_once_with("$argon2-test", "alicepw")
        self.assertEqual(response, "index")
        self.assertEqual(session["username"], "alice")
        self.assertEqual(session["role"], "student")

    def test_wrong_legacy_password_does_not_log_in(self):
        _, session, _, _, _, _ = self.login("admin", "wrong", {
            "id": 1, "username": "admin", "password": "admin123", "role": "admin"})
        self.assertEqual(session, {})

    def ping(self, host, authorized=True):
        run = Mock(return_value=SimpleNamespace(stdout="ping output", stderr=""))
        render = Mock(return_value="admin page")
        response = route(
            "admin_ping", request=SimpleNamespace(form={"host": host}),
            login_required=Mock(return_value=authorized),
            subprocess=SimpleNamespace(run=run), render_template=render,
            _all_users=lambda: [], _all_classes=lambda: [], log=Mock(),
            redirect=lambda target: target, url_for=lambda name: name,
        )()
        return response, run, render

    def test_command_payloads_remain_one_argument_without_a_shell(self):
        for host in ("127.0.0.1; id", "127.0.0.1; id; head -2 /etc/passwd",
                     "$(id)", "-V"):
            with self.subTest(host=host):
                _, run, _ = self.ping(host)
                run.assert_called_once_with(
                    ["ping", "-c", "1", "--", host],
                    capture_output=True, text=True, timeout=10)

    def test_plain_host_and_output_are_preserved(self):
        _, run, render = self.ping("127.0.0.1")
        self.assertEqual(run.call_args.args[0][-1], "127.0.0.1")
        self.assertEqual(render.call_args.kwargs["ping_result"], "ping output")

    def test_non_admin_cannot_start_a_process(self):
        response, run, render = self.ping("127.0.0.1; id", authorized=False)
        self.assertEqual(response, "login")
        run.assert_not_called()
        render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
