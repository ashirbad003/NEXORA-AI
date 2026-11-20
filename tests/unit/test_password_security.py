import unittest
import os
import sys

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.security import (
    hash_password,
    verify_password,
    check_needs_rehash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from backend.app.schemas.auth import UserRole

class TestArgon2idPasswordSecurity(unittest.TestCase):
    def test_argon2id_hashing_and_verification(self):
        password = "SecureCandidatePassword#2026!"
        hashed = hash_password(password)
        
        # Verify hash begins with Argon2id signature
        self.assertTrue(hashed.startswith("$argon2id$"), f"Expected $argon2id$ header, got: {hashed[:15]}")
        
        # Verify valid password succeeds
        self.assertTrue(verify_password(password, hashed))
        
        # Verify incorrect password fails
        self.assertFalse(verify_password("IncorrectPassword#2026!", hashed))

    def test_empty_password_rejection(self):
        with self.assertRaises(ValueError):
            hash_password("")

    def test_malformed_hash_handling(self):
        # Must return False safely and not raise unhandled exception
        self.assertFalse(verify_password("any_pwd", "malformed_hash_string"))
        self.assertFalse(verify_password("any_pwd", "$argon2id$v=19$invalid$corrupted$hash"))
        self.assertFalse(verify_password("any_pwd", ""))

    def test_constant_time_different_length_inputs(self):
        hashed = hash_password("short")
        self.assertFalse(verify_password("a" * 1000, hashed))
        self.assertFalse(verify_password("", hashed))

    def test_salt_uniqueness(self):
        pwd = "SamePassword123"
        h1 = hash_password(pwd)
        h2 = hash_password(pwd)
        self.assertNotEqual(h1, h2, "Argon2id hashes for identical passwords must have unique salts.")

    def test_rehash_check(self):
        pwd = "TestRehashPassword"
        hashed = hash_password(pwd)
        self.assertFalse(check_needs_rehash(hashed))

if __name__ == "__main__":
    unittest.main()
