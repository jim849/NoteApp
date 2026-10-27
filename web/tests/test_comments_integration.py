"""Run with RUN_DB_TESTS=1; all writes use a temporary, isolated Postgres schema."""
import base64
import hashlib
import hmac
import os
import unittest
import uuid
from unittest.mock import patch

from comment_crypto import PREFIX, CommentDecryptionError
from migrate_comments import migrate_comments


@unittest.skipUnless(os.environ.get("RUN_DB_TESTS") == "1", "Set RUN_DB_TESTS=1 for PostgreSQL tests")
class CommentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app as application
        from psycopg2 import sql

        cls.application = application
        cls.original_get_db = staticmethod(application.get_db)
        cls.schema = "test_comments_" + uuid.uuid4().hex
        conn = application.get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        finally:
            conn.close()
        cls.addClassCleanup(cls.cleanup_schema)
        cls.db_patch = patch.object(application, "get_db", side_effect=cls.connect)
        cls.db_patch.start()
        cls.addClassCleanup(cls.db_patch.stop)
        conn = cls.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT, password TEXT, role TEXT);
                    CREATE TABLE classes (id SERIAL PRIMARY KEY, name TEXT, teacher_id INTEGER);
                    CREATE TABLE notes (id SERIAL PRIMARY KEY, student_id INTEGER, class_id INTEGER,
                                        grade NUMERIC(4,1), comment TEXT);
                    INSERT INTO users VALUES (1, 'alice', 'alicepw', 'student'),
                                             (2, 'prof.turing', 'teach123', 'teacher');
                    INSERT INTO classes VALUES (1, 'Mathematics', 2);
                """)
        finally:
            conn.close()

    @classmethod
    def connect(cls):
        import psycopg2
        import psycopg2.extras

        config = cls.application
        conn = psycopg2.connect(host=config.DB_HOST, dbname=config.DB_NAME,
                                user=config.DB_USER, password=config.DB_PASSWORD,
                                options=f"-c search_path={cls.schema}",
                                cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = True
        return conn

    @classmethod
    def cleanup_schema(cls):
        from psycopg2 import sql

        conn = cls.original_get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))
        finally:
            conn.close()

    def setUp(self):
        self.cipher = self.application.comment_cipher
        self.conn = self.connect()
        self.addCleanup(self.conn.close)
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE notes RESTART IDENTITY")
            cur.execute("INSERT INTO notes (student_id, class_id, grade, comment) VALUES (1, 1, 16.2, %s)",
                        ("原始评语: Good work",))
        self.assertEqual(migrate_comments(self.conn, self.cipher), 1)
        self.conn.autocommit = True
        self.client = self.application.app.test_client()

    def sign_in(self, role):
        with self.client.session_transaction() as session:
            session["user_id"] = 1 if role == "student" else 2
            session["username"] = "alice" if role == "student" else "prof.turing"
            session["role"] = role

    def stored(self, note_id=1):
        with self.conn.cursor() as cur:
            cur.execute("SELECT comment FROM notes WHERE id=%s", (note_id,))
            return cur.fetchone()["comment"]

    def test_migration_encrypts_existing_data_and_is_idempotent(self):
        stored = self.stored()
        self.assertTrue(stored.startswith(PREFIX))
        self.assertEqual(self.cipher.decrypt(stored), "原始评语: Good work")
        self.assertEqual(migrate_comments(self.conn, self.cipher), 0)
        self.assertEqual(self.stored(), stored)

    def test_migration_preserves_null_and_encrypts_empty_strings(self):
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO notes (comment) VALUES (NULL), ('')")
        self.assertEqual(migrate_comments(self.conn, self.cipher), 1)
        self.assertIsNone(self.stored(2))
        self.assertEqual(self.cipher.decrypt(self.stored(3)), "")

    def test_migration_rolls_back_on_corrupt_or_unknown_ciphertext(self):
        for invalid in (PREFIX + "bad!", "aesgcm:v2:AAAA"):
            with self.subTest(invalid=invalid):
                self.conn.rollback()
                self.conn.autocommit = True
                with self.conn.cursor() as cur:
                    cur.execute("UPDATE notes SET comment='legacy' WHERE id=1")
                    cur.execute("DELETE FROM notes WHERE id<>1")
                    cur.execute("INSERT INTO notes (comment) VALUES (%s)", (invalid,))
                with self.assertRaises(CommentDecryptionError):
                    migrate_comments(self.conn, self.cipher)
                self.assertEqual(self.stored(), "legacy")

    def test_migration_rejects_wrong_key_without_changing_existing_data(self):
        from comment_crypto import CommentCipher
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        before = self.stored()
        with self.assertRaises(CommentDecryptionError):
            migrate_comments(self.conn, CommentCipher(AESGCM.generate_key(bit_length=256).hex()))
        self.assertEqual(self.stored(), before)

    def test_student_dashboard_and_api_decrypt_comments(self):
        self.sign_in("student")
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("原始评语: Good work", response.get_data(as_text=True))
        response = self.client.get("/api/notes/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["comment"], "原始评语: Good work")
        self.assertEqual(response.json["grade"], 16.2)

    def test_teacher_page_and_signed_csv_decrypt_comments(self):
        self.sign_in("teacher")
        response = self.client.get("/teacher")
        self.assertEqual(response.status_code, 200)
        self.assertIn("原始评语: Good work", response.get_data(as_text=True))
        for url in ("/export.csv", "/export.csv?class_id=1"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("原始评语: Good work", response.get_data(as_text=True))
                self.assertNotIn(PREFIX, response.get_data(as_text=True))
                content, tag = response.data.rsplit(b"# HMAC: ", 1)
                expected = hmac.new(os.environ["EXPORT_HMAC_KEY"].encode(), content, hashlib.sha256).hexdigest()
                self.assertEqual(tag.strip().decode(), expected)

    def test_create_and_update_encrypt_including_empty_comment_and_new_nonces(self):
        self.sign_in("teacher")
        for comment in ("新增中文评语 😀", "", "aesgcm:v1:this is user text"):
            with self.subTest(comment=comment):
                response = self.client.post("/grades", data={"student_id": "1", "class_id": "1",
                                                           "grade": "15", "comment": comment})
                self.assertEqual(response.status_code, 302)
                with self.conn.cursor() as cur:
                    cur.execute("SELECT id, comment FROM notes ORDER BY id DESC LIMIT 1")
                    row = cur.fetchone()
                self.assertEqual(self.cipher.decrypt(row["comment"]), comment)
                self.assertNotEqual(row["comment"], comment)
                before = row["comment"]
                response = self.client.post("/grades", data={"note_id": row["id"], "grade": "16",
                                                           "comment": comment})
                self.assertEqual(response.status_code, 302)
                after = self.stored(row["id"])
                self.assertNotEqual(before, after)
                self.assertEqual(self.cipher.decrypt(after), comment)

    def test_tampered_comments_fail_closed_on_every_read_path(self):
        payload = bytearray(base64.b64decode(self.stored()[len(PREFIX):]))
        payload[-1] ^= 1
        tampered = PREFIX + base64.b64encode(payload).decode()
        with self.conn.cursor() as cur:
            cur.execute("UPDATE notes SET comment=%s WHERE id=1", (tampered,))
        for role, urls in (("student", ("/dashboard", "/api/notes/1")),
                           ("teacher", ("/teacher", "/export.csv", "/export.csv?class_id=1"))):
            self.sign_in(role)
            for url in urls:
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 500)
                    self.assertEqual(response.json, {"error": "Unable to decrypt comment."})
                    self.assertNotIn(tampered, response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
