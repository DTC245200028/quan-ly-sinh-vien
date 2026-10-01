#!/usr/bin/env python3
"""Discover this Docker daemon's JSON log directory without changing old secrets."""

import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from init_monitoring import read_values


def log_directory(docker_root, records):
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", docker_root):
        raise ValueError("DockerRootDir khong phai duong dan Linux duoc ho tro.")
    root = PurePosixPath(docker_root)
    if root == PurePosixPath("/") or ".." in root.parts:
        raise ValueError("DockerRootDir qua rong hoac khong hop le.")
    expected = root / "containers"
    if not records:
        raise ValueError("Chua co container qlsv dang chay. Hay chay moc 2 truoc.")
    for record in records:
        if record.get("project") != "qlsv" or record.get("driver") != "json-file":
            raise ValueError("Container qlsv phai dung driver json-file de thu thap log.")
        path = PurePosixPath(record.get("path", ""))
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(expected):
            raise ValueError("LogPath khong nam trong DockerRootDir/containers; dung de kiem tra.")
        if not path.name.endswith("-json.log"):
            raise ValueError("LogPath khong phai file Docker JSON mong doi.")
    return str(expected)


def save_directory(env_path, directory):
    original = env_path.read_bytes()
    values = read_values(original.decode("utf-8-sig"))
    if not values.get("MYSQL_EXPORTER_PASSWORD") or not values.get("GRAFANA_ADMIN_PASSWORD"):
        raise ValueError("Thieu cau hinh moc 2 trong .env; chua the bat log.")
    if "DOCKER_LOG_DIR" in values:
        if values["DOCKER_LOG_DIR"] != directory:
            raise ValueError("DOCKER_LOG_DIR da co nhung khac daemon hien tai; khong tu ghi de.")
        return False
    separator = b"" if original.endswith(b"\n") else b"\n"
    with env_path.open("ab") as stream:
        stream.write(separator + f"DOCKER_LOG_DIR={directory}\n".encode("utf-8"))
    if os.name == "posix":
        env_path.chmod(0o600)
    return True


def main():
    project = Path(__file__).resolve().parents[1]
    try:
        if os.name != "posix":
            raise RuntimeError("Chay prepare_logging.py trong Ubuntu dang chay Docker.")
        prefix = []
        if os.geteuid() != 0:
            subprocess.run(["sudo", "-v"], check=True)
            prefix = ["sudo", "-n"]

        def output(arguments):
            return subprocess.check_output(prefix + ["docker"] + arguments, cwd=project, text=True, timeout=30).strip()

        docker_root = output(["info", "--format", "{{.DockerRootDir}}"])
        ids = output(["ps", "--filter", "label=com.docker.compose.project=qlsv", "--format", "{{.ID}}"]).split()
        if not ids:
            raise ValueError("Chua co container qlsv dang chay.")
        template = '{"project":{{json (index .Config.Labels "com.docker.compose.project")}},"driver":{{json .HostConfig.LogConfig.Type}},"path":{{json .LogPath}}}'
        records = [json.loads(line) for line in output(["inspect", "--format", template, *ids]).splitlines()]
        directory = log_directory(docker_root, records)
        changed = save_directory(project / ".env", directory)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Chuan bi log dung: {error}", file=sys.stderr)
        return 1
    print(f"{'Da them' if changed else 'Giu nguyen'} DOCKER_LOG_DIR={directory}")
    print(f"Da kiem tra {len(records)} container qlsv dung json-file; giu nguyen mat khau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
