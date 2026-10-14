#!/usr/bin/env python3
"""Create an UNPUBLISHED image+video Instagram carousel to validate integration.

This program deliberately has NO media_publish call and can not post to the feed.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API="https://graph.instagram.com/v26.0"
RAW="https://raw.githubusercontent.com/tateishiaoremi-crypto/nora-golf-lab-media/main/posts/2026-10-10-menard/"
def request(method, path, token, data=None):
    url=API+"/"+path.lstrip("/")
    body=urllib.parse.urlencode(data).encode() if data is not None else None
    req=urllib.request.Request(url,data=body,method=method,headers={"Authorization":"Bearer "+token})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as error:
        details=error.read().decode("utf-8",errors="replace")
        # API token never included in error print.
        raise RuntimeError(f"Meta API HTTP {error.code} on {method} {path}: {details[:600]}") from None

def ready(token,id,wait=270):
    deadline=time.monotonic()+wait
    while time.monotonic()<deadline:
        state=request("GET",f"{id}?fields=status_code,status",token)
        code=state.get("status_code")
        if code=="FINISHED":
            return
        if code in ("ERROR","EXPIRED"):
            raise RuntimeError(f"Media container processing failed: {state.get('status')}")
        time.sleep(12)
    raise RuntimeError("Video container not ready within deadline")

def main():
    token=os.environ["INSTAGRAM_GRAPH_TOKEN"]
    me=request("GET","me?fields=id,username",token)
    if me.get("username")!="nora_golf_lab":
        raise RuntimeError("Wrong Instagram account")
    ig=str(me["id"])
    print("Authorized account: nora_golf_lab")

    pic=request("POST",f"{ig}/media",token,{
        "image_url":RAW+"photo-2.jpg","is_carousel_item":"true"
    })
    print("Image carousel item created (not published)")

    movie=request("POST",f"{ig}/media",token,{
        "media_type":"VIDEO","video_url":RAW+"swings.mp4","is_carousel_item":"true"
    })
    print("Video carousel item submitted (not published)")
    ready(token,str(movie["id"]))
    print("Video item processed successfully")

    album=request("POST",f"{ig}/media",token,{
        "media_type":"CAROUSEL",
        "children":",".join((str(pic["id"]),str(movie["id"]))),
        "caption":"UNPUBLISHED CONNECTION TEST"
    })
    if not album.get("id"):
        raise RuntimeError("No carousel container returned")
    print("PASS: Mixed photo+video carousel container created successfully.")
    print("NOT PUBLISHED. media_publish endpoint never called.")

if __name__=="__main__":
    try:main()
    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}",file=sys.stderr)
        sys.exit(1)
