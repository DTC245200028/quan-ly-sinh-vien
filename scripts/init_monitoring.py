#!/usr/bin/env python3
"""Append monitoring settings without changing any existing application secret."""

import os
from pathlib import Path
import re
import secrets
import sys


def read_values(content):
    values = {}
    for line in content.splitlines():
        match = re.match(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            raise ValueError(f"Bien {key} bi lap trong .env; hay sua truoc khi tiep tuc.")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def initialize(path):
    # Read bytes to preserve existing formatting and application secrets exactly.
    original = path.read_bytes()
    values = read_values(original.decode("utf-8-sig"))
    for key in ("MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "DJANGO_SECRET_KEY"):
        if not values.get(key):
            raise ValueError(f"Thieu {key} trong .env moc1; dung lai de kiem tra.")
    defaults = {
        "GRAFANA_ADMIN_USER": "admin",
        "GRAFANA_ADMIN_PASSWORD": secrets.token_hex(24),
        "MYSQL_EXPORTER_PASSWORD": secrets.token_hex(24),
    }
    additions = {key: value for key, value in defaults.items() if key not in values}
    merged = {**values, **additions}
    for key in defaults:
        if not merged[key]:
            raise ValueError(f"{key} dang rong; khong tu ghi de gia tri da co.")
    if not re.fullmatch(r"[0-9a-f]{48}", merged["MYSQL_EXPORTER_PASSWORD"]):
        raise ValueError("MYSQL_EXPORTER_PASSWORD phai la 48 ky tu hex sinh boi script.")
    if additions:
        separator = b"" if original.endswith(b"\n") else b"\n"
        extra = "# Monitoring credentials. Never share this file.\n"
        extra += "".join(f"{key}={value}\n" for key, value in additions.items())
        with path.open("ab") as stream:
            stream.write(separator + extra.encode("utf-8"))
    if os.name == "posix":
        path.chmod(0o600)
    return len(additions)


def main():
    path = Path(__file__).resolve().parents[1] / ".env"
    try:
        count = initialize(path)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Khong khoi tao giam sat: {error}", file=sys.stderr)
        return 1
    print(f"Da them {count} bien giam sat. Giu nguyen mat khau va du lieu moc1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
