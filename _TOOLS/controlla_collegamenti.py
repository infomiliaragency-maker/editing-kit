#!/usr/bin/env python3
"""Controlla che ogni segmento del parlato punti ancora al file giusto, confrontandolo con un backup.

  python3 controlla_collegamenti.py "<progetto>" --backup <cartella _BACKUP_CAPCUT_...>

Il dialogo "Link media" di CapCut può agganciare un materiale al file sbagliato: su un video, ricollegando
il girato, IMG_1278 è finito su IMG_1270.MOV. Tempi e punti di attacco
restano giusti, quindi capcut.py stato non se ne accorge: il segmento riproduce un'altra ripresa agli stessi tempi e
CapCut gli toglie "Migliora voce". Va lanciato dopo ogni Link media.

I segmenti si abbinano per punto e durata nella sorgente. "senza corrispondenza" sono i segmenti che nel backup non
c'erano (outro, tagli rifatti a mano): non sono errori, ma vanno guardati se sono tanti.
"""
import argparse, json, os, pathlib, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut as cc

N = lambda s: unicodedata.normalize("NFC", s)


def segmenti(d):
    vids = {v["id"]: v for v in d["materials"]["videos"]}
    return [(N(pathlib.Path(vids[s["material_id"]].get("path", "")).name), s["source_timerange"]["start"],
             s["source_timerange"]["duration"], s["target_timerange"]["start"])
            for s in sorted(cc.principale(d)["segments"], key=lambda s: s["target_timerange"]["start"])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("progetto"); ap.add_argument("--backup", required=True)
    a = ap.parse_args()
    cart = cc.trova(a.progetto)
    prima = {}
    for nome, s0, sd, _ in segmenti(json.load(open(os.path.join(a.backup, "draft_info.json")))):
        prima.setdefault((s0, sd), set()).add(nome)
    sbagliati = senza = 0
    for f in cc.copie(cart):
        for nome, s0, sd, t0 in segmenti(json.load(open(f))):
            if (s0, sd) not in prima:
                senza += f.endswith("/draft_info.json") and "Timelines" not in f
            elif nome not in prima[(s0, sd)]:
                sbagliati += 1
                print(f"{f.replace(cart, '.')}: {t0/1e6:8.3f} s punta a {nome}, nel backup era {sorted(prima[(s0, sd)])}")
    print(f"segmenti con il file sbagliato (somma sulle copie): {sbagliati} | senza corrispondenza nel backup: {senza}")
    sys.exit(1 if sbagliati else 0)


if __name__ == "__main__":
    main()
