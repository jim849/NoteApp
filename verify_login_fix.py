"""Check the Class 7 lab against your local NotesApp, without sharing cookies.

Run inside the web container, or pass --base-url http://localhost:8080 on the host.
Requires the user's two original Class 6 tokens saved in local files.
"""
import argparse
import http.cookiejar
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


def fetch(opener, url, *, token=None, data=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with opener.open(request, timeout=15) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--stage", choices=("vulnerable", "algorithm-fixed", "fixed"), default="fixed")
    parser.add_argument("--none-token-file", type=Path, required=True,
                        help="File containing your original alg:none token")
    parser.add_argument("--signed-token-file", type=Path, required=True,
                        help="File containing your original s3cr3t-signed token")
    args = parser.parse_args()
    tokens = (args.none_token_file.read_text().strip(), args.signed_token_file.read_text().strip())
    if not all(tokens):
        parser.error("Both original token files must be nonempty; no samples will be generated.")
    base = args.base_url.rstrip("/")
    # This opener never stores cookies, including cookies received during login.
    bearer_only = urllib.request.build_opener()
    expected = {"vulnerable": (200, 200), "algorithm-fixed": (401, 200), "fixed": (401, 401)}[args.stage]
    print(f"Stage: {args.stage}; target: {base}")
    print("Samples: user-supplied original Class 6 tokens; no cookies on Bearer requests.")
    status, body = fetch(bearer_only, base + "/api/notes/3")
    assert status == 401 and json.loads(body) == {"error": "unauthorized"}, (status, body)
    print(f"No credentials: HTTP {status} {body.strip()}")
    for algorithm, original_token, expected_status in zip(("none", "HS256"), tokens, expected):
        status, body = fetch(bearer_only, base + "/api/notes/3", token=original_token)
        assert status == expected_status, (algorithm, status, body)
        if status == 401:
            assert json.loads(body) == {"error": "unauthorized"}, body
            detail = body.strip()
        else:
            detail = f"accepted; note_id={json.loads(body)['id']}"
        print(f"Forged {algorithm}: HTTP {status} {detail}")

    signed_in = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    status, body = fetch(signed_in, base + "/login", data=urllib.parse.urlencode({"username": "alice", "password": "alicepw"}).encode())
    assert status == 200 and "My grades" in body, "Alice login did not reach her dashboard"
    token_match = re.search(r"const TOKEN = (.*?);", body)
    note_match = re.search(r"<td>\s*(\d+)\s*</td>", body)
    assert token_match and note_match, "Dashboard must include a genuine token and Alice's note"
    token = json.loads(token_match.group(1))
    print("Real alice login: HTTP 200 dashboard contains My grades")
    status, body = fetch(bearer_only, base + "/api/notes/" + note_match.group(1), token=token)
    assert status == 200 and json.loads(body)["student"] == "alice", (status, body)
    print(f"Fresh genuine JWT, no cookies: HTTP {status}; student=alice; note_id={json.loads(body)['id']}")
    print("PASS: all checks match the selected stage.")


if __name__ == "__main__":
    main()
