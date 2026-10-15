"""Publish one approved story; persist intent before any publish request."""
import json, os, subprocess, sys, hashlib
from pathlib import Path
from publish_instagram_carousel import api, await_ready, EXPECTED_USERNAME

root=Path.cwd().resolve()
p=(root/sys.argv[1]).resolve()
if not p.is_relative_to(root) or p.name != 'instagram-story.json':
    raise ValueError('Invalid manifest path')
m=json.loads(p.read_text())
if m['status']!='approved' or m['username']!=EXPECTED_USERNAME:
    raise ValueError('Not approved for expected account')
v=(root/m['path']).resolve()
if not v.is_relative_to(root) or hashlib.sha256(v.read_bytes()).hexdigest()!=m['sha256']:
    raise ValueError('Media mismatch')
r=p.with_name('instagram-story-published.json')
if r.exists():
    raise RuntimeError('Receipt or pending attempt exists; refusing duplicate publication')
token=os.environ['INSTAGRAM_GRAPH_TOKEN']
identity=api('GET','me?fields=id,username',token)
if identity['username']!=EXPECTED_USERNAME: raise ValueError('Wrong account')
uid=identity['id']
sha=os.environ['GITHUB_SHA']
url=f'https://raw.githubusercontent.com/tateishiaoremi-crypto/nora-golf-lab-media/{sha}/{m["path"]}'
created=api('POST',f'{uid}/media',token,{'media_type':'STORIES','video_url':url})
cid=created['id']
await_ready(token,cid)
receipt={'status':'publishing','container_id':cid,'source_commit':sha,'sha256':m['sha256']}
def save():
    r.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    subprocess.run(['git','add',str(r.relative_to(root))],check=True)
    subprocess.run(['git','commit','-m','Record Instagram story publication state [skip ci]'],check=True)
    subprocess.run(['git','push','origin','HEAD:main'],check=True)
save()
# No retries after this request: a lost response requires checking the account.
result=api('POST',f'{uid}/media_publish',token,{'creation_id':cid})
mid=result['id']
receipt.update(status='published',instagram_media_id=mid)
save()
info=api('GET',f'{mid}?fields=id,media_type,media_product_type,permalink',token)
receipt['verification']=info
receipt['permalink']=info.get('permalink') or f'https://www.instagram.com/stories/{EXPECTED_USERNAME}/{mid}/'
save()
print('PUBLISHED_AND_VERIFIED '+json.dumps(receipt,ensure_ascii=False))
