"""Logging setup and end-to-end probe tests without Docker, HTTP or real .env."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.parse

import check_logging
import prepare_logging


def record(project="qlsv", driver="json-file", path="/var/lib/docker/containers/abc/abc-json.log"):
    return {"project": project, "driver": driver, "path": path}


def payload(marker, project="qlsv", service="nginx"):
    return {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [{
                "stream": {"project": project, "service": service},
                "values": [["1800000000000000000", f'GET /{marker} HTTP/1.1 404']],
            }],
        },
    }


class Response(io.BytesIO):
    def __init__(self, data=None, status=200):
        super().__init__(json.dumps(data).encode("utf-8") if data is not None else b"ready")
        self.status = status


class FakeClock:
    def __init__(self):
        self.value = 0

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class LogDirectoryTests(unittest.TestCase):
    def test_default_and_custom_daemon_roots(self):
        self.assertEqual(prepare_logging.log_directory("/var/lib/docker", [record()]), "/var/lib/docker/containers")
        custom = record(path="/srv/docker-data/containers/abc/abc-json.log")
        self.assertEqual(prepare_logging.log_directory("/srv/docker-data", [custom]), "/srv/docker-data/containers")

    def test_rejects_broad_relative_traversal_and_interpolated_roots(self):
        for root in ("/", "var/lib/docker", "/var/../docker", "/var/lib/$DOCKER", "/var/lib/docker\nEVIL=1"):
            with self.subTest(root=root), self.assertRaises(ValueError):
                prepare_logging.log_directory(root, [record()])

    def test_every_record_must_belong_to_exact_project_and_json_driver(self):
        for invalid in (record(project="wordpress"), record(project="qlsv-old"), record(project=""), record(driver="local")):
            with self.subTest(record=invalid), self.assertRaises(ValueError):
                prepare_logging.log_directory("/var/lib/docker", [record(), invalid])

    def test_empty_container_list_rejected(self):
        with self.assertRaises(ValueError):
            prepare_logging.log_directory("/var/lib/docker", [])

    def test_log_path_must_stay_in_container_directory(self):
        for path in (
            "containers/abc/abc-json.log",
            "/var/lib/docker/containers-other/abc-json.log",
            "/var/lib/docker/containers/../private/abc-json.log",
            "/srv/docker/containers/abc/abc-json.log",
            "/var/lib/docker/containers/abc/local.log",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare_logging.log_directory("/var/lib/docker", [record(path=path)])


class SaveDirectoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / ".env"
        self.original = (
            b'\xef\xbb\xbf# Existing settings\r\nMYSQL_PASSWORD="fake-existing-secret"\r\n'
            b'MYSQL_EXPORTER_PASSWORD=fake-exporter-secret\r\n'
            b'GRAFANA_ADMIN_PASSWORD=fake-grafana-secret'
        )
        self.path.write_bytes(self.original)

    def test_append_preserves_all_existing_bytes_and_rerun_is_identical(self):
        self.assertTrue(prepare_logging.save_directory(self.path, "/var/lib/docker/containers"))
        expected = self.original + b"\nDOCKER_LOG_DIR=/var/lib/docker/containers\n"
        self.assertEqual(self.path.read_bytes(), expected)
        self.assertFalse(prepare_logging.save_directory(self.path, "/var/lib/docker/containers"))
        self.assertEqual(self.path.read_bytes(), expected)

    def test_conflicting_or_empty_existing_directory_does_not_overwrite(self):
        for directory in ("/srv/other/containers", ""):
            with self.subTest(directory=directory):
                original = self.original + f"\nDOCKER_LOG_DIR={directory}\n".encode()
                self.path.write_bytes(original)
                with self.assertRaises(ValueError):
                    prepare_logging.save_directory(self.path, "/var/lib/docker/containers")
                self.assertEqual(self.path.read_bytes(), original)

    def test_missing_monitoring_setting_or_duplicate_key_does_not_write(self):
        cases = (
            b"MYSQL_EXPORTER_PASSWORD=fake-exporter\n",
            b"GRAFANA_ADMIN_PASSWORD=fake-grafana\n",
            self.original + b"\nGRAFANA_ADMIN_PASSWORD=duplicate\n",
        )
        for original in cases:
            with self.subTest(content=original):
                self.path.write_bytes(original)
                with self.assertRaises(ValueError):
                    prepare_logging.save_directory(self.path, "/var/lib/docker/containers")
                self.assertEqual(self.path.read_bytes(), original)

    def test_absent_env_is_not_created(self):
        absent = self.path.parent / "missing.env"
        with self.assertRaises(FileNotFoundError):
            prepare_logging.save_directory(absent, "/var/lib/docker/containers")
        self.assertFalse(absent.exists())


class MarkerTests(unittest.TestCase):
    def test_accepts_exact_project_and_nginx_marker(self):
        self.assertTrue(check_logging.marker_found(payload("new-marker"), "new-marker"))

    def test_rejects_old_marker_wrong_project_service_or_missing_labels(self):
        for candidate in (
            payload("old-marker"),
            payload("new-marker", project="wordpress"),
            payload("new-marker", project="qlsv-old"),
            payload("new-marker", project=""),
            payload("new-marker", service="app"),
        ):
            with self.subTest(candidate=candidate):
                self.assertFalse(check_logging.marker_found(candidate, "new-marker"))
        missing = payload("new-marker")
        missing["data"]["result"][0]["stream"] = {}
        self.assertFalse(check_logging.marker_found(missing, "new-marker"))

    def test_error_empty_and_nonstream_responses_do_not_pass(self):
        for candidate in ({}, {"status": "error"}, {"status": "success", "data": {"resultType": "vector", "result": []}}, {"status": "success", "data": {"resultType": "streams", "result": []}}):
            with self.subTest(candidate=candidate):
                self.assertFalse(check_logging.marker_found(candidate, "marker"))

    def test_query_uses_five_minute_window_and_encoded_selector(self):
        query = '{project="qlsv",service="nginx"} |= "fresh-marker"'
        url = check_logging.query_url("http://127.0.0.1:3100", query, 1800000000)
        parts = urllib.parse.urlsplit(url)
        parameters = urllib.parse.parse_qs(parts.query)
        self.assertEqual(parts.path, "/loki/api/v1/query_range")
        self.assertEqual(parameters["query"], [query])
        self.assertEqual(parameters["start"], [str((1800000000 - 300) * 1_000_000_000)])
        self.assertEqual(parameters["end"], [str(1800000000 * 1_000_000_000)])


class LoggingCheckTests(unittest.TestCase):
    def run_check(self, opener, timeout=6):
        clock = FakeClock()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(check_logging.uuid, "uuid4", return_value=Mock(hex="123456789abcffffffff")):
            result = check_logging.check(timeout, opener=opener, monotonic=clock.monotonic, now=lambda: 1800000000, sleep=clock.sleep)
        return result, output.getvalue()

    def test_waits_for_new_marker_after_readiness_and_http404(self):
        expected = "moc3-demo-404-123456789abc"
        queries = []

        def open_url(url, timeout):
            if url.endswith("/ready"):
                return Response()
            if url.startswith("http://127.0.0.1:8080/"):
                self.assertTrue(url.endswith(expected))
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO())
            queries.append(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["query"][0])
            if len(queries) == 1:
                return Response(payload("stale-demo-marker"))
            if len(queries) == 2:
                return Response(payload(expected, project="wordpress"))
            return Response(payload(expected))

        marker, output = self.run_check(Mock(open=Mock(side_effect=open_url)))
        self.assertEqual(marker, expected)
        self.assertEqual(len(queries), 3)
        self.assertTrue(all(query == '{project="qlsv",service="nginx"} |= "' + expected + '"' for query in queries))
        self.assertIn("PASS:", output)

    def test_readiness_timeout_never_generates_website_request(self):
        opener = Mock(open=Mock(return_value=None))
        opener.open.side_effect = lambda url, timeout: Response(status=503)
        with self.assertRaisesRegex(RuntimeError, "Loki chua ready"):
            self.run_check(opener, timeout=4)
        self.assertTrue(all(call.args[0].endswith("/ready") for call in opener.open.call_args_list))

    def test_non404_website_response_fails_before_querying_loki(self):
        for status in (200, 503):
            with self.subTest(status=status):
                def open_url(url, timeout):
                    if url.endswith("/ready"):
                        return Response()
                    if status >= 400:
                        raise urllib.error.HTTPError(url, status, "Unavailable", {}, io.BytesIO())
                    return Response(status=status)

                opener = Mock(open=Mock(side_effect=open_url))
                with self.assertRaises(RuntimeError):
                    self.run_check(opener)
                self.assertFalse(any("query_range" in call.args[0] for call in opener.open.call_args_list))

    def test_only_wrong_project_marker_times_out_without_pass(self):
        expected = "moc3-demo-404-123456789abc"

        def open_url(url, timeout):
            if url.endswith("/ready"):
                return Response()
            if url.startswith("http://127.0.0.1:8080/"):
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO())
            return Response(payload(expected, project="wordpress"))

        with self.assertRaisesRegex(RuntimeError, "Chua xac nhan thu log"):
            self.run_check(Mock(open=Mock(side_effect=open_url)), timeout=4)


if __name__ == "__main__":
    unittest.main()
