"""Safety checks for monitoring setup; no Docker daemon or real secrets needed."""

import contextlib
import io
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import init_monitoring
import setup_monitoring


BASE_ENV = (
    "# Existing application settings\n"
    "MYSQL_DATABASE=qlsv\n"
    "MYSQL_USER=qlsv_app\n"
    "MYSQL_PASSWORD='existing-app-test-secret'\n"
    'MYSQL_ROOT_PASSWORD="existing-root-test-secret"\n'
    "DJANGO_SECRET_KEY=existing-django-test-secret\n"
    "WEB_PORT=8080\n"
)
EXPORTER_PASSWORD = "abcdef0123456789" * 3


class InitializeMonitoringTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env_path = Path(self.directory.name) / ".env"

    def write_env(self, content=BASE_ENV):
        raw = content.encode("utf-8") if isinstance(content, str) else content
        self.env_path.write_bytes(raw)
        return raw

    def assert_rejected_without_mutation(self, content, error_type=ValueError):
        original = self.write_env(content)
        with self.assertRaises(error_type):
            init_monitoring.initialize(self.env_path)
        self.assertEqual(self.env_path.read_bytes(), original)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [self.env_path])

    def test_preserves_existing_bytes_bom_crlf_and_missing_final_newline(self):
        original = self.write_env(b"\xef\xbb\xbf" + BASE_ENV.rstrip("\n").replace("\n", "\r\n").encode("utf-8"))

        count = init_monitoring.initialize(self.env_path)

        updated = self.env_path.read_bytes()
        self.assertEqual(count, 3)
        self.assertEqual(updated[:len(original)], original)
        self.assertTrue(updated[len(original):].startswith(b"\n"))
        before = init_monitoring.read_values(original.decode("utf-8-sig"))
        after = init_monitoring.read_values(updated.decode("utf-8-sig"))
        for key, value in before.items():
            self.assertEqual(after[key], value)
        self.assertEqual(after["GRAFANA_ADMIN_USER"], "admin")
        self.assertRegex(after["GRAFANA_ADMIN_PASSWORD"], r"^[0-9a-f]{48}$")
        self.assertRegex(after["MYSQL_EXPORTER_PASSWORD"], r"^[0-9a-f]{48}$")
        self.assertNotEqual(after["GRAFANA_ADMIN_PASSWORD"], after["MYSQL_EXPORTER_PASSWORD"])

    def test_second_run_is_byte_identical_and_preserves_generated_credentials(self):
        self.write_env()
        init_monitoring.initialize(self.env_path)
        initialized = self.env_path.read_bytes()

        count = init_monitoring.initialize(self.env_path)

        self.assertEqual(count, 0)
        self.assertEqual(self.env_path.read_bytes(), initialized)

    def test_partial_monitoring_settings_are_kept_and_only_missing_keys_added(self):
        partial_values = {
            "GRAFANA_ADMIN_USER": "lab-owner",
            "GRAFANA_ADMIN_PASSWORD": "existing-grafana-test-secret",
            "MYSQL_EXPORTER_PASSWORD": EXPORTER_PASSWORD,
        }
        for key, value in partial_values.items():
            with self.subTest(existing_key=key):
                original = self.write_env(BASE_ENV + f"{key}={value}\n")
                self.assertEqual(init_monitoring.initialize(self.env_path), 2)
                updated = self.env_path.read_bytes()
                self.assertTrue(updated.startswith(original))
                parsed = init_monitoring.read_values(updated.decode("utf-8"))
                self.assertEqual(parsed[key], value)
                self.assertTrue(all(parsed.get(name) for name in partial_values))
                self.assertEqual(init_monitoring.initialize(self.env_path), 0)
                self.assertEqual(self.env_path.read_bytes(), updated)

    def test_duplicate_existing_or_monitoring_key_rejected_without_write(self):
        for extra in (
            "MYSQL_PASSWORD=another-test-secret\n",
            "GRAFANA_ADMIN_USER=admin\nGRAFANA_ADMIN_USER=other\n",
            f"MYSQL_EXPORTER_PASSWORD={EXPORTER_PASSWORD}\nMYSQL_EXPORTER_PASSWORD={EXPORTER_PASSWORD}\n",
        ):
            with self.subTest(extra_key=extra.split("=", 1)[0]):
                self.assert_rejected_without_mutation(BASE_ENV + extra)

    def test_missing_application_secret_rejected_without_write(self):
        for key in ("MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "DJANGO_SECRET_KEY"):
            with self.subTest(key=key):
                content = "".join(line for line in BASE_ENV.splitlines(keepends=True) if not line.startswith(key + "="))
                self.assert_rejected_without_mutation(content)

    def test_empty_application_setting_rejected_without_write(self):
        for key in ("MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD", "DJANGO_SECRET_KEY"):
            with self.subTest(key=key):
                content = "".join(f'{key}=""\n' if line.startswith(key + "=") else line for line in BASE_ENV.splitlines(keepends=True))
                self.assert_rejected_without_mutation(content)

    def test_empty_existing_monitoring_setting_not_silently_replaced(self):
        for key in ("GRAFANA_ADMIN_USER", "GRAFANA_ADMIN_PASSWORD", "MYSQL_EXPORTER_PASSWORD"):
            with self.subTest(key=key):
                self.assert_rejected_without_mutation(BASE_ENV + f'{key}=""\n')

    def test_invalid_or_malicious_exporter_password_rejected_before_file_write(self):
        passwords = [
            "a" * 47,
            "a" * 49,
            "G" * 48,
            "A" * 48,
            "$(touch injected-file)",
            "bad'; DROP DATABASE qlsv; --",
            "${MYSQL_ROOT_PASSWORD}",
        ]
        for password in passwords:
            with self.subTest(password_kind=password[:8]):
                self.assert_rejected_without_mutation(BASE_ENV + f"MYSQL_EXPORTER_PASSWORD={password}\n")

    def test_non_utf8_content_rejected_without_write(self):
        self.assert_rejected_without_mutation(BASE_ENV.encode("utf-8") + b"\xff", UnicodeError)

    def test_missing_env_is_not_created_with_replacement_credentials(self):
        with self.assertRaises(FileNotFoundError):
            init_monitoring.initialize(self.env_path)
        self.assertFalse(self.env_path.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permissions apply on the Ubuntu deployment host.")
    def test_env_permissions_are_owner_only(self):
        self.write_env()
        self.env_path.chmod(0o644)
        init_monitoring.initialize(self.env_path)
        self.assertEqual(stat.S_IMODE(self.env_path.stat().st_mode), 0o600)


class ProvisionMonitoringTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_sql_uses_dedicated_limited_account_and_supports_rerun(self):
        sql = setup_monitoring.exporter_sql(EXPORTER_PASSWORD)
        self.assertIn("CREATE USER IF NOT EXISTS 'qlsv_exporter'@'%'", sql)
        self.assertIn("ALTER USER 'qlsv_exporter'@'%'", sql)
        self.assertIn("MAX_USER_CONNECTIONS 3", sql)
        self.assertIn("GRANT PROCESS, REPLICATION CLIENT ON *.*", sql)
        self.assertNotIn("ALL PRIVILEGES", sql)
        self.assertNotIn("GRANT SELECT", sql)
        self.assertNotIn("'root'", sql)
        self.assertNotIn("qlsv_app", sql)
        self.assertNotIn("DROP ", sql)

    def test_sql_is_sent_only_through_stdin_and_host_argv_has_no_secret(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))

        setup_monitoring.provision(self.root, EXPORTER_PASSWORD, ["sudo", "-n"], runner=runner)

        runner.assert_called_once()
        command = runner.call_args.args[0]
        kwargs = runner.call_args.kwargs
        self.assertEqual(command[:4], ["sudo", "-n", "docker", "compose"])
        self.assertIn("exec", command)
        self.assertIn("-T", command)
        self.assertIn("db", command)
        self.assertNotIn(EXPORTER_PASSWORD, " ".join(command))
        self.assertNotIn("CREATE USER", " ".join(command))
        self.assertIn('MYSQL_PWD="$MYSQL_ROOT_PASSWORD"', command[-1])
        self.assertEqual(kwargs["input"], setup_monitoring.exporter_sql(EXPORTER_PASSWORD))
        self.assertEqual(kwargs["cwd"], self.root)
        self.assertTrue(kwargs["text"])
        self.assertTrue(kwargs["capture_output"])
        self.assertGreater(kwargs["timeout"], 0)
        self.assertNotIn("env", kwargs)
        self.assertFalse(kwargs.get("shell", False))

    def test_invalid_password_prevents_any_subprocess_call(self):
        for password in ("", "short", "bad'; DROP DATABASE qlsv; --", "${MYSQL_ROOT_PASSWORD}"):
            with self.subTest(password_kind=password[:8]):
                runner = Mock()
                with self.assertRaises(ValueError) as failure:
                    setup_monitoring.provision(self.root, password, [], runner=runner)
                runner.assert_not_called()
                if password:
                    self.assertNotIn(password, str(failure.exception))
                self.assertEqual(list(self.root.iterdir()), [])

    def test_database_error_redacts_every_copy_of_exporter_password(self):
        error = f"ERROR 1045: failed statement IDENTIFIED BY '{EXPORTER_PASSWORD}'; retry '{EXPORTER_PASSWORD}'"
        runner = Mock(return_value=subprocess.CompletedProcess([], 1, EXPORTER_PASSWORD, error))

        with self.assertRaises(RuntimeError) as failure:
            setup_monitoring.provision(self.root, EXPORTER_PASSWORD, [], runner=runner)

        message = str(failure.exception)
        self.assertNotIn(EXPORTER_PASSWORD, message)
        self.assertEqual(message.count("[REDACTED]"), 2)
        self.assertIn("1045", message)
        self.assertIn("exit 1", message)

    def test_success_does_not_print_subprocess_output_or_secrets(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, EXPORTER_PASSWORD, EXPORTER_PASSWORD))
        stdout, stderr = io.StringIO(), io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            setup_monitoring.provision(self.root, EXPORTER_PASSWORD, [], runner=runner)

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
