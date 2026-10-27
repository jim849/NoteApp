import base64
import os
import unittest
from unittest.mock import patch

from comment_crypto import AAD, NONCE_BYTES, PREFIX, CommentCipher, CommentDecryptionError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CommentCryptoTests(unittest.TestCase):
    def setUp(self):
        self.key = AESGCM.generate_key(bit_length=256)
        self.cipher = CommentCipher(self.key.hex())

    def test_round_trip_unicode_empty_null_and_long_comments(self):
        for text in (None, "", "Good work", "中文评语 é 😀\n第二行", "x" * 10000):
            with self.subTest(text_type=type(text).__name__, length=len(text or "")):
                encrypted = self.cipher.encrypt(text)
                self.assertEqual(self.cipher.decrypt(encrypted), text)
                if text is not None:
                    self.assertTrue(encrypted.startswith(PREFIX))
                    self.assertNotEqual(encrypted, text)

    def test_fresh_twelve_byte_nonce_for_each_encryption(self):
        encrypted = [self.cipher.encrypt("same comment") for _ in range(100)]
        nonces = {base64.b64decode(value[len(PREFIX):])[:NONCE_BYTES] for value in encrypted}
        self.assertEqual(len(nonces), 100)
        self.assertEqual({len(nonce) for nonce in nonces}, {12})

    def test_payload_is_interoperable_aes_gcm_with_full_tag(self):
        plaintext = "Independent decrypt"
        payload = base64.b64decode(self.cipher.encrypt(plaintext)[len(PREFIX):])
        self.assertEqual(len(payload), 12 + len(plaintext.encode()) + 16)
        self.assertEqual(AESGCM(self.key).decrypt(payload[:12], payload[12:], AAD).decode(), plaintext)

    def test_wrong_key_is_rejected(self):
        other = CommentCipher(AESGCM.generate_key(bit_length=256).hex())
        with self.assertRaises(CommentDecryptionError):
            other.decrypt(self.cipher.encrypt("private"))

    def test_nonce_ciphertext_and_tag_tampering_are_rejected(self):
        payload = base64.b64decode(self.cipher.encrypt("private comment")[len(PREFIX):])
        for position in (0, 12, len(payload) - 1):
            with self.subTest(position=position):
                changed = bytearray(payload)
                changed[position] ^= 1
                with self.assertRaises(CommentDecryptionError):
                    self.cipher.decrypt(PREFIX + base64.b64encode(changed).decode())

    def test_plaintext_unknown_version_invalid_base64_and_truncation_are_rejected(self):
        for stored in ("plaintext", "", "aesgcm:v2:AAAA", PREFIX + "!", PREFIX + "AAAA", PREFIX):
            with self.subTest(stored=stored):
                with self.assertRaises(CommentDecryptionError):
                    self.cipher.decrypt(stored)

    def test_missing_or_invalid_configuration_is_rejected(self):
        for value in (None, "", "0" * 32, "g" * 64, "00 " * 32):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    CommentCipher(value)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "COMMENT_ENCRYPTION_KEY"):
                CommentCipher.from_env()


if __name__ == "__main__":
    unittest.main()
