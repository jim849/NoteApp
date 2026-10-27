"""Encrypt legacy comments in one transaction before serving requests."""
def migrate_comments(conn, cipher):
    """Use an idle connection; rollback everything if any stored ciphertext is invalid."""
    conn.autocommit = False
    migrated = 0
    with conn:
        with conn.cursor() as cur:
            # Serialize migrations and prevent writes while the snapshot is encrypted.
            cur.execute("LOCK TABLE notes IN SHARE ROW EXCLUSIVE MODE")
            cur.execute("SELECT id, comment FROM notes WHERE comment IS NOT NULL ORDER BY id")
            for row in cur.fetchall():
                stored = row["comment"]
                if stored.startswith("aesgcm:"):
                    # Validate the key and tag even on repeat runs; never double encrypt.
                    cipher.decrypt(stored)
                    continue
                cur.execute(
                    "UPDATE notes SET comment = %s WHERE id = %s",
                    (cipher.encrypt(stored), row["id"]),
                )
                migrated += 1
    return migrated


def main():
    from app import comment_cipher, get_db

    conn = get_db()
    try:
        count = migrate_comments(conn, comment_cipher)
    finally:
        conn.close()
    print(f"Comment migration complete: {count} encrypted; existing ciphertext verified.")


if __name__ == "__main__":
    main()
