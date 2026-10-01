#!/usr/bin/env python3
"""Create the dedicated MySQL metrics account in the existing database."""

import os
from pathlib import Path
import re
import subprocess
import sys

from init_monitoring import read_values


def exporter_sql(password):
    # Only generated hex is accepted, so SQL interpolation cannot carry syntax.
    if not re.fullmatch(r"[0-9a-f]{48}", password):
        raise ValueError("MYSQL_EXPORTER_PASSWORD khong hop le; chay init_monitoring.py.")
    return (
        f"CREATE USER IF NOT EXISTS 'qlsv_exporter'@'%' IDENTIFIED BY '{password}' WITH MAX_USER_CONNECTIONS 3;\n"
        f"ALTER USER 'qlsv_exporter'@'%' IDENTIFIED BY '{password}' WITH MAX_USER_CONNECTIONS 3;\n"
        "GRANT PROCESS, REPLICATION CLIENT ON *.* TO 'qlsv_exporter'@'%';\n"
    )


def provision(root, password, prefix, runner=subprocess.run):
    # Root's existing secret is expanded INSIDE db; no secret in host argv.
    command = prefix + [
        "docker", "compose", "-f", "compose.yaml", "exec", "-T", "db", "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root --protocol=socket --batch',
    ]
    result = runner(
        command, cwd=root, input=exporter_sql(password),
        text=True, capture_output=True, timeout=90,
    )
    if result.returncode:
        # mysql errors can contain the failed statement: redact before printing.
        detail = result.stderr.replace(password, "[REDACTED]").strip()
        raise RuntimeError(f"Khong tao duoc user giam sat (exit {result.returncode}). {detail}")


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        if os.name != "posix":
            raise RuntimeError("Chay script nay trong Ubuntu cua ban.")
        values = read_values((root / ".env").read_text(encoding="utf-8-sig"))
        password = values.get("MYSQL_EXPORTER_PASSWORD", "")
        exporter_sql(password)
        prefix = []
        if os.geteuid() != 0:
            # Authenticate with the terminal first; sudo must not consume SQL stdin.
            subprocess.run(["sudo", "-v"], check=True)
            prefix = ["sudo", "-n"]
        provision(root, password, prefix)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Setup monitoring dung: {error}", file=sys.stderr)
        return 1
    print("Da cau hinh qlsv_exporter: chi giam sat metadata, toi da 3 ket noi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
