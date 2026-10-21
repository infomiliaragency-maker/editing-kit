#!/usr/bin/env python3
"""Riporta i b-roll sulle frasi del piano dopo che i tagli sono cambiati.

  python3 riallinea_broll.py "<progetto>" --piano <piano_broll.json> --riferimento <backup> [--traccia "b-roll"]
                             [--spostati-da-claude CLIP1,CLIP2] [--scrivi --dest <cartella video>]

Quando l'utente ritocca i tagli in CapCut la traccia dei b-roll non si sposta. Su un video
un taglio allungato di 4 fotogrammi ha lasciato tutti i b-roll successivi 4 fotogrammi in anticipo sulla loro frase, e
dove un b-roll finiva su un taglio si vedeva il volto per qualche fotogramma prima del salto.

--riferimento è il backup con i tagli su cui è stato fatto il piano (di solito _BACKUP_CAPCUT_prima-broll_*).
Per ogni b-roll il tratto del piano si porta nel punto della ripresa che copriva, e da lì nella timeline di adesso.
Un confine che nel piano stava su un taglio resta sul taglio corrispondente; uno che cade entro 0,2 s da un taglio va
sul taglio. Durata e tratto della clip seguono la frase: se la frase si è allungata oltre la clip, lo si segnala.

Un b-roll che non sta più dove l'aveva messo il piano l'ha spostato l'utente e non si tocca, salvo quelli elencati in
--spostati-da-claude (riallineati a mano in una sessione precedente). Senza --scrivi mostra soltanto.
Con --scrivi: CapCut chiuso, backup nella cartella del video, tutte e sei le copie.
"""
import argparse, json, os, pathlib, subprocess, sys, time, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut as cc

FR = 1 / 30
N = lambda s: unicodedata.normalize("NFC", s)
nome = lambda v: N(pathlib.Path(v.get("path", "")).name)
fot = lambda t: round(t / FR) * FR


def parlato(d):
    vids = {v["id"]: v for v in d["materials"]["videos"]}
    out = []
    for s in sorted(cc.principale(d)["segments"], key=lambda s: s["target_timerange"]["start"]):
        v = vids[s["material_id"]]
        if s.get("volume", 1.0) == 0:          # l'outro
            continue
        t0, td = s["target_timerange"]["start"] / 1e6, s["target_timerange"]["duration"] / 1e6
        s0, sd = s["source_timerange"]["start"] / 1e6, s["source_timerange"]["duration"] / 1e6
        out.append({"file": nome(v), "t0": t0, "t1": t0 + td, "s0": s0, "s1": s0 + sd, "v": s.get("speed", 1.0) or 1.0})
    return out


def corrispondente(r, cur):
    """Il segmento di adesso che viene dalla stessa presa: stesso file, sorgente più sovrapposta."""
    cand = [(min(c["s1"], r["s1"]) - max(c["s0"], r["s0"]), c) for c in cur if c["file"] == r["file"]]
    cand = [x for x in cand if x[0] > 0]
    return max(cand, key=lambda x: x[0])[1] if cand else None


def porta(t, lato, rif, cur):
    """Un confine del piano (tempo nella timeline di riferimento) nella timeline di adesso."""
    for r in rif:
        if lato == "inizio" and abs(t - r["t0"]) < 0.02 or lato == "fine" and abs(t - r["t1"]) < 0.02:
            c = corrispondente(r, cur)
            return (c["t0"] if lato == "inizio" else c["t1"]) if c else None, "taglio"
    for r in rif:
        if r["t0"] <= t <= r["t1"]:
            s = r["s0"] + (t - r["t0"]) * r["v"]
            for c in cur:
                if c["file"] == r["file"] and c["s0"] <= s <= c["s1"]:
                    return c["t0"] + (s - c["s0"]) / c["v"], "parola"
            c = corrispondente(r, cur)
            if c is None:
                return None, "frase tolta"
            return (c["t0"] if s < c["s0"] else c["t1"]), "frase accorciata"
    return None, "fuori dal parlato"


