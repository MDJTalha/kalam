"""Read-only Phase 8 security smoke for a running gateway and API."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def probe(url, method="GET", headers=None, body=None):
    request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    opener = urllib.request.build_opener(urllib.request.HTTPHandler)
    try:
        response = opener.open(request, timeout=12)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, {name.lower(): value for name, value in response.headers.items()}


def check(results, name, actual, expected, details=""):
    passed = actual == expected
    results.append({"name": name, "pass": passed, "expected": expected,
                    "actual": actual, "details": details})
    print(f"{'PASS' if passed else 'FAIL'} {name}: {actual}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", default="http://127.0.0.1:3100")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--web-origin", default="http://127.0.0.1:3000")
    parser.add_argument("--output", default="qa/phase8-security-smoke.json")
    args = parser.parse_args()
    gateway, api = args.gateway.rstrip("/"), args.api.rstrip("/")
    results = []
    expected_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=()",
    }
    status, headers = probe(gateway + "/")
    check(results, "gateway_home", status, 200)
    for name, value in expected_headers.items():
        actual = headers.get(name.lower(), "")
        check(results, "gateway_" + name.lower(), value in actual, True)
    for path in ("/api/v1/auth/me", "/api/v1/reports/summary"):
        status, _ = probe(api + path)
        check(results, "anonymous_" + path, status, 401)
    status, headers = probe(
        api + "/api/v1/auth/forgot-password", method="POST",
        headers={"Origin": "https://untrusted.invalid", "Content-Type": "application/json"},
        body=b"{}",
    )
    check(results, "foreign_origin_rejected", status, 403)
    for name, value in expected_headers.items():
        actual = headers.get(name.lower(), "")
        check(results, "denial_" + name.lower(), value in actual, True)
    check(results, "denial_request_id", bool(headers.get("x-request-id")), True)
    status, _ = probe(api + "/api/v1/health/live", headers={"Host": "invalid.example"})
    check(results, "untrusted_host_rejected", status, 400)
    status, headers = probe(
        api + "/api/v1/auth/login", method="OPTIONS",
        headers={"Origin": "https://untrusted.invalid",
                 "Access-Control-Request-Method": "POST"},
    )
    check(results, "foreign_cors_preflight_rejected", status, 400)
    check(results, "foreign_cors_origin_absent",
          bool(headers.get("access-control-allow-origin")), False)
    status, headers = probe(
        api + "/api/v1/auth/login", method="OPTIONS",
        headers={"Origin": args.web_origin, "Access-Control-Request-Method": "POST"},
    )
    check(results, "trusted_cors_preflight", status, 200)
    check(results, "trusted_cors_origin", headers.get("access-control-allow-origin"),
          args.web_origin)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "gateway": gateway, "api": api, "checks": results}
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    failures = [item["name"] for item in results if not item["pass"]]
    print(json.dumps({"total": len(results), "failures": failures,
                      "report": str(output)}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
