"""Effetti sonori su una traccia audio di un progetto CapCut, scritti dal file.

  python3 sfx.py elenco  --da-progetto "<progetto che li usa già>"
  python3 sfx.py scrivi  <progetto> --piano piano_sfx.json --da-progetto "<progetto>" [--traccia Effetti]

Gli effetti sono quelli della libreria di CapCut: il file sta già nella sua cache, quindi non c'è niente
da importare dall'interfaccia. Il materiale però esiste solo dentro i progetti che lo usano, quindi lo
si copia da un progetto di riferimento: `--da-progetto "<un tuo reel>"` prende gli effetti che usi già
(per esempio "Woosh", "Metallic Riser", "Swish"), con i volumi che hai messo lì.

piano_sfx.json, tempi in secondi sulla timeline montata:

  [{"effetto": "Woosh", "da": 21.72},
   {"effetto": "Metallic Riser", "da": 52.14, "volume": 0.45}]

Senza "volume" si usa quello del progetto di riferimento. Con CapCut chiuso, su tutte e sei le copie,
dopo un backup fatto da chi chiama. Rilanciarlo è sicuro: rifà la traccia da zero.
"""
import argparse, copy, json, os, subprocess, sys, uuid

PROGETTI = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
FPS_US = 1e6 / 30


def uid():
    return str(uuid.uuid4()).upper()


def cartella_progetto(nome):
    if os.path.isdir(nome):
        return nome
    p = os.path.join(PROGETTI, nome)
    if os.path.isdir(p):
        return p
    sys.exit(f"progetto non trovato: {nome}")


def copie(cart):
    out = [os.path.join(cart, n) for n in ("draft_info.json", "draft_info.json.bak", "template-2.tmp")]
    tl = os.path.join(cart, "Timelines")
    if os.path.isdir(tl):
        for d in os.listdir(tl):
            out += [os.path.join(tl, d, n) for n in ("draft_info.json", "draft_info.json.bak", "template-2.tmp")]
    return [f for f in out if os.path.exists(f)]


def libreria(nome_progetto):
    """{nome effetto: (materiale, volume, extra_material_refs modello)} da un progetto che li usa"""
    cart = cartella_progetto(nome_progetto)
    d = json.load(open(os.path.join(cart, "draft_info.json")))
    aud = {m["id"]: m for m in d["materials"].get("audios", [])}
    extra = {k: {m["id"]: m for m in l} for k, l in d["materials"].items() if isinstance(l, list)}
    out = {}
    for t in d["tracks"]:
        if t["type"] != "audio":
            continue
        for s in t["segments"]:
            m = aud.get(s["material_id"])
            if not m or m.get("type") != "sound" or m.get("name") in out:
                continue
            modelli = []
            for i in s.get("extra_material_refs", []):
                for k, mm in extra.items():
                    if i in mm:
                        modelli.append((k, mm[i]))
                        break
            out[m["name"]] = (m, s.get("volume", 0.7), modelli)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comando", choices=["elenco", "scrivi"])
    ap.add_argument("progetto", nargs="?")
    ap.add_argument("--piano")
    ap.add_argument("--da-progetto", required=True)
    ap.add_argument("--traccia", default="Effetti")
    a = ap.parse_args()

    lib = libreria(a.da_progetto)
    if a.comando == "elenco":
        for n, (m, vol, _) in lib.items():
            c = "c'è" if os.path.exists(m["path"]) else "MANCA in cache"
            print(f"  {n:18} {m['duration']/1e6:5.2f}s  volume {vol}  {c}")
        return

    if not a.progetto or not a.piano:
        sys.exit("servono il progetto e --piano")
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        sys.exit("CapCut è aperto: va chiuso prima di scrivere")

    piano = json.load(open(a.piano))
    for v in piano:
        if v["effetto"] not in lib:
            sys.exit(f"effetto {v['effetto']!r} non c'è nel progetto di riferimento. Quelli che ci sono: {list(lib)}")
        p = lib[v["effetto"]][0]["path"]
        if not os.path.exists(p):
            sys.exit(f"il file di {v['effetto']!r} non è nella cache di CapCut: {p}")

    cart = cartella_progetto(a.progetto)
    for f in copie(cart):
        d = json.load(open(f))
        vecchia = next((t for t in d["tracks"] if t["type"] == "audio" and t.get("name") == a.traccia), None)
        if vecchia is not None:
            vecchi = set()
            for s in vecchia["segments"]:
                vecchi.add(s["material_id"]); vecchi.update(s.get("extra_material_refs", []))
            d["tracks"] = [t for t in d["tracks"] if t is not vecchia]
            for k, l in d["materials"].items():
                if isinstance(l, list):
                    d["materials"][k] = [m for m in l if not (isinstance(m, dict) and m.get("id") in vecchi)]
        d["materials"].setdefault("audios", [])
        tr = {"id": uid(), "type": "audio", "flag": 0, "attribute": 0,
              "name": a.traccia, "is_default_name": False, "segments": []}
        for v in piano:
            mat0, vol0, modelli = lib[v["effetto"]]
            m = copy.deepcopy(mat0); m["id"] = uid()
            d["materials"]["audios"].append(m)
            refs = []
            for k, mm in modelli:
                nm = copy.deepcopy(mm); nm["id"] = uid()
                d["materials"].setdefault(k, []).append(nm)
                refs.append(nm["id"])
            da = int(round(round(v["da"] * 1e6 / FPS_US) * FPS_US))
            dur = m["duration"]
            tr["segments"].append({
                "id": uid(), "source_timerange": {"start": 0, "duration": dur},
                "target_timerange": {"start": da, "duration": dur},
                "render_timerange": {"start": 0, "duration": 0}, "desc": "", "state": 0, "speed": 1.0,
                "is_loop": False, "is_tone_modify": False, "reverse": False, "intensifies_audio": False,
                "cartoon": False, "volume": float(v.get("volume", vol0)), "last_nonzero_volume": 1.0,
                "clip": None, "uniform_scale": None, "material_id": m["id"], "extra_material_refs": refs,
                "render_index": 0, "keyframe_refs": [], "enable_lut": False, "enable_adjust": False,
                "enable_hsl": False, "visible": True, "group_id": "", "enable_color_curves": True,
                "enable_hsl_curves": True, "track_render_index": 2, "hdr_settings": None,
                "hdr_vivid_settings": None, "enable_color_wheels": True, "track_attribute": 0,
                "is_placeholder": False, "template_id": "", "common_keyframes": [], "caption_info": None,
                "responsive_layout": None, "lyric_keyframes": None, "raw_segment_id": "", "source": 0,
            })
        d["tracks"].append(tr)
        json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(piano)} effetti sulla traccia {a.traccia!r}, su {len(copie(cart))} copie")


if __name__ == "__main__":
    main()
