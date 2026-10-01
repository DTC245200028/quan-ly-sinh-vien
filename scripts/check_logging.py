#!/usr/bin/env python3
"""Check Loki readiness and a fresh HTTP -> Docker -> Promtail -> Loki marker."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


def query_url(base, query, now):
    params = urllib.parse.urlencode({
        "query": query,
        "start": str(int((now - 300) * 1_000_000_000)),
        "end": str(int(now * 1_000_000_000)),
        "limit": "20",
        "direction": "backward",
    })
    return f"{base}/loki/api/v1/query_range?{params}"


def marker_found(payload, marker):
    if payload.get("status") != "success" or payload.get("data", {}).get("resultType") != "streams":
        return False
    for stream in payload["data"].get("result", []):
        labels = stream.get("stream", {})
        if labels.get("project") != "qlsv" or labels.get("service") != "nginx":
            continue
        for _, message in stream.get("values", []):
            if marker in message:
                return True
    return False


def check(timeout, opener=None, monotonic=time.monotonic, now=time.time, sleep=time.sleep):
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}))
    loki = "http://127.0.0.1:3100"
    deadline = monotonic() + timeout
    last_error = "Loki chua san sang"
    while monotonic() < deadline:
        try:
            with opener.open(f"{loki}/ready", timeout=3) as response:
                if response.status == 200:
                    break
        except (OSError, urllib.error.URLError) as error:
            last_error = str(error)
        sleep(2)
    else:
        raise RuntimeError(f"Loki chua ready sau {timeout}s: {last_error}")

    marker = "moc3-demo-404-" + uuid.uuid4().hex[:12]
    url = "http://127.0.0.1:8080/" + marker
    try:
        with opener.open(url, timeout=5) as response:
            raise RuntimeError(f"Duong dan demo can HTTP404, nhung nhan {response.status}.")
    except urllib.error.HTTPError as error:
        error.close()
        if error.code != 404:
            raise RuntimeError(f"Website tra HTTP{error.code}, can kiem tra moc1 truoc.") from error

    print("Loki ready; da tao request 404 thu nghiem. Dang doi log qua Promtail...")
    query = '{project="qlsv",service="nginx"} |= "' + marker + '"'
    deadline = monotonic() + timeout
    last_error = "Chua thay marker moi trong Loki"
    while monotonic() < deadline:
        try:
            with opener.open(query_url(loki, query, now()), timeout=5) as response:
                payload = json.load(response)
            if marker_found(payload, marker):
                print("PASS: website -> Docker JSON -> Promtail -> Loki da nhan marker moi.")
                print("Mo Grafana Explore, chon Loki QLSV, Last 15 minutes; thu tung query:")
                print('1. {project="qlsv",service="nginx"}')
                print("2. " + query)
                print('3. sum by (service) (count_over_time({project="qlsv"}[5m]))')
                return marker
            if payload.get("status") == "error":
                last_error = "Loki bao query error; xem log loki de chan doan."
        except (OSError, ValueError, urllib.error.URLError) as error:
            last_error = str(error)
        sleep(2)
    raise RuntimeError(f"Chua xac nhan thu log sau {timeout}s: {last_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per readiness/ingestion stage (default 120)")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("--timeout must be between 1 and 300")
    try:
        check(args.timeout)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Kiem tra log chua dat: {error}", file=sys.stderr)
        print("Chay: bash scripts/logging.sh logs --tail=60 loki promtail", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
