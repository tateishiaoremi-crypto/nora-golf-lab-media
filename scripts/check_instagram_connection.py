#!/usr/bin/env python3
"""Test Meta Instagram account publishing access WITHOUT publishing a post.

Reads INSTAGRAM_GRAPH_TOKEN from GitHub Actions secrets, validates that it
belongs to the intended professional account, and creates a temporary test
image container. It intentionally never calls the media_publish endpoint.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v26.0"
IG_USERNAME = "nora_golf_lab"
SAMPLE_JPEG = (
    "https://raw.githubusercontent.com/"
    "tateishiaoremi-crypto/nora-golf-lab-media/main/"
    "posts/2026-10-10-menard/photo-2.jpg"
)


def request(method, endpoint, token, params=None):
    data = urllib.parse.urlencode(params).encode("utf-8") if params else None
    req = urllib.request.Request(
        f"{API}/{endpoint.lstrip('/')}",
        data=data, method=method,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Never output the bearer token or raw API request.
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Meta returned HTTP {error.code} on {endpoint}: {body[:800]}"
        ) from None


def main():
    token = os.getenv("INSTAGRAM_GRAPH_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "GitHub Actions secret INSTAGRAM_GRAPH_TOKEN not configured. "
            "Add the Instagram Login user token in repository Actions secrets."
        )
    identity = request("GET", "me?fields=id,username", token)
    ig_id = str(identity.get("id", ""))
    if not ig_id.isdigit() or identity.get("username") != IG_USERNAME:
        raise RuntimeError("The access token does not belong to nora_golf_lab.")
    print("PASS: Verified nora_golf_lab account identity.")

    # Creates a temporary media container, but does NOT publish it.
    result = request("POST", f"{ig_id}/media", token, {
        "image_url": SAMPLE_JPEG,
    })
    if not result.get("id"):
        raise RuntimeError("Container creation returned no ID.")
    print("PASS: Meta accepted a test image media container.")
    print("NO POST PUBLISHED — account authorization test succeeded.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
