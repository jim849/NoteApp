"""AES-256-GCM storage for notes.comment (Session 03 homework)."""
import base64
import binascii
import os
import re

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


PREFIX = "aesgcm:v1:"
NONCE_BYTES = 12
TAG_BYTES = 16
AAD = b"notesapp:notes.comment:v1"


class CommentDecryptionError(ValueError):
    """Stored data is malformed or failed authentication; never return it as text."""


class CommentCipher:
    def __init__(self, key_hex):
        if not isinstance(key_hex, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", key_hex):
            raise ValueError(
                "COMMENT_ENCRYPTION_KEY must contain exactly 64 hexadecimal characters "
                "(32 random bytes). Generate once with: openssl rand -hex 32"
            )
        self._aes = AESGCM(bytes.fromhex(key_hex))

    @classmethod
    def from_env(cls):
        return cls(os.environ.get("COMMENT_ENCRYPTION_KEY"))

    def encrypt(self, plaintext):
        if plaintext is None:
            return None
        nonce = os.urandom(NONCE_BYTES)
        # AESGCM appends the full 16-byte authentication tag to the ciphertext.
        ciphertext = self._aes.encrypt(nonce, plaintext.encode("utf-8"), AAD)
        return PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, stored):
        if stored is None:
            return None
        if not stored.startswith(PREFIX):
            raise CommentDecryptionError("Comment is not in the supported encrypted format.")
        try:
            payload = base64.b64decode(stored[len(PREFIX):], validate=True)
            if len(payload) < NONCE_BYTES + TAG_BYTES:
                raise ValueError("Truncated encrypted comment.")
            plaintext = self._aes.decrypt(payload[:NONCE_BYTES], payload[NONCE_BYTES:], AAD)
            return plaintext.decode("utf-8")
        except (InvalidTag, ValueError, binascii.Error) as exc:
            raise CommentDecryptionError("Comment authentication failed.") from exc
