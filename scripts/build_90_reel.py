#!/usr/bin/env python3
"""Build a 19-second unpublished reel using Menard's actual synchronized video/audio."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json, math, os

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/"posts/2026-10-10-menard/swings.mp4"
OUT=ROOT/"posts/2026-10-31-90-vow"
OUT.mkdir(parents=True,exist_ok=True)
TMP=OUT/"_tmp"; TMP.mkdir(exist_ok=True)
JPFONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REGFONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
W,H=1080,1920
SCENES=[
    (0.0,3.8,"もう絶対に\n90は打たない！"),
    (5.0,3.8,"85も打ちたくない！"),
    (10.0,3.8,"毎回そう誓います。笑"),
    (15.0,3.8,"結果、90。\nOB5。笑"),
    (20.0,3.8,"みんなも\nそんなことない？笑"),
]

def run(cmd):
    subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def font(size,bold=True):
    return ImageFont.truetype(JPFONT if bold else REGFONT,size,index=0)

def multiline_center(draw,lines,y,sz=78,color=(255,255,255,255)):
    for line in lines:
        n=sz
        while draw.textbbox((0,0),line,font=font(n))[2]>W-140 and n>52:
            n-=2
        f=font(n)
        box=draw.textbbox((0,0),line,font=f)
        tw=box[2]-box[0]; hh=box[3]-box[1]
        draw.text(((W-tw)//2,y),line,font=f,fill=color)
        y+=max(hh+32,100)

def overlay_image(text,out_path,cover=False):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    pix=img.load()
    # Gentle graduated shading on the golf video, not a solid black banner.
    for y in range(1260,1800):
        x=(y-1260)/540
        alpha=int(8+65*(math.sin(math.pi*x/2)**2))
        for ix in range(W):
            pix[ix,y]=(0,0,0,alpha)
    d=ImageDraw.Draw(img)
    gold=(203,171,101,255)
    d.text((85,220),"NORA GOLF LAB",font=font(35),fill=gold)
    d.text((85,268),"MENARD AOYAMA  |  2026.10.10",font=font(23,False),fill=(255,255,255,240))
    d.line((85,310,220,310),fill=gold,width=4)
    lines=text.split("\n")
    y=1440 if len(lines)==2 else 1510
    multiline_center(d,lines,y,80)
    img.save(out_path)

def filter_base():
    # The source has an existing header; isolate the original shot area.
    # The same shot supplies a blurred edge-to-edge backdrop, without a black band.
    return "[0:v]crop=720:900:0:230,split=2[ab][bb];[ab]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=42[bg];[bb]scale=1080:1350:flags=lanczos[fg];[bg][fg]overlay=0:285:shortest=1,format=rgba[base];[base][1:v]overlay=0:0:shortest=1,format=yuv420p[v]"

clip_names=[]
for i,(start,dur,txt) in enumerate(SCENES,1):
    png=TMP/f"title-{i}.png"; overlay_image(txt,png)
    clip=TMP/f"segment-{i:02}.mp4"
    clip_names.append(clip)
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",str(SRC),"-ss",str(start),"-t",str(dur),
         "-loop","1","-i",str(png),
         "-filter_complex",filter_base(),"-map","[v]","-map","0:a:0",
         "-r","30","-c:v","libx264","-preset","medium","-crf","20",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-ar","48000",
         "-t",str(dur),"-movflags","+faststart",str(clip)])
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-ss","2.25","-i",str(clip),"-frames:v","1","-q:v","4",
         str(OUT/f"preview-{i:02}.jpg")])

listfile=TMP/"segments.txt"
listfile.write_text("".join("file '"+str(p.resolve())+"'\n" for p in clip_names))
REEL=OUT/"reel.mp4"
run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(listfile),"-c","copy","-movflags","+faststart",str(REEL)])

# Make a distinct cover based on a real mid-swing frame (never black).
coverbase=TMP/"coverbase.jpg"
run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
     "-ss","2.1","-i",str(REEL),"-frames:v","1","-q:v","2",str(coverbase)])
cover=Image.open(coverbase).convert("RGBA")
v=Image.new("RGBA",(W,H),(0,0,0,0))
d=ImageDraw.Draw(v)
d.rectangle([60,1280,1020,1760],fill=(0,0,0,42))
d.text((85,1320),"90はもう打たない。",font=font(76),fill=(255,255,255,255))
d.text((85,1445),"いや、85も。笑",font=font(66),fill=(255,255,255,255))
cover=Image.alpha_composite(cover,v).convert("RGB")
cover.save(OUT/"cover.jpg",quality=90,subsampling=0)

caption="""もう絶対に90は打たない！
いや、85も打ちたくない！

って、毎回そう誓います。笑

それでもメナード青山は90。
OB5。そらそうなるわ。😭

これ、ゴルファーあるあるやと思うんやけど、
みんなもそんなことない？笑

#ゴルフ #ゴルフスイング #ラウンド記録 #メナード青山 #野良ゴルファー #nora_golf_lab #bkndr
"""
(OUT/"caption.txt").write_text(caption,encoding="utf8")

probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(REEL)]))
streams=[{"type":s["codec_type"],"codec":s["codec_name"],"duration":s.get("duration"),"width":s.get("width"),"height":s.get("height")} for s in probe["streams"]]
duration=float(probe["format"]["duration"])
assert 18.7<duration<19.4,(duration,streams)
assert any(s["type"]=="audio" for s in streams)
assert any(s["type"]=="video" and s.get("width")==1080 and s.get("height")==1920 for s in streams)
result={"status":"draft_not_published","source":"posts/2026-10-10-menard/swings.mp4","duration":duration,"video_audio_cut_from_matching_intervals":True,"no_audio_offset_applied":True,"segments":[{"start":start,"duration":dur,"text":txt} for start,dur,txt in SCENES],"streams":streams,"source_has_original_audio":True,"visual_check":"Five frame previews available; human check required"}
(OUT/"qc.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("REEL_DRAFT_READY "+json.dumps(result,ensure_ascii=False))