def piano_nuovo(d, piano, rif, gia_spostati):
    cur = parlato(d)
    tagli = sorted({c["t0"] for c in cur} | {c["t1"] for c in cur})
    vids = {v["id"]: v for v in d["materials"]["videos"]}
    broll = sorted([s for t in d["tracks"] if t["type"] == "video" and t.get("flag", 0) != 0 for s in t["segments"]],
                   key=lambda s: s["target_timerange"]["start"])
    usate = {}
    righe = []
    for s in broll:
        clip = nome(vids[s["material_id"]])
        voci = [p for p in piano if N(p["clip"]) == clip]
        k = usate.get(clip, 0); usate[clip] = k + 1
        if k >= len(voci):
            righe.append({"seg": s, "clip": clip, "stato": "non è nel piano: lasciato"}); continue
        p = voci[k]
        t0, t1 = s["target_timerange"]["start"] / 1e6, (s["target_timerange"]["start"] + s["target_timerange"]["duration"]) / 1e6
        intatto = abs(t0 - fot(p["da"])) < 0.035 and abs(t1 - fot(p["a"])) < 0.035
        if not intatto and clip not in gia_spostati:
            righe.append({"seg": s, "clip": clip, "stato": f"spostato a mano ({t0:.3f}-{t1:.3f}, piano {p['da']:.3f}-{p['a']:.3f}): lasciato"})
            continue
        (n0, m0), (n1, m1) = porta(p["da"], "inizio", rif, cur), porta(p["a"], "fine", rif, cur)
        if n0 is None or n1 is None:
            righe.append({"seg": s, "clip": clip, "stato": f"la frase non c'è più ({m0}, {m1}): lasciato"}); continue
        vicino = lambda t: min(tagli, key=lambda c: abs(c - t))
        n0 = vicino(n0) if abs(vicino(n0) - n0) < 0.2 else n0
        n1 = vicino(n1) if abs(vicino(n1) - n1) < 0.2 else n1
        n0, n1 = fot(n0), fot(n1)
        righe.append({"seg": s, "clip": clip, "da": n0, "a": n1, "prima": (t0, t1),
                      "stato": "già a posto" if abs(n0 - t0) < 0.001 and abs(n1 - t1) < 0.001 else "da spostare",
                      "modo": f"{m0}/{m1}"})
    return righe


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("progetto"); ap.add_argument("--piano", required=True); ap.add_argument("--riferimento", required=True)
    ap.add_argument("--spostati-da-claude", default=""); ap.add_argument("--scrivi", action="store_true")
    ap.add_argument("--dest", help="cartella del video per il backup (con --scrivi)")
    a = ap.parse_args()
    cart = cc.trova(a.progetto)
    piano = json.load(open(a.piano)); piano = piano if isinstance(piano, list) else piano["broll"]
    rif = parlato(json.load(open(os.path.join(a.riferimento, "draft_info.json"))))
    gia = {N(x) for x in a.spostati_da_claude.split(",") if x}
    righe = piano_nuovo(json.load(open(f"{cart}/draft_info.json")), piano, rif, gia)
    da_fare = [r for r in righe if r["stato"] == "da spostare"]
    for r in righe:
        if "da" in r:
            print(f"{r['clip'][:34]:34s} {r['prima'][0]:8.3f}-{r['prima'][1]:8.3f} -> {r['da']:8.3f}-{r['a']:8.3f}  {r['stato']} ({r['modo']})")
        else:
            print(f"{r['clip'][:34]:34s} {r['stato']}")
    print(f"{len(da_fare)} b-roll da spostare su {len(righe)}")
    if not a.scrivi or not da_fare:
        return
    cc.serve_chiuso(cart)
    if not a.dest:
        sys.exit("--dest serve per il backup")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "capcut.py"), "backup", cart,
                    "--dest", a.dest, "--etichetta", "prima-di-riallineare-broll"], check=True)
    scritte = []
    for f in cc.copie(cart):
        d = json.load(open(f))
        vids = {v["id"]: v for v in d["materials"]["videos"]}
        fatti = 0
        for t in d["tracks"]:
            if t["type"] != "video" or t.get("flag", 0) == 0:
                continue
            for s in t["segments"]:
                t0 = s["target_timerange"]["start"] / 1e6
                r = next((r for r in da_fare if r["clip"] == nome(vids[s["material_id"]]) and abs(r["prima"][0] - t0) < 0.001), None)
                if r is None:
                    continue
                dur = int(round((r["a"] - r["da"]) * 1e6))
                v = vids[s["material_id"]]
                if s["source_timerange"]["start"] + dur > v["duration"]:
                    sys.exit(f"{r['clip']}: la frase ora dura {dur/1e6:.3f} s e la clip non basta, niente scritto")
                s["target_timerange"] = {"start": int(round(r["da"] * 1e6)), "duration": dur}
                s["source_timerange"]["duration"] = dur
                fatti += 1
            t["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        if fatti != len(da_fare):
            sys.exit(f"{f}: trovo {fatti} b-roll da spostare invece di {len(da_fare)}, niente scritto")
        scritte.append((f, d))
    for f, d in scritte:
        json.dump(d, open(f, "w"), ensure_ascii=False)
    print(f"spostati {len(da_fare)} b-roll in {len(cc.copie(cart))} copie")


if __name__ == "__main__":
    main()
