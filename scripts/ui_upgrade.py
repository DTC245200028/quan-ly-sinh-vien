#!/usr/bin/env python3
"""Apply or roll back the QLSV UI overlay without touching data or secrets."""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import stat
import tempfile
import uuid
import zipfile


APP_FILES = {
    "app/config/settings.py",
    "app/students/admin.py",
    "app/students/apps.py",
    "app/students/admin_site.py",
    "app/students/test_admin_ui.py",
    "app/templates/admin/base_site.html",
    "app/templates/admin/index.html",
    "app/templates/admin/login.html",
    "app/templates/admin/nav_sidebar.html",
    "app/templates/admin/includes/icon.html",
    "app/students/static/students/css/admin-ui.css",
    "app/students/static/students/js/admin-ui.js",
}
OPTIONAL_FILES = {"docs/ui-upgrade.md", "scripts/ui_upgrade.py"}
ALLOWED_FILES = APP_FILES | OPTIONAL_FILES
MAX_FILE_BYTES = 2 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    """Reject symlinks and paths outside the intended project or backup root."""
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"Unsafe path: {relative}")
    path = root.joinpath(relative)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path outside project: {relative}")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Symlink is not supported: {cursor}")
    if path.exists() and not path.is_file() and not path.is_dir():
        raise ValueError(f"Unsupported file: {path}")
    return path


def write_file(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_manifest(backup, manifest):
    write_file(backup / "manifest.json", json.dumps(manifest, indent=2).encode())


def apply(root, archive):
    with zipfile.ZipFile(archive) as package:
        items = [item for item in package.infolist() if not item.is_dir()]
        names = [item.filename for item in items]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate file paths in ZIP")
        if set(names) - ALLOWED_FILES or APP_FILES - set(names):
            raise ValueError("ZIP does not match the QLSV UI file list")
        payload = {}
        for item in items:
            if item.file_size > MAX_FILE_BYTES:
                raise ValueError(f"File too large: {item.filename}")
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError(f"Symlink in ZIP: {item.filename}")
            safe_path(root, item.filename)
            payload[item.filename] = package.read(item)

    records = {}
    previous = {}
    for name, data in sorted(payload.items()):
        target = safe_path(root, name)
        if target.exists() and not target.is_file():
            raise ValueError(f"Expected a regular file: {name}")
        before = target.read_bytes() if target.exists() else None
        previous[name] = before
        records[name] = {
            "before": digest(before) if before is not None else None,
            "after": digest(data),
            "mode": stat.S_IMODE(target.stat().st_mode) if before is not None else 0o644,
        }

    backup_base = safe_path(root, "tmp/ui-backups")
    backup_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:6]
    backup = backup_base / backup_name
    backup.mkdir(parents=True)
    for name, before in previous.items():
        if before is not None:
            write_file(backup / "files" / name, before, records[name]["mode"])
    manifest = {"version": 1, "state": "prepared", "files": records}
    save_manifest(backup, manifest)
    print(f"Backup: {backup}", flush=True)
    for name, data in payload.items():
        write_file(safe_path(root, name), data, records[name]["mode"])
    manifest["state"] = "applied"
    save_manifest(backup, manifest)
    print(f"Applied {len(payload)} UI files. Rebuild the app container next.")


def rollback(root, backup_name):
    backup_base = safe_path(root, "tmp/ui-backups")
    if backup_name:
        if Path(backup_name).name != backup_name or backup_name in {".", ".."}:
            raise ValueError("Use only the backup directory name")
        backup = safe_path(backup_base, backup_name)
    else:
        backups = sorted(backup_base.glob("*/manifest.json"))
        if not backups:
            raise ValueError("No UI backup found in tmp/ui-backups")
        backup = safe_path(backup_base, backups[-1].parent.name)
    manifest_path = safe_path(backup, "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") != 1 or manifest.get("state") not in {"prepared", "applied"}:
        raise ValueError("This backup is invalid or has already been rolled back")
    records = manifest["files"]
    if set(records) - ALLOWED_FILES or APP_FILES - set(records):
        raise ValueError("Backup does not match the QLSV UI file list")
    restore = {}
    for name, record in records.items():
        target = safe_path(root, name)
        current = digest(target.read_bytes()) if target.exists() else None
        if current not in {record["before"], record["after"]}:
            raise ValueError(f"File changed after upgrade; preserve and review it first: {name}")
        before = None
        if record["before"] is not None:
            saved = safe_path(backup, "files/" + name)
            before = saved.read_bytes()
            if digest(before) != record["before"]:
                raise ValueError(f"Backup checksum mismatch: {name}")
        restore[name] = before
    for name, before in restore.items():
        target = safe_path(root, name)
        if before is None:
            target.unlink(missing_ok=True)
        else:
            write_file(target, before, records[name]["mode"])
    manifest["state"] = "rolled_back"
    save_manifest(backup, manifest)
    print(f"Restored source from {backup}. Rebuild the app container next.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("archive", type=Path)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("backup", nargs="?")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    for marker in ("compose.yaml", "app/config/settings.py", "scripts/logging.sh"):
        if not safe_path(root, marker).is_file():
            parser.error("Run this command from ~/quan-ly-sinh-vien")
    try:
        if args.command == "apply":
            apply(root, args.archive)
        else:
            rollback(root, args.backup)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"ERROR: {error}\nNo container or database operation was performed.\n")


if __name__ == "__main__":
    main()
