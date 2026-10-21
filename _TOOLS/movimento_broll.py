# -*- coding: utf-8 -*-
"""Quanto si muove una clip b-roll. Una clip ferma, sopra il parlato, sembra una fotografia.

  python3 movimento_broll.py clip1.mp4 [clip2.mp4 ...] [--da 0.5 --durata 4]

Misura: differenza media fra fotogrammi consecutivi (ffmpeg tblend difference, luminanza media 0-255).
Riferimenti misurati con questo strumento su una libreria b-roll vera:
  sotto 1        sembra una foto, bocciata (clip misurate 0.37 e 0.06)
  1-3            movimento lento, usabile solo in brevi stacchi (1.12)
  oltre 4        si muove davvero (7.80, 14.43)
Si misura il tratto che finisce nel montaggio (--da, --durata), non la clip intera.
"""
import argparse, os, re, shutil, subprocess

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("clip", nargs="+"); ap.add_argument("--da", type=float, default=0); ap.add_argument("--durata", type=float, default=0)
a = ap.parse_args()
for c in a.clip:
    cmd = [FF, "-nostdin", "-hide_banner", "-ss", str(a.da)] + (["-t", str(a.durata)] if a.durata else []) + [
        "-i", c, "-vf", "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
        "-an", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    v = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", err)]
    if not v:
        print(f"{os.path.basename(c)}: misura non riuscita"); continue
    m = sum(v) / len(v)
    giudizio = "sembra una foto" if m < 1 else ("lenta" if m < 3 else ("si muove poco" if m < 4 else "si muove"))
    print(f"{os.path.basename(c):48s} movimento {m:6.2f}  {giudizio}")
