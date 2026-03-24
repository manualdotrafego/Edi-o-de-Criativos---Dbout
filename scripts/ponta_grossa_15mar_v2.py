import subprocess, os
from PIL import Image, ImageDraw, ImageFont

FFMPEG  = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"
FONT_TTF = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

template = "/Users/alexrangelalves/Downloads/15 - MAR.MOV"
audio    = "/tmp/ponta_grossa.mp3"
city     = "PONTA GROSSA"
slug     = "ponta_grossa"
out_mp4  = f"/tmp/15mar_{slug}_v2.mp4"
out_png  = f"/tmp/overlay_{slug}.png"   # já existe, reutiliza
out_ass  = f"/tmp/sub_{slug}_v2.ass"

vw, vh = 1080, 1920

# ── Subtitles (ASS) — legenda mais acima ──────────────────────────────────
narration = """Você evita sorrir em fotos? Ou sente dificuldade até pra mastigar por causa dos dentes desalinhados?
Isso pode afetar sua autoestima e sua rotina mais do que parece.
O aparelho ortodôntico, com acompanhamento profissional, pode ajudar na função e na harmonia do seu sorriso. Cada caso é único.
Se você está em Ponta Grossa, não adie mais.
Clique agora e fale com a gente no WhatsApp para agendar sua avaliação."""

rd = subprocess.run([FFPROBE,"-v","error","-show_entries","format=duration",
    "-of","csv=p=0", audio], capture_output=True, text=True)
total_dur = float(rd.stdout.strip())

words = []
for line in narration.strip().split("\n"):
    for w in line.split():
        words.append(w)

def word_weight(w):
    base = len(w)
    if w[-1] in ".,!?;:": base += 5
    return max(1, base)

total_weight = sum(word_weight(w) for w in words)
scale_t = total_dur / total_weight

def fmt_ass_time(s):
    h = int(s//3600); m = int((s%3600)//60); sec = s%60
    return f"{h}:{m:02d}:{sec:05.2f}"

scale_v = vh / 1920.0
fs_sub  = max(28, int(52 * scale_v))
mv      = int(750 * scale_v)   # ← subiu de 40 para 750 (próximo ao centro)

ass  = "[Script Info]\nScriptType: v4.00+\nPlayResX: {}\nPlayResY: {}\n\n".format(vw, vh)
ass += "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
ass += "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
ass += (f"Style: Default,Impact,{fs_sub},&H00FFFFFF,&H000000FF,&H00000000,"
        f"&H00000000,-1,0,0,0,100,100,0,0,1,10,0,2,10,10,{mv},1\n\n")
ass += "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"

t = 0.0
CHUNK = 4
i = 0
while i < len(words):
    chunk = words[i:i+CHUNK]
    dur   = sum(word_weight(w) for w in chunk) * scale_t
    end   = t + dur
    text  = " ".join(chunk)
    ass  += f"Dialogue: 0,{fmt_ass_time(t)},{fmt_ass_time(end)},Default,,0,0,0,,{text}\n"
    t     = end
    i    += CHUNK

with open(out_ass, "w", encoding="utf-8") as f:
    f.write(ass)

# ── FFmpeg render ─────────────────────────────────────────────────────────
ass_esc = out_ass.replace("\\","\\\\").replace(":","\\:").replace("'","\\'")

fc = (f"[0:v][2:v]overlay=0:0[bg];"
      f"[bg]subtitles=filename='{ass_esc}'[vout];"
      f"[0:a][1:a]amix=inputs=2:duration=shortest:dropout_transition=2[aout]")

cmd = [FFMPEG,"-y",
       "-stream_loop","-1","-i", template,
       "-i", audio,
       "-i", out_png,
       "-filter_complex", fc,
       "-map","[vout]","-map","[aout]",
       "-c:v","libx264","-preset","fast","-crf","23",
       "-c:a","aac","-b:a","192k",
       "-shortest", out_mp4]

print("Renderizando...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size = os.path.getsize(out_mp4) / 1024 / 1024
    print(f"✅ {out_mp4} ({size:.1f} MB)")
    import shutil
    shutil.copy(out_mp4, "/Users/alexrangelalves/Downloads/15mar_ponta_grossa.mp4")
    print("📁 Copiado para Downloads")
else:
    print("❌ ERRO:", result.stderr[-2000:])
