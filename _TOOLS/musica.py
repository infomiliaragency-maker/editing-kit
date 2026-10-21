# -*- coding: utf-8 -*-
"""Musica di sottofondo originale generata su fal (Stable Audio 2.5), strumentale, senza diritti di terzi.

  python3 musica.py --prompt "..." --durata 80 --out <cartella>/musica_a.wav [--seme 7]

La chiave fal si legge con chiavi.py, come negli altri strumenti.
"""
import argparse, json, sys
import genera_broll as g

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--prompt", required=True); ap.add_argument("--durata", type=int, default=80)
ap.add_argument("--out", required=True); ap.add_argument("--seme", type=int)
a = ap.parse_args()
corpo = {"prompt": a.prompt, "seconds_total": a.durata}
if a.seme is not None:
    corpo["seed"] = a.seme
r = g.coda("fal-ai/stable-audio-25/text-to-audio", corpo)
url = (r.get("audio") or r.get("audio_file") or {}).get("url")
if not url:
    sys.exit("risposta senza audio: " + json.dumps(r)[:400])
g.scarica(url, a.out)
