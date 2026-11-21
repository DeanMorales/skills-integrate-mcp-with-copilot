import hashlib
import json
import secrets
from pathlib import Path
from typing import Any


TEACHERS_FILE = Path(__file__).with_name("teachers.json")
PASSWORD_HASH_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_BYTES = 32


class TeacherConfigurationError(Exception):
    """Raised when the teacher credential store is missing or invalid."""


def create_password_record(password: str) -> dict[str, str]:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return {"salt": salt.hex(), "password_hash": digest.hex()}


def _read_teachers(path: Path) -> dict[str, Any]:
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise TeacherConfigurationError(
            "Teacher login is not configured. Create src/teachers.json with "
            "the teacher account setup instructions."
        ) from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TeacherConfigurationError(
            "The teacher credential file could not be read."
        ) from error

    if not isinstance(store, dict) or not isinstance(store.get("teachers"), dict):
        raise TeacherConfigurationError(
            "The teacher credential file must contain a teachers object."
        )
    return store["teachers"]


def authenticate_teacher(
    username: str,
    password: str,
    path: Path = TEACHERS_FILE,
) -> bool:
    teachers = _read_teachers(path)
    record = teachers.get(username)

    if record is None:
        salt = bytes(PASSWORD_SALT_BYTES)
        expected_digest = bytes(PASSWORD_HASH_BYTES)
    else:
        if not isinstance(record, dict):
            raise TeacherConfigurationError(
                f"Teacher credential record for {username!r} is invalid."
            )
        try:
            salt = bytes.fromhex(record["salt"])
            expected_digest = bytes.fromhex(record["password_hash"])
        except (KeyError, TypeError, ValueError) as error:
            raise TeacherConfigurationError(
                f"Teacher credential record for {username!r} is invalid."
            ) from error
        if len(salt) != PASSWORD_SALT_BYTES or len(expected_digest) != PASSWORD_HASH_BYTES:
            raise TeacherConfigurationError(
                f"Teacher credential record for {username!r} is invalid."
            )

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    is_valid = secrets.compare_digest(candidate_digest, expected_digest)
    return record is not None and is_valid
