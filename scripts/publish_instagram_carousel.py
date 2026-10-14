#!/usr/bin/env python3
"""Publish an APPROVED Instagram carousel from public, repository-hosted files.

GitHub secrets hold the Meta token. This script NEVER copies it into files/logs.
Use a reviewable manifest and an approval gate; draft changes only run preflight.
"""
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "tateishiaoremi-crypto/nora-golf-lab-media"
EXPECTED_USERNAME = "nora_golf_lab"
EXPECTED_IG_ID = "17841428397719857"
VERSION = os.getenv("INSTAGRAM_GRAPH_VERSION", "v25.0")
BASE = f"https://graph.facebook.com/{VERSION}"
ROOT = Path.cwd().resolve()


def api(method, route, token, data=None):
    url = BASE + "/" + route.lstrip("/")
    body = urllib.parse.urlencode(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url, data=body, method=method,
        headers={"Authorization": "Bearer " + token,
                 "User-Agent": "nora-golf-lab-publisher/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meta API {method} {route} returned HTTP {e.code}: {raw[:650]}") from None


def preflight(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError("manifest version must be 1")
    if manifest.get("username") != EXPECTED_USERNAME:
        raise ValueError("unexpected Instagram username")
    if manifest.get("status") not in ("draft", "approved"):
        raise ValueError("status must be draft or approved")
    items = manifest.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 10:
        raise ValueError("carousel needs 2 to 10 media items")
    if manifest.get("status") == "approved" and not str(manifest.get("caption", "")).strip():
        raise ValueError("approved post must have a caption")
    if len(manifest.get("caption", "")) > 2200:
        raise ValueError("Instagram caption exceeds 2200 characters")

    cleaned = []
    for index, item in enumerate(items, 1):
        kind, relative = item.get("type"), item.get("path")
        if kind not in ("image", "video") or not isinstance(relative, str):
            raise ValueError(f"item {index}: invalid type/path")
        path_parts = PurePosixPath(relative)
        if (path_parts.is_absolute() or ".." in path_parts.parts
                or "\\" in relative or "%" in relative or not relative.startswith("posts/")):
            raise ValueError(f"item {index}: unsupported repository path")
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"item {index}: local file not found: {relative}")
        extension = path.suffix.lower()
        if kind == "image" and extension not in (".jpg", ".jpeg"):
            raise ValueError(f"item {index}: Instagram images must be JPEG")
        if kind == "video" and extension not in (".mp4", ".mov"):
            raise ValueError(f"item {index}: Instagram carousel videos must be MP4 or MOV")

        # ffprobe is installed in the GitHub runner; check stream/shape/audio before approval.
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", str(path)], capture_output=True, text=True, check=True)
        meta = json.loads(probe.stdout)
        video_streams = [s for s in meta.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            raise ValueError(f"item {index}: no image/video stream")
        video = video_streams[0]
        w, h = int(video.get("width", 0)), int(video.get("height", 0))
        if w <= 0 or h <= 0:
            raise ValueError(f"item {index}: could not read dimensions")
        ratio = w / h
        if kind == "image" and not 0.799 <= ratio <= 1.911:
            raise ValueError(f"item {index}: JPEG aspect ratio {ratio:.3f} outside 4:5 to 1.91:1")
        if kind == "video":
            if not 0.799 <= ratio <= 1.911:
                print(f"FRAMING REVIEW NEEDED: item {index} has {ratio:.3f} aspect ratio; first carousel image uses a 4:5 layout")
                if manifest["status"] == "approved" and not item.get("framing_approved"):
                    raise ValueError(f"item {index}: video framing must be reviewed before approval")
            if video.get("codec_name") not in ("h264", "hevc"):
                raise ValueError(f"item {index}: video must use H264/HEVC")
            if not any(s.get("codec_type") == "audio" for s in meta.get("streams", [])):
                raise ValueError(f"item {index}: no audio track (review required)")
            duration = float(meta.get("format", {}).get("duration", 0))
            if duration < 3:
                raise ValueError(f"item {index}: video is shorter than 3 seconds")
        print(f"PRECHECK item {index}: {kind} {relative} ({w}x{h})")
        cleaned.append({"type": kind, "path": relative})
    return manifest, cleaned


def await_ready(token, container_id, max_seconds=600):
    limit = time.monotonic() + max_seconds
    while time.monotonic() < limit:
        state = api("GET", f"{container_id}?fields=status_code,status", token)
        code = state.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Media container {container_id} failed: {state.get('status')}")
        time.sleep(15)
    raise TimeoutError(f"Media container {container_id} not ready before deadline")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/publish_instagram_carousel.py posts/.../instagram-carousel.json")
    manifest_path = (ROOT / sys.argv[1]).resolve()
    if not manifest_path.is_relative_to(ROOT) or manifest_path.name != "instagram-carousel.json":
        raise ValueError("expected posts/.../instagram-carousel.json")
    manifest, items = preflight(manifest_path)
    receipt_path = manifest_path.with_name("instagram-published.json")
    if receipt_path.exists():
        raise RuntimeError("Already published: receipt exists; refusing to duplicate post")
    if manifest["status"] == "draft":
        print("DRAFT: Preflight only; no Instagram post created.")
        return

    token = os.getenv("INSTAGRAM_GRAPH_TOKEN", "")
    if not token:
        raise RuntimeError("Missing INSTAGRAM_GRAPH_TOKEN in GitHub Actions secrets; no post made")
    git_sha = os.getenv("GITHUB_SHA")
    if not git_sha or len(git_sha) < 20:
        raise RuntimeError("Missing pinned GITHUB_SHA; no post made")

    identity = api("GET", f"{EXPECTED_IG_ID}?fields=id,username", token)
    if identity.get("username") != EXPECTED_USERNAME:
        raise RuntimeError("Token account mismatch; refusing to publish")
    print("Meta authentication OK: nora_golf_lab")
    children = []
    for item in items:
        media_url = (
            f"https://raw.githubusercontent.com/{REPOSITORY}/{git_sha}/"
            + urllib.parse.quote(item["path"], safe="/")
        )
        payload = {"is_carousel_item": "true"}
        if item["type"] == "image":
            payload["image_url"] = media_url
        else:
            payload.update({"media_type": "VIDEO", "video_url": media_url})
        created = api("POST", f"{EXPECTED_IG_ID}/media", token, payload)
        container_id = created["id"]
        await_ready(token, container_id)
        children.append(container_id)
        print(f"Ready: {item['type']} container {len(children)}/{len(items)}")

    parent = api("POST", f"{EXPECTED_IG_ID}/media", token, {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": manifest["caption"],
    })
    parent_id = parent["id"]
    await_ready(token, parent_id)
    result = api("POST", f"{EXPECTED_IG_ID}/media_publish", token, {
        "creation_id": parent_id
    })
    media_id = result["id"]
    try:
        info = api("GET", f"{media_id}?fields=id,permalink", token)
    except Exception as error:
        print(f"Permalink retrieval failed (post WAS published): {type(error).__name__}")
        info = {}
    receipt_path.write_text(json.dumps({
        "instagram_media_id": media_id,
        "permalink": info.get("permalink", ""),
        "source_manifest": str(manifest_path.relative_to(ROOT)),
        "source_commit": git_sha,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PUBLISHED Instagram media id={media_id}")
    if info.get("permalink"):
        print(f"Instagram URL: {info['permalink']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
