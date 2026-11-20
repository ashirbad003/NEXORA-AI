import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.config import settings
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from backend.app.schemas.auth import UserRole
from ai_engine.providers.factory import get_ai_provider

class TestPhase1BackendFoundation(unittest.TestCase):
    def test_settings_loaded(self):
        self.assertEqual(settings.APP_NAME, "NEXORA AI")
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertTrue(len(settings.ALLOWED_ORIGINS) > 0)

    def test_argon2id_password_hashing(self):
        pwd = "SecureStudentPassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_access_token_creation_and_decoding(self):
        token = create_access_token("student_uuid_001", UserRole.STUDENT)
        payload = decode_token(token)
        self.assertEqual(payload.sub, "student_uuid_001")
        self.assertEqual(payload.role, UserRole.STUDENT)
        self.assertEqual(payload.type, "access")

    def test_jwt_refresh_token_creation_and_decoding(self):
        token = create_refresh_token("student_uuid_001", UserRole.STUDENT)
        payload = decode_token(token)
        self.assertEqual(payload.sub, "student_uuid_001")
        self.assertEqual(payload.role, UserRole.STUDENT)
        self.assertEqual(payload.type, "refresh")

    def test_ai_provider_abstraction_local(self):
        import asyncio
        provider = get_ai_provider("local")
        self.assertEqual(provider.get_provider_name(), "local_deterministic_fallback")
        
        async def run_prompt():
            return await provider.generate_response("Explain binary search")
            
        res = asyncio.run(run_prompt())
        self.assertTrue(res.is_fallback)
        self.assertIn("NEXORA", res.content)

if __name__ == "__main__":
    unittest.main()
