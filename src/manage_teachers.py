import argparse
import getpass
import json
import os
import tempfile

from .teacher_auth import TEACHERS_FILE, create_password_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a teacher login account.")
    parser.add_argument("username", help="Teacher username")
    args = parser.parse_args()

    password = getpass.getpass("Teacher password (minimum 12 characters): ")
    if len(password) < 12:
        parser.error("Teacher passwords must be at least 12 characters.")
    if password != getpass.getpass("Confirm teacher password: "):
        parser.error("Passwords do not match.")

    try:
        teachers = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))["teachers"]
    except FileNotFoundError:
        teachers = {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SystemExit(f"Could not read {TEACHERS_FILE}: {error}") from error

    if not isinstance(teachers, dict):
        raise SystemExit(f"{TEACHERS_FILE} must contain a teachers object.")
    if args.username in teachers:
        raise SystemExit(f"Teacher account {args.username!r} already exists.")

    teachers[args.username] = create_password_record(password)
    TEACHERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        dir=TEACHERS_FILE.parent, prefix=".teachers-"
    )
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump({"teachers": teachers}, file, indent=2)
            file.write("\n")
        os.replace(temporary_path, TEACHERS_FILE)
        os.chmod(TEACHERS_FILE, 0o600)
    except OSError:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise

    print(f"Added teacher {args.username!r} to {TEACHERS_FILE}.")


if __name__ == "__main__":
    main()
