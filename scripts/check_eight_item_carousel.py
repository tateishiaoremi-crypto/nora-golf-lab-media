#!/usr/bin/env python3
"""Verify exact 8-item Menard draft on Meta without publishing."""
import os
import sys
import urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_instagram_carousel import api, preflight, await_ready, EXPECTED_USERNAME, REPOSITORY

def main():
    manifest,items=preflight(Path("posts/2026-10-10-menard/instagram-carousel.json"))
    if manifest["status"]!="draft":
        raise RuntimeError("Safety: only draft manifests can run unpublished test")
    if len(items)!=8 or sum(x["type"]=="video" for x in items)!=5:
        raise RuntimeError("Unexpected media order/count")
    token=os.environ["INSTAGRAM_GRAPH_TOKEN"]
    sha=os.environ["GITHUB_SHA"]
    user=api("GET","me?fields=id,username",token)
    if user.get("username")!=EXPECTED_USERNAME:
        raise RuntimeError("Wrong Instagram account")
    ig=user["id"]
    ids=[]
    for index,item in enumerate(items,1):
        source=f"https://raw.githubusercontent.com/{REPOSITORY}/{sha}/"+urllib.parse.quote(item["path"],safe="/")
        opts={"is_carousel_item":"true"}
        if item["type"]=="image":
            opts["image_url"]=source
        else:
            opts["media_type"]="VIDEO"
            opts["video_url"]=source
        new=api("POST",f"{ig}/media",token,opts)
        if item["type"] == "video":
            await_ready(token,new["id"],max_seconds=240)
        ids.append(str(new["id"]))
        print(f"Item {index}/8: {item['type']} ready.",flush=True)
    outer=api("POST",f"{ig}/media",token,{"media_type":"CAROUSEL","children":",".join(ids),"caption":manifest["caption"]})
    await_ready(token,outer["id"])
    print("PASS: All 8 final item containers and their carousel container created.",flush=True)
    print("NOT PUBLISHED: media_publish was never called.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {str(e)[:650]}",file=sys.stderr)
        sys.exit(1)
