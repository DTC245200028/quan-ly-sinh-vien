#!/usr/bin/env python3
"""Generate local lab credentials once without printing or overwriting secrets."""

import os
from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    values = {
        "MYSQL_DATABASE": "qlsv",
        "MYSQL_USER": "qlsv_app",
        "MYSQL_PASSWORD": secrets.token_hex(24),
        "MYSQL_ROOT_PASSWORD": secrets.token_hex(24),
        "DJANGO_SECRET_KEY": secrets.token_hex(40),
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost:8080,http://127.0.0.1:8080",
        "WEB_PORT": "8080",
        "PMA_PORT": "8081",
    }
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(".env da ton tai: giu nguyen. Khong doi mat khau cua database da khoi tao.")
        return
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("# Local credentials. Never commit or share this file.\n")
        for key, value in values.items():
            stream.write(f"{key}={value}\n")
    print("Da tao .env voi mat khau ngau nhien. Khong chia se file nay.")


if __name__ == "__main__":
    main()
