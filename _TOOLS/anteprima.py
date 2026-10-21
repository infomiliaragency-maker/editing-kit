# -*- coding: utf-8 -*-
"""Anteprima a 540p di un progetto CapCut, resa con ffmpeg: girato, b-roll sopra, sottotitoli, audio esatto.

  python3 anteprima.py <progetto> --out ANTEPRIMA_540p.mp4 --stile-ass <intestazione .ass> [--font-dir <dir>] [--fino 20]
  python3 anteprima.py <progetto> --out ANTEPRIMA_broll-v2.mp4 --stile-ass <.ass> --piano piano_broll.json --cartella-clip <dir> [--traccia "b-roll"]

Serve a controllare tagli, b-roll e tempi senza aprire CapCut. Color e Migliora voce li applica
solo CapCut: qui l'audio è quello grezzo.
L'audio si ricostruisce in PCM segmento per segmento alla durata esatta della timeline e si rimette sul video alla
fine: concatenare pezzi AAC sposta i sottotitoli di decimi di secondo verso la fine.
--stile-ass è un file .ass con [Script Info] e [V4+ Styles]: si usa il primo stile, centrato a --pos-y (1920 righe).
--fino limita l'anteprima ai primi N secondi, per le prove.
--piano mostra un piano b-roll non ancora scritto: la traccia --traccia del progetto viene ignorata e al suo posto vanno
le voci del piano (clip, da, a, offset). Le clip si cercano in --cartella-clip, poi fra i media del progetto. Serve a
controllare b-roll nuovi prima di importarli in CapCut.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut import trova, principale  # noqa: E402

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("progetto"); ap.add_argument("--out", required=True); ap.add_argument("--stile-ass", required=True)
ap.add_argument("--font-dir", default=os.path.expanduser("~/Library/Fonts")); ap.add_argument("--pos-y", type=int, default=1240)
ap.add_argument("--fino", type=float, default=0)
ap.add_argument("--piano"); ap.add_argument("--cartella-clip", default=""); ap.add_argument("--traccia", default="b-roll")
a = ap.parse_args()

cart = trova(a.progetto)
d = json.load(open(f"{cart}/draft_info.json"))
vids = {v["id"]: v for v in d["materials"]["videos"]}
vel = {s["id"]: s["speed"] for s in d["materials"].get("speeds", [])}
mp = principale(d)
lav = tempfile.mkdtemp(prefix="anteprima_")
run = lambda c: subprocess.run([FF, "-nostdin", "-v", "error", "-y"] + c, check=True)
limite = a.fino * 1e6 if a.fino else float("inf")

video, audio = [], []
for i, s in enumerate(sorted(mp["segments"], key=lambda x: x["target_timerange"]["start"])):
    if s["target_timerange"]["start"] >= limite:
        break
    m = vids[s["material_id"]]; sr = s["source_timerange"]; D = s["target_timerange"]["duration"] / 1e6
    v = next((vel[r] for r in s["extra_material_refs"] if r in vel), s.get("speed", 1.0)) or 1.0
    ss = f"{sr['start']/1e6:.6f}"
    vo, ao = f"{lav}/v{i:03d}.mp4", f"{lav}/a{i:03d}.wav"
    run(["-ss", ss, "-i", m["path"], "-an", "-vf",
         f"trim=duration={sr['duration']/1e6:.6f},setpts=(PTS-STARTPTS)/{v},scale=540:960,fps=30,setsar=1,trim=duration={D:.6f}",
         "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", vo])
    if m.get("has_audio"):
        run(["-ss", ss, "-i", m["path"], "-vn", "-af",
             f"atrim=duration={sr['duration']/1e6:.6f},asetpts=N/SR/TB,atempo={v},apad,atrim=duration={D:.6f}",
             "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", ao])
    else:
        run(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{D:.6f}", "-c:a", "pcm_s16le", ao])
    video.append(vo); audio.append(ao)
for nome, lista in (("v", video), ("a", audio)):
    open(f"{lav}/{nome}.txt", "w").write("\n".join(f"file '{p}'" for p in lista))
run(["-f", "concat", "-safe", "0", "-i", f"{lav}/v.txt", "-c", "copy", f"{lav}/base.mp4"])
run(["-f", "concat", "-safe", "0", "-i", f"{lav}/a.txt", "-c:a", "pcm_s16le", f"{lav}/audio.wav"])

ingressi, filtri, prev = [], [], "[0:v]"
sopra = [t for t in d["tracks"] if t["type"] == "video" and t is not mp and not (a.piano and t.get("name") == a.traccia)]
# ogni voce: (file, offset nella clip, inizio in timeline, durata), in secondi
voci = [(vids[s["material_id"]]["path"], s["source_timerange"]["start"] / 1e6, s["target_timerange"]["start"] / 1e6,
         s["target_timerange"]["duration"] / 1e6) for t in sopra for s in t["segments"]]
if a.piano:
    percorsi = {os.path.basename(v["path"]): v["path"] for v in d["materials"]["videos"]}
    for x in json.load(open(a.piano)):
        p = os.path.join(a.cartella_clip, x["clip"])
        p = p if os.path.exists(p) else percorsi.get(x["clip"])
        if not p:
            sys.exit(f"{x['clip']}: non è in {a.cartella_clip} né fra i media del progetto")
        voci.append((p, x.get("offset", 0), x["da"], x["a"] - x["da"]))
segs = sorted([v for v in voci if v[2] * 1e6 < limite], key=lambda v: v[2])
for j, (percorso, off, t0, durata) in enumerate(segs):
    t1 = t0 + durata
    ingressi += ["-ss", f"{off:.3f}", "-t", f"{durata:.3f}", "-i", percorso]
    filtri.append(f"[{j+1}:v]scale=540:960,fps=30,setsar=1,setpts=PTS-STARTPTS+{t0}/TB[b{j}]")
    filtri.append(f"{prev}[b{j}]overlay=enable='between(t,{t0},{t1})'[v{j}]"); prev = f"[v{j}]"

righe = open(a.stile_ass).read().rstrip("\n").split("\n")
stile = next((l.split(":", 1)[1].split(",")[0].strip() for l in righe if l.startswith("Style:")), "Default")
if not any(l.startswith("[Events]") for l in righe):
    righe += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
testi = {m["id"]: m for m in d["materials"].get("texts", [])}
tc = lambda t: f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
for t in d["tracks"]:
    if t["type"] != "text":
        continue
    for s in t["segments"]:
        x0 = s["target_timerange"]["start"] / 1e6; x1 = x0 + s["target_timerange"]["duration"] / 1e6
        if x0 * 1e6 >= limite or s["material_id"] not in testi:
            continue
        testo = json.loads(testi[s["material_id"]]["content"])["text"].replace(" \n", "\\N").replace("\n", "\\N")
        righe.append(f"Dialogue: 0,{tc(x0)},{tc(x1)},{stile},,0,0,0,,{{\\an5\\pos(540,{a.pos_y})}}{testo}")
open(f"{lav}/sottotitoli.ass", "w").write("\n".join(righe) + "\n")
filtri.append(f"{prev}scale=1080:1920,ass={lav}/sottotitoli.ass:fontsdir={a.font_dir},scale=540:960[vout]")
run(["-i", f"{lav}/base.mp4"] + ingressi + ["-i", f"{lav}/audio.wav", "-filter_complex", ";".join(filtri),
     "-map", "[vout]", "-map", f"{len(segs)+1}:a", "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "160k", "-shortest", a.out])
shutil.rmtree(lav)
print("anteprima in", a.out)
