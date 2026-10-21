#!/usr/bin/env python3
"""Riattacca "Migliora voce" ai segmenti, prendendolo da un backup del progetto.

CapCut, aprendo un progetto con i media mancanti, toglie l'elaborazione della voce:
i materiali `vocal_beautifys` spariscono e i segmenti perdono il riferimento. Il
montaggio resta, ma all'apertura successiva la voce non e' piu' quella elaborata.
Qui si rimette, abbinando i segmenti per file e punto nella sorgente.
"""
import copy, json, os, pathlib, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut as cc

def principale(d):
    return next(t for t in d["tracks"] if t["type"] == "video" and t.get("flag", 0) == 0)

def chiave(seg, vids):
    v = vids.get(seg["material_id"], {})
    return (pathlib.Path(v.get("path", "")).name, seg["source_timerange"]["start"])

def main(progetto, backup):
    cart = cc.trova(progetto)
    cc.serve_chiuso(cart)
    b = json.load(open(backup, encoding="utf-8"))
    bvids = {v["id"]: v for v in b["materials"]["videos"]}
    bidx = {m["id"]: m for m in b["materials"].get("vocal_beautifys", [])}
    sorgente = {}
    for s in principale(b)["segments"]:
        for r in s.get("extra_material_refs", []):
            if r in bidx:
                sorgente[chiave(s, bvids)] = bidx[r]
    if not sorgente:
        sys.exit("il backup non ha vocal_beautifys sulla traccia principale")

    messi = 0
    for f in cc.copie(cart):
        d = json.load(open(f, encoding="utf-8"))
        vids = {v["id"]: v for v in d["materials"]["videos"]}
        d["materials"].setdefault("vocal_beautifys", [])
        presenti = {m["id"] for m in d["materials"]["vocal_beautifys"]}
        for s in principale(d)["segments"]:
            if any(r in presenti for r in s.get("extra_material_refs", [])):
                continue
            orig = sorgente.get(chiave(s, vids))
            if orig is None:
                continue
            m = copy.deepcopy(orig); m["id"] = str(uuid.uuid4()).upper()
            d["materials"]["vocal_beautifys"].append(m)
            s["extra_material_refs"].append(m["id"])
            messi += 1
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
    copie = len(cc.copie(cart))
    print(f"{progetto[:44]:46s} voce rimessa su {messi//copie} segmenti")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
