"""Settings for the test suite (see pyproject.toml)."""

import os
import tempfile

_TEST_DATA_DIR = tempfile.mkdtemp(prefix="pidash-test-")

os.environ["PIDASH_SKIP_DOTENV"] = "1"
os.environ.setdefault("PIDASH_SECRET_KEY", "test-only-secret-key")
os.environ["PIDASH_DATA_DIR"] = _TEST_DATA_DIR
os.environ["PIDASH_SHARED_CONFIG_DIR"] = os.path.join(_TEST_DATA_DIR, "shared")

from config.settings import *  # noqa: E402, F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES = {  # noqa: F405 - the tests don't run collectstatic
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PIDASH_NTFY_URL = ""
