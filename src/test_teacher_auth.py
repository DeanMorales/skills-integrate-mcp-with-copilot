import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from src import manage_teachers
from src.app import app, require_teacher
from src.teacher_auth import (
    TeacherConfigurationError,
    authenticate_teacher,
    create_password_record,
)


class TeacherAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.credential_file = Path(self.temp_dir.name) / "teachers.json"
        self.credential_file.write_text(
            json.dumps(
                {
                    "teachers": {
                        "coach": create_password_record("correct-horse-battery")
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_authentication_accepts_valid_credentials_and_rejects_invalid_ones(self):
        self.assertTrue(
            authenticate_teacher(
                "coach", "correct-horse-battery", self.credential_file
            )
        )
        self.assertFalse(
            authenticate_teacher("coach", "wrong-password", self.credential_file)
        )
        self.assertFalse(
            authenticate_teacher(
                "unknown", "correct-horse-battery", self.credential_file
            )
        )

    def test_missing_credential_file_is_an_explicit_configuration_error(self):
        with self.assertRaises(TeacherConfigurationError):
            authenticate_teacher(
                "coach",
                "correct-horse-battery",
                self.credential_file.parent / "missing.json",
            )

    def test_account_helper_writes_a_hash_to_the_local_store(self):
        with (
            patch.object(manage_teachers, "TEACHERS_FILE", self.credential_file),
            patch.object(sys, "argv", ["manage_teachers", "new-teacher"]),
            patch.object(
                manage_teachers.getpass,
                "getpass",
                side_effect=["a-secure-test-password", "a-secure-test-password"],
            ),
        ):
            manage_teachers.main()

        store = json.loads(self.credential_file.read_text(encoding="utf-8"))
        record = store["teachers"]["new-teacher"]
        self.assertNotIn("password", record)
        self.assertTrue(
            authenticate_teacher(
                "new-teacher", "a-secure-test-password", self.credential_file
            )
        )

    def test_login_dependency_rejects_missing_or_invalid_credentials(self):
        with self.assertRaises(HTTPException) as missing:
            require_teacher(None)
        self.assertEqual(missing.exception.status_code, 401)

        credentials = HTTPBasicCredentials(username="coach", password="wrong-password")
        with patch("src.app.authenticate_teacher", return_value=False):
            with self.assertRaises(HTTPException) as invalid:
                require_teacher(credentials)
        self.assertEqual(invalid.exception.status_code, 401)

        with patch("src.app.authenticate_teacher", return_value=True):
            self.assertEqual(require_teacher(credentials), "coach")

    def test_roster_mutation_routes_require_teacher_authentication(self):
        protected_paths = {
            "/activities/{activity_name}/signup",
            "/activities/{activity_name}/unregister",
            "/auth/login",
        }
        protected_routes = [
            route for route in app.routes if getattr(route, "path", None) in protected_paths
        ]
        self.assertEqual({route.path for route in protected_routes}, protected_paths)
        for route in protected_routes:
            with self.subTest(path=route.path):
                self.assertTrue(
                    any(
                        dependency.call is require_teacher
                        for dependency in route.dependant.dependencies
                    )
                )


if __name__ == "__main__":
    unittest.main()
