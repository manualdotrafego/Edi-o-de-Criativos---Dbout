import subprocess, os, zipfile
from PIL import Image, ImageDraw, ImageFont

FFMPEG   = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE  = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FONT_TTF = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
DL       = "/Users/alexrangelalves/Downloads"

cities = [
    ("SANTO ANDRÉ",   "santo_andre"),
    ("SÃO BERNARDO",  "sao_bernardo"),
    ("OSASCO",        "osasco"),
    ("SANTA BÁRBARA", "santa_barbara"),
    ("BARBACENA",     "barbacena"),
]

templates = [
    ("21-mar.MOV",     "21mar",   False),
    ("02 jan26.mp4",   "02jan26", False),
    ("24-mar.MOV",     "24mar",   True),
    ("[2 - FEV] .mp4", "2fev",    False),
    ("17 - MAR.MOV",   "17mar",   False),
]

narrations = {
    "santo_andre":   "Atenção Santo André! Últimas 3 vagas para por aparelho dental! com vários benefícios inclusos pagando apenas a mensalidade! Clique agora no link e reserve sua vaga antes que acabe.",
    "sao_bernardo":  "Atenção São Bernardo! Últimas 3 vagas para por aparelho dental! com vários benefícios inclusos pagando apenas a mensalidade! Clique agora no link e reserve sua vaga antes que acabe.",
    "osasco":        "Atenção Osasco! Últimas 3 vagas para por aparelho dental! com vários benefícios inclusos pagando apenas a mensalidade! Clique agora no link e reserve sua vaga antes que acabe.",
    "santa_barbara": "Atenção Santa Bárbara! Últimas 3 vagas para por aparelho dental! com vários benefícios inclusos pagando apenas a mensalidade! Clique agora no link e reserve sua vaga antes que acabe.",
    "barbacena":     "Atenção Barbacena! Últimas 3 vagas para por aparelho dental! com vários benefícios inclusos pagando apenas a mensalidade! Clique agora no link e reserve sua vaga antes que acabe.",
}

def get_video_size(path):
    r = subprocess.run([FFPROBE,"-v","error","-show_entries","stream=width,height",
        "-of","csv=p=0", path], capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)

def build_overlay(city, vw, vh, out_png):
    scale  = vh / 1920.0
    fs     = max(36, int(90 * scale))
    pad_x  = int(38 * scale); pad_y = int(20 * scale)
    radius = int(35 * scale); shadow = max(3, int(6 * scale))
    y_city = int(170 * scale)
    font   = ImageFont.truetype(FONT_TTF, fs)
    bb     = font.getbbox(city)
    px_w   = bb[2] - bb[0]
    draw_x = (vw - px_w) // 2 - bb[0]
    draw_y = y_city + pad_y - bb[1]
    bx0    = draw_x + bb[0] - pad_x; by0 = draw_y + bb[1] - pad_y
    bx1    = draw_x + bb[2] + pad_x; by1 = draw_y + bb[3] + pad_y
    img    = Image.new("RGBA", (vw, vh), (0,0,0,0))
    draw   = ImageDraw.Draw(img)
    draw.rounded_rectangle([bx0+shadow,by0+shadow,bx1+shadow,by1+shadow], radius=radius, fill=(0,0,0,90))
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
    words = narration.strip().split()
    def ww(w):
        base = len(w)
        if w[-1] in ".,!?;:": base += 5
        return max(1, base)
    total_w = sum(ww(w) for w in words)
    scale_t = total_dur / total_w
    scale_v = vh / 1920.0
    fs_sub  = max(28, int(52 * scale_v))
    mv      = int(750 * scale_v)
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

all_outputs = []

for city_label, city_slug in cities:
    print(f"\n🏙️  {city_label}")
    audio     = f"/tmp/{city_slug}.mp3"
    narration = narrations[city_slug]
    city_files = []

    for tpl_file, tpl_slug, reduce_vol in templates:
        tpl_path = f"{DL}/{tpl_file}"
        out_png  = f"/tmp/overlay_{city_slug}_{tpl_slug}.png"
        out_ass  = f"/tmp/sub_{city_slug}_{tpl_slug}.ass"
        out_mp4  = f"/tmp/{tpl_slug}_{city_slug}.mp4"

        vw, vh = get_video_size(tpl_path)
        build_overlay(city_label, vw, vh, out_png)
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

        cmd = [FFMPEG,"-y","-stream_loop","-1","-i", tpl_path,
               "-i", audio, "-i", out_png,
               "-filter_complex", fc,
               "-map","[vout]","-map","[aout]",
               "-c:v","libx264","-preset","fast","-crf","23",
               "-c:a","aac","-b:a","192k","-shortest", out_mp4]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            sz = os.path.getsize(out_mp4)/1024/1024
            print(f"  ✅ {tpl_slug} → {sz:.1f}MB")
            city_files.append(out_mp4)
        else:
            print(f"  ❌ {tpl_slug}: {res.stderr[-300:]}")

    all_outputs.extend(city_files)

# ZIP único
zip_path = f"{DL}/batch_5cidades_templates.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for mp4 in all_outputs:
        zf.write(mp4, os.path.basename(mp4))

print(f"\n📦 {zip_path} ({os.path.getsize(zip_path)/1024/1024:.1f} MB) — {len(all_outputs)} vídeos")
