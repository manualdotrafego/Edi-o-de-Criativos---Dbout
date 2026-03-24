import subprocess, os, shutil
from PIL import Image, ImageDraw, ImageFont

FFMPEG   = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE  = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FONT_TTF = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
DL       = "/Users/alexrangelalves/Downloads"

city  = "PONTA GROSSA"
slug  = "ponta_grossa"
audio = "/tmp/ponta_grossa_v2.mp3"

narration = """Vergonha de sorrir ou dificuldade pra mastigar?
Dentes desalinhados afetam sua autoestima.
O aparelho ortodôntico corrige isso!
Se você está em Ponta Grossa, fale agora no WhatsApp e comece seu tratamento ortodôntico."""

# templates: (filename, slug, reduce_vol)
templates = [
    ("14 - MAR.MOV",   "14mar",  False),
    ("15 - MAR.MOV",   "15mar",  False),
    ("16 - MAR.MOV",   "16mar",  False),
    ("17 - MAR.MOV",   "17mar",  False),
    ("18 - MAR.MOV",   "18mar",  False),
    ("19 - MAR.MOV",   "19mar",  False),
    ("20-mar.MOV",     "20mar",  True),
    ("21-mar.MOV",     "21mar",  True),
    ("22-mar.MOV",     "22mar",  True),
    ("24-mar.MOV",     "24mar",  True),
]

# ── helpers ──────────────────────────────────────────────────────────────
def get_video_size(path):
    r = subprocess.run([FFPROBE,"-v","error","-show_entries","stream=width,height",
        "-of","csv=p=0", path], capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)

def build_overlay(city, vw, vh, out_png):
    scale  = vh / 1920.0
    fs     = max(36, int(90 * scale))
    pad_x  = int(38 * scale)
    pad_y  = int(20 * scale)
    radius = int(35 * scale)
    shadow = max(3, int(6 * scale))
    y_city = int(170 * scale)
    font   = ImageFont.truetype(FONT_TTF, fs)
    bb     = font.getbbox(city)
    px_w   = bb[2] - bb[0]
    draw_x = (vw - px_w) // 2 - bb[0]
    draw_y = y_city + pad_y - bb[1]
    bx0    = draw_x + bb[0] - pad_x
    by0    = draw_y + bb[1] - pad_y
    bx1    = draw_x + bb[2] + pad_x
    by1    = draw_y + bb[3] + pad_y
    img    = Image.new("RGBA", (vw, vh), (0,0,0,0))
    draw   = ImageDraw.Draw(img)
    draw.rounded_rectangle([bx0+shadow,by0+shadow,bx1+shadow,by1+shadow],
                           radius=radius, fill=(0,0,0,90))
    draw.rounded_rectangle([bx0,by0,bx1,by1], radius=radius, fill=(35,35,35,77))
    bw = max(4, int(8*scale))
    for dx in range(-bw, bw+1, 2):
        for dy in range(-bw, bw+1, 2):
            if abs(dx)+abs(dy) >= bw-1:
                draw.text((draw_x+dx, draw_y+dy), city, font=font, fill=(255,255,255,255))
    draw.text((draw_x, draw_y), city, font=font, fill=(255,105,180,255))
    img.save(out_png, "PNG")

def build_ass(narration, audio, vw, vh, out_ass):
    rd = subprocess.run([FFPROBE,"-v","error","-show_entries","format=duration",
        "-of","csv=p=0", audio], capture_output=True, text=True)
    total_dur = float(rd.stdout.strip())
    words = [w for line in narration.strip().split("\n") for w in line.split()]

    def ww(w):
        base = len(w)
        if w[-1] in ".,!?;:": base += 5
        return max(1, base)

    total_w   = sum(ww(w) for w in words)
    scale_t   = total_dur / total_w
    scale_v   = vh / 1920.0
    fs_sub    = max(28, int(52 * scale_v))
    mv        = int(750 * scale_v)

    def fmt(s):
        h=int(s//3600); m=int((s%3600)//60); sec=s%60
        return f"{h}:{m:02d}:{sec:05.2f}"

    ass  = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {vw}\nPlayResY: {vh}\n\n"
    ass += "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
    ass += "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
    ass += (f"Style: Default,Impact,{fs_sub},&H00FFFFFF,&H000000FF,&H00000000,"
            f"&H00000000,-1,0,0,0,100,100,0,0,1,10,0,2,10,10,{mv},1\n\n")
    ass += "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"

    t = 0.0; CHUNK = 4; i = 0
    while i < len(words):
        chunk = words[i:i+CHUNK]
        dur   = sum(ww(w) for w in chunk) * scale_t
        end   = t + dur
        ass  += f"Dialogue: 0,{fmt(t)},{fmt(end)},Default,,0,0,0,,{' '.join(chunk)}\n"
        t = end; i += CHUNK

    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(ass)

# ── render loop ───────────────────────────────────────────────────────────
outputs = []
for tpl_file, tpl_slug, reduce_vol in templates:
    tpl_path = f"{DL}/{tpl_file}"
    out_png  = f"/tmp/overlay_{slug}_{tpl_slug}.png"
    out_ass  = f"/tmp/sub_{slug}_{tpl_slug}.ass"
    out_mp4  = f"/tmp/{tpl_slug}_{slug}.mp4"

    print(f"\n▶ {tpl_file}")
    vw, vh = get_video_size(tpl_path)
    print(f"  Resolução: {vw}x{vh}")

    build_overlay(city, vw, vh, out_png)
    build_ass(narration, audio, vw, vh, out_ass)

    ass_esc = out_ass.replace("\\","\\\\").replace(":","\\:").replace("'","\\'")

    if reduce_vol:
        fc = (f"[0:v][2:v]overlay=0:0[bg];"
              f"[bg]subtitles=filename='{ass_esc}'[vout];"
              f"[0:a]volume=0.3[va];[va][1:a]amix=inputs=2:duration=shortest:dropout_transition=2[aout]")
    else:
        fc = (f"[0:v][2:v]overlay=0:0[bg];"
              f"[bg]subtitles=filename='{ass_esc}'[vout];"
              f"[0:a][1:a]amix=inputs=2:duration=shortest:dropout_transition=2[aout]")

    cmd = [FFMPEG,"-y",
           "-stream_loop","-1","-i", tpl_path,
           "-i", audio,
           "-i", out_png,
           "-filter_complex", fc,
           "-map","[vout]","-map","[aout]",
           "-c:v","libx264","-preset","fast","-crf","23",
           "-c:a","aac","-b:a","192k",
           "-shortest", out_mp4]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        sz = os.path.getsize(out_mp4)/1024/1024
        print(f"  ✅ {out_mp4} ({sz:.1f} MB)")
        outputs.append(out_mp4)
    else:
        print(f"  ❌ ERRO: {res.stderr[-1000:]}")

# ── ZIP ───────────────────────────────────────────────────────────────────
import zipfile
zip_path = f"{DL}/{slug}_v2_templates.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for mp4 in outputs:
        zf.write(mp4, os.path.basename(mp4))

zsize = os.path.getsize(zip_path)/1024/1024
print(f"\n📦 ZIP gerado: {zip_path} ({zsize:.1f} MB) — {len(outputs)} vídeos")
