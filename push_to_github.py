"""Push admin.html and index.html to GitHub Pages via Contents API."""
import base64
import json
import os
import sys
import urllib.request

OWNER = "madados"
REPO = "krmcpc-pages"
BRANCH = "master"

# Read token from WorkBuddy connector
TOKEN_PATH = os.path.expanduser(
    "~/.workbuddy/connectors/028cfe20-12fc-4181-a9be-7e324e538eed/tokens/github.txt"
)
with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    TOKEN = f.read().strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = [
    ("admin.html", os.path.join(BASE_DIR, "admin.html"),
     "fix: admin.html 改用 CloudBase SDK 直连云函数（免 HTTP 网关）"),
    ("index.html", os.path.join(BASE_DIR, "index.html"),
     "fix: index.html 改用 CloudBase SDK 直连云函数（免 HTTP 网关）"),
]


def github_api(method, path, body=None):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-push-script",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, body_text


def push_file(repo_path, local_path, message):
    # Step 1: get current SHA
    status, data = github_api("GET", f"{repo_path}?ref={BRANCH}")
    sha = None
    if status == 200 and isinstance(data, dict):
        sha = data.get("sha")
        print(f"  Current SHA: {sha}")
    else:
        print(f"  File not found, will create new (status={status})")

    # Step 2: read + base64 encode
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("ascii")
    size_kb = os.path.getsize(local_path) / 1024
    print(f"  Size: {size_kb:.1f} KB")

    # Step 3: push
    body = {
        "message": message,
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        body["sha"] = sha

    status, data = github_api("PUT", repo_path, body)
    if status in (200, 201):
        commit_sha = data.get("commit", {}).get("sha", "unknown") if isinstance(data, dict) else "unknown"
        print(f"  OK - commit {commit_sha}")
        return True
    else:
        print(f"  FAILED status={status}")
        print(f"  {str(data)[:500]}")
        return False


def main():
    ok = True
    for repo_path, local_path, msg in FILES:
        print(f"\n=== Pushing {repo_path} ===")
        print(f"  Message: {msg}")
        if not push_file(repo_path, local_path, msg):
            ok = False
    print("\n" + ("=" * 50))
    print("ALL DONE" if ok else "SOME FILES FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
