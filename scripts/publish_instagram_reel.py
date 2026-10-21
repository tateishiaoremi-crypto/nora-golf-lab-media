"""Publish an approved Reel using the existing Instagram Login connection."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from urllib.parse import quote
from publish_instagram_carousel import api,await_ready,EXPECTED_USERNAME,REPOSITORY

root=Path.cwd().resolve()
p=(root/sys.argv[1]).resolve()
if not p.is_relative_to(root) or p.name!='instagram-reel.json':
    raise ValueError('Invalid manifest path')
m=json.loads(p.read_text())
if m.get('status')!='approved' or m.get('username')!=EXPECTED_USERNAME:
    raise ValueError('Manifest not approved for expected account')
if not 0<len(m.get('caption',''))<=2200:
    raise ValueError('Invalid caption')
for key in ('video','cover'):
    f=(root/m[key]['path']).resolve()
    if not f.is_relative_to(root) or hashlib.sha256(f.read_bytes()).hexdigest()!=m[key]['sha256']:
        raise ValueError('Approved asset hash mismatch')
r=p.with_name('instagram-reel-published.json')
if r.exists():
    raise RuntimeError('Receipt or pending attempt exists; refusing duplicate publication')
token=os.environ['INSTAGRAM_GRAPH_TOKEN']
identity=api('GET','me?fields=id,username',token)
if identity.get('username')!=EXPECTED_USERNAME:
    raise ValueError('Wrong Instagram account')
uid=identity['id']
sha=os.environ['GITHUB_SHA']
def url(key):
    return f'https://raw.githubusercontent.com/{REPOSITORY}/{sha}/'+quote(m[key]['path'],safe='/')
created=api('POST',f'{uid}/media',token,{
    'media_type':'REELS','video_url':url('video'),'cover_url':url('cover'),
    'caption':m['caption'],'share_to_feed':'true'
})
cid=created['id']
print('Reel container created; waiting for processing',flush=True)
await_ready(token,cid)
receipt={'status':'publishing','container_id':cid,'source_commit':sha,
         'video_sha256':m['video']['sha256'],'cover_sha256':m['cover']['sha256']}
def save():
    r.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    subprocess.run(['git','add',str(r.relative_to(root))],check=True)
    subprocess.run(['git','commit','-m','Record Instagram reel publication state [skip ci]'],check=True)
    subprocess.run(['git','pull','--rebase','origin','main'],check=True)
    subprocess.run(['git','push','origin','HEAD:main'],check=True)
save()
# Never automatically retry publication after a lost response.
result=api('POST',f'{uid}/media_publish',token,{'creation_id':cid})
receipt.update(status='published',instagram_media_id=result['id'])
save()
info=api('GET',f"{result['id']}?fields=id,media_type,media_product_type,permalink,caption",token)
receipt.update(verification=info,permalink=info.get('permalink',''))
save()
print('PUBLISHED_AND_VERIFIED '+json.dumps(receipt,ensure_ascii=False),flush=True)
