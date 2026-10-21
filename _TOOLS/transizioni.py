"""Transizioni fra i tagli e dissolvenze audio in un progetto CapCut, scritte dal file.

  python3 transizioni.py <progetto> [--traccia ""] [--durata 0.2] [--fade 0.04] [--togli]

Serve quando i jump cut si sentono e si vedono troppo. Mette due cose, che risolvono due difetti diversi:

- una transizione "Mix" (dissolvenza incrociata) su ogni giunzione della traccia, che toglie il salto
  dell'immagine. È `is_overlap`, cioè prende metà durata da ogni lato **senza spostare i tempi**: la
  timeline resta lunga uguale e b-roll e sottotitoli non si muovono. Perché funzioni, ogni taglio deve
  avere nella ripresa sorgente almeno mezza transizione di materiale prima dell'inizio e dopo la fine:
  se non ce l'ha, lo strumento lo dice e salta quella giunzione;
- una dissolvenza audio in entrata e in uscita su ogni segmento, che toglie lo scatto della prima
  consonante quando il girato non ha silenzio in cui allargare il taglio.

Con CapCut chiuso, su tutte e sei le copie, dopo un backup fatto da chi chiama. Rilanciarlo è sicuro:
prima toglie quello che aveva messo.
"""
import argparse, copy, json, os, subprocess, sys, uuid

PROGETTI = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
CACHE = os.path.expanduser("~/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/"
                           "User Data/Cache/effect/6724845717472416269/7b53f4c008c4c684fccf8c7d4d46cc92")
MIX = "6724845717472416269"      # "Mix", la dissolvenza incrociata di CapCut


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


def materiale_transizione(durata_us):
    return {"id": uid(), "type": "transition", "name": "Mix", "effect_id": MIX, "resource_id": MIX,
            "third_resource_id": MIX, "source_platform": 1, "path": CACHE, "duration": durata_us,
            "is_overlap": True, "platform": "all", "category_id": "25809", "category_name": "Trending",
            "request_id": "", "is_ai_transition": False, "video_path": "", "task_id": ""}


def materiale_fade(entrata_us, uscita_us):
    return {"id": uid(), "type": "audio_fade", "fade_type": 0,
            "fade_in_duration": entrata_us, "fade_out_duration": uscita_us}


def durata_materiale(d, mid):
    for m in d["materials"].get("videos", []):
        if m["id"] == mid:
            return m.get("duration")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("progetto")
    ap.add_argument("--traccia", default="", help="nome della traccia video; vuoto = la principale")
    ap.add_argument("--durata", type=float, default=0.2, help="durata della transizione in secondi")
    ap.add_argument("--fade", type=float, default=0.04, help="dissolvenza audio per lato, in secondi")
    ap.add_argument("--togli", action="store_true", help="toglie transizioni e dissolvenze messe da qui")
    a = ap.parse_args()

    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        sys.exit("CapCut è aperto: va chiuso prima di scrivere")
    if not a.togli and not os.path.isdir(CACHE):
        sys.exit(f"l'effetto Mix non è nella cache di CapCut: {CACHE}\n"
                 "applicane una a mano su un progetto qualsiasi, così CapCut la scarica")

    cart = cartella_progetto(a.progetto)
    dur_us = int(round(a.durata * 1e6))
    fade_us = int(round(a.fade * 1e6))
    prima = None

    for f in copie(cart):
        d = json.load(open(f))
        tr = next((t for t in d["tracks"] if t["type"] == "video" and (t.get("name") or "") == a.traccia), None)
        if tr is None:
            continue
        d["materials"].setdefault("transitions", [])
        d["materials"].setdefault("audio_fades", [])

        # via quello che c'era, sia in ripetizione sia con --togli
        vecchi = {m["id"] for m in d["materials"]["transitions"]} | {m["id"] for m in d["materials"]["audio_fades"]}
        for s in tr["segments"]:
            s["extra_material_refs"] = [i for i in s.get("extra_material_refs", []) if i not in vecchi]
        d["materials"]["transitions"] = []
        d["materials"]["audio_fades"] = []

        messe = saltate = 0
        if not a.togli:
            for i, s in enumerate(tr["segments"]):
                # dissolvenza audio su ogni segmento
                fd = materiale_fade(fade_us, fade_us)
                d["materials"]["audio_fades"].append(fd)
                s["extra_material_refs"].append(fd["id"])
                # transizione verso il segmento dopo, se c'è materiale per la sovrapposizione
                if i == len(tr["segments"]) - 1:
                    continue
                meta = dur_us // 2
                fine_qui = s["source_timerange"]["start"] + s["source_timerange"]["duration"]
                tot_qui = durata_materiale(d, s["material_id"])
                inizio_la = tr["segments"][i + 1]["source_timerange"]["start"]
                if tot_qui is not None and fine_qui + meta > tot_qui or inizio_la < meta:
                    saltate += 1
                    continue
                tz = materiale_transizione(dur_us)
                d["materials"]["transitions"].append(tz)
                s["extra_material_refs"].append(tz["id"])
                messe += 1
        json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
        if prima is None:
            prima = (messe, saltate, len(tr["segments"]))

    if prima is None:
        sys.exit(f"traccia {a.traccia!r} non trovata")
    messe, saltate, n = prima
    if a.togli:
        print(f"transizioni e dissolvenze tolte da {len(copie(cart))} copie")
    else:
        print(f"{messe} transizioni da {a.durata}s e {n} dissolvenze audio da {a.fade}s per lato, "
              f"su {len(copie(cart))} copie")
        if saltate:
            print(f"{saltate} giunzioni saltate: la ripresa non ha materiale per la sovrapposizione")


if __name__ == "__main__":
    main()
