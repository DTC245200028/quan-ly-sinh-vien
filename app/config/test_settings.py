"""SQLite is only for local checks; Compose always uses config.settings/MySQL."""
import os


os.environ.setdefault("DJANGO_SECRET_KEY", "local-tests-only-not-a-deployment-secret")
os.environ.setdefault("MYSQL_DATABASE", "unused_for_sqlite_tests")
os.environ.setdefault("MYSQL_USER", "unused_for_sqlite_tests")
os.environ.setdefault("MYSQL_PASSWORD", "unused_for_sqlite_tests")

from .settings import *  # noqa: E402,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
