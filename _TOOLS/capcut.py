# -*- coding: utf-8 -*-
"""Progetti CapCut scritti dal file, con CapCut chiuso.

  python3 capcut.py lista
  python3 capcut.py stato   <progetto>
  python3 capcut.py backup  <progetto> --dest <cartella del video> --etichetta tagli-v1
  python3 capcut.py chiudi  [--forza]
  python3 capcut.py prepara <progetto> --modello <progetto modello> --riprese IMG_1,IMG_2 [--velocita 1.03]
  python3 capcut.py taglia  <progetto> --tagli tagli.json [--velocita 1.03]
  python3 capcut.py broll   <progetto> --piano piano.json --cartella-clip <dir> [--outro <file>] [--traccia "b-roll"]
  python3 capcut.py spegni-loudness <progetto>

<progetto> è il nome nella home di CapCut, il nome della cartella, oppure un percorso a una cartella progetto.

Flusso: prima le riprese intere con color e audio (prepara), CapCut le
elabora una volta per ripresa, poi i tagli (taglia) che riusano l'audio già elaborato, poi b-roll e outro (broll).
I media vanno importati prima dall'interfaccia di CapCut (permessi della sandbox) e non possono stare sul Desktop.

Regole che il codice rispetta:
- il progetto esiste in sei copie (draft_info.json, .bak, template-2.tmp, e le stesse in Timelines/<id>/) e ogni
  copia ha id suoi: si scrive in tutte, cercando i segmenti per ripresa e tempo, mai per id;
- durate in timeline intere in fotogrammi (30 fps), sorgente = timeline x velocità;
- normalizzazione loudness ("Normalize loudness") mai, su nessun segmento: prepara e taglia non la scrivono e la
  tolgono dai segmenti che riscrivono, stato segnala dove è ancora attiva, spegni-loudness la spegne su un progetto
  esistente come fa CapCut quando si toglie la spunta (enable false);
- b-roll: niente color, niente Migliora voce, volume 0, velocità 1; mai più sorgente della clip;
- "Migliora voce" punta al file dell'intera ripresa (<prefisso>_0_<durata>.wav), così i tagli non lo rifanno: taglia copia
  percorso e tratto dalla ripresa intera già elaborata da CapCut, senza ricostruirli.
"""
import argparse, copy, glob, json, os, shutil, subprocess, sys, time, unicodedata, uuid

PROGETTI = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
FR = 1_000_000 / 30
SEGNAPOSTO = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
TENGO_PARLATO = {"speeds", "placeholder_infos", "hsl", "effects", "canvases", "realtime_denoises", "material_animations",
                 "sound_channel_mappings", "material_colors", "vocal_separations", "vocal_beautifys"}
TENGO_BROLL = {"speeds", "placeholder_infos", "hsl", "canvases", "realtime_denoises", "material_animations",
               "sound_channel_mappings", "material_colors", "vocal_separations"}
N = lambda s: unicodedata.normalize("NFC", s)
uid = lambda: str(uuid.uuid4()).upper()


# ------------------------------------------------------------------ utilità
def trova(nome):
    if os.path.isdir(nome) and os.path.exists(os.path.join(nome, "draft_info.json")):
        return os.path.abspath(nome)
    for cart in glob.glob(os.path.join(PROGETTI, "*")):
        meta = os.path.join(cart, "draft_meta_info.json")
        if not os.path.exists(meta):
            continue
        if N(os.path.basename(cart)) == N(nome):
            return cart
        try:
            if N(json.load(open(meta)).get("draft_name", "")) == N(nome):
                return cart
        except Exception:
            pass
    sys.exit(f"progetto non trovato: {nome}")


def copie(cart):
    c = [f"{cart}/draft_info.json", f"{cart}/draft_info.json.bak", f"{cart}/template-2.tmp"]
    for t in glob.glob(f"{cart}/Timelines/*/"):
        c += [f"{t}draft_info.json", f"{t}draft_info.json.bak", f"{t}template-2.tmp"]
    return [f for f in c if os.path.exists(f)]


def aperto():
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0


def primo_piano():
    r = subprocess.run(["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
                       capture_output=True, text=True)
    return r.stdout.strip()


def serve_chiuso(cart):
    # una copia del progetto fuori dalla cartella di CapCut (prove) si può scrivere anche con CapCut aperto
    if aperto() and os.path.realpath(cart).startswith(os.path.realpath(PROGETTI)):
        sys.exit("CapCut è aperto: al salvataggio sovrascriverebbe il file. Chiudilo (capcut.py chiudi) e riprova.")


def indice(d):
    idx = {}
    for k, l in d["materials"].items():
        if isinstance(l, list):
            for m in l:
                if isinstance(m, dict) and "id" in m:
                    idx[m["id"]] = (k, m)
    return idx


def principale(d):
    for t in d["tracks"]:
        if t["type"] == "video" and t.get("flag", 0) == 0:
            return t
    return next(t for t in d["tracks"] if t["type"] == "video")


def media_importati(cart):
    meta = json.load(open(f"{cart}/draft_meta_info.json"))
    per = {}
    for gruppo in meta.get("draft_materials", []):
        for x in gruppo.get("value", []):
            if x.get("file_Path"):
                per[N(x["file_Path"])] = x
    return meta, per


def stem(nome):
    return os.path.splitext(os.path.basename(N(nome)))[0]


def clona_riferimenti(d, idx, seg, tieni, velocita):
    refs = []
    for rid in seg["extra_material_refs"]:
        if rid not in idx:
            continue
        k, orig = idx[rid]
        if k not in tieni:
            continue
        m = copy.deepcopy(orig); m["id"] = uid()
        if k == "speeds":
            m["speed"] = velocita
        if k == "realtime_denoises":
            m["is_denoise"] = False
        d["materials"].setdefault(k, []).append(m); refs.append(m["id"])
    return refs


def scrivi_meta_durata(cart, durata):
    meta = json.load(open(f"{cart}/draft_meta_info.json")); meta["tm_duration"] = durata
    json.dump(meta, open(f"{cart}/draft_meta_info.json", "w"), ensure_ascii=False)


# ------------------------------------------------------------------ comandi
def lista(a):
    righe = []
    for cart in glob.glob(os.path.join(PROGETTI, "*")):
        meta = os.path.join(cart, "draft_meta_info.json")
        if os.path.exists(meta):
            m = json.load(open(meta))
            righe.append((os.path.getmtime(f"{cart}/draft_info.json") if os.path.exists(f"{cart}/draft_info.json") else 0,
                          os.path.basename(cart), m.get("draft_name", ""), m.get("tm_duration", 0) / 1e6))
    for t, c, n, dur in sorted(righe, reverse=True):
        print(f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(t))}  {dur:7.1f} s  cartella {c!r}  nome {n!r}")


def stato(a):
    cart = trova(a.progetto)
    print(f"progetto {cart}\nCapCut {'APERTO' if aperto() else 'chiuso'}{' (progetto aperto: .locked)' if os.path.exists(cart + '/.locked') and aperto() else ''}")
    for f in copie(cart):
        d = json.load(open(f)); idx = indice(d)
        mp = principale(d); vids = {v["id"]: v for v in d["materials"]["videos"]}
        segs = sorted(mp["segments"], key=lambda s: s["target_timerange"]["start"])
        pos = 0; contigui = True
        for s in segs:
            contigui &= s["target_timerange"]["start"] == pos; pos += s["target_timerange"]["duration"]
        non_fot = sum(1 for t in d["tracks"] if t["type"] == "video" for s in t["segments"]
                      if abs(s["target_timerange"]["duration"] / FR - round(s["target_timerange"]["duration"] / FR)) > 0.02)
        loud = sum(1 for t in d["tracks"] for s in t["segments"]
                   if any(idx[r][0] == "loudnesses" and idx[r][1].get("enable", True) for r in s.get("extra_material_refs", []) if r in idx))
        voce = voce_intera = voce_pronta = 0
        for s in segs:
            v = vids.get(s["material_id"], {})
            if not v.get("has_audio"):
                continue
            kinds = {idx[r][0]: idx[r][1] for r in s["extra_material_refs"] if r in idx}
            if "vocal_beautifys" in kinds:
                voce += 1; pp = kinds["vocal_beautifys"]["production_path"]
                voce_intera += kinds["vocal_beautifys"].get("time_range", {}).get("start", -1) == 0
                voce_pronta += os.path.exists(pp.replace(SEGNAPOSTO, cart))
        orfani = sum(1 for t in d["tracks"] for s in t["segments"] for r in s.get("extra_material_refs", []) if r not in idx)
        oltre = [vids[s["material_id"]]["material_name"] for t in d["tracks"] if t["type"] == "video" for s in t["segments"]
                 if s["material_id"] in vids and s["source_timerange"]["start"] + s["source_timerange"]["duration"] > vids[s["material_id"]]["duration"] + 1000]
        mancanti = sorted({v["path"] for v in vids.values() if v.get("path") and not os.path.exists(v["path"])})
        tracce = ", ".join(f"{t['type']}{'/' + t['name'] if t.get('name') else ''}:{len(t['segments'])}" for t in d["tracks"])
        print(f"\n{f.replace(cart, '.')}\n  tracce {tracce} | durata {d['duration']/1e6:.2f} s | principale contigua {contigui}"
              f" | durate non a fotogramma {non_fot}\n  Migliora voce {voce} (sulla ripresa intera {voce_intera},"
              f" file già elaborati {voce_pronta}) | riferimenti orfani {orfani}"
              + (f"\n  NORMALIZZAZIONE LOUDNESS ATTIVA SU {loud} SEGMENTI: va tolta" if loud else "")
              + (f"\n  CLIP PIÙ CORTE DEL TRATTO USATO: {oltre}" if oltre else "")
              + (f"\n  MEDIA MANCANTI: {mancanti}" if mancanti else ""))


def backup(a):
    cart = trova(a.progetto)
    dest = os.path.join(a.dest, f"_BACKUP_CAPCUT_{a.etichetta}_{time.strftime('%Y-%m-%d_%H%M')}")
    shutil.copytree(cart, dest); print("backup in", dest)


def chiudi(a):
    if not aperto():
        print("CapCut è già chiuso"); return
    if primo_piano() == "CapCut" and not a.forza:
        sys.exit("CapCut è in primo piano: l'utente potrebbe starlo usando. Chiedi prima, poi --forza.")
    subprocess.run(["osascript", "-e", 'tell application "CapCut" to quit'], capture_output=True)   # risponde -128 ma chiude
    for _ in range(40):
        if not aperto():
            print("CapCut chiuso, progetto salvato"); return
        time.sleep(1)
    sys.exit("CapCut non si è chiuso in 40 s: controlla se c'è un dialogo aperto")


def prepara(a):
    cart = trova(a.progetto); serve_chiuso(cart); mod_cart = trova(a.modello)
    mod = json.load(open(f"{mod_cart}/draft_info.json")); midx = indice(mod)
    mvids = {v["id"]: v for v in mod["materials"]["videos"]}
    tpl = next(s for s in principale(mod)["segments"] if mvids[s["material_id"]].get("has_audio"))
    tpl_video = mvids[tpl["material_id"]]
    tpl_kinds = {midx[r][0]: midx[r][1] for r in tpl["extra_material_refs"] if r in midx}
    for k in ("vocal_beautifys", "effects"):
        if k not in tpl_kinds:
            print(f"attenzione: il modello non ha {k} sul parlato")
    if "loudnesses" in tpl_kinds:
        print("il modello ha la normalizzazione loudness: non viene copiata")
    _, per = media_importati(cart)
    riprese = []
    for o in [x.strip() for x in a.riprese.split(",") if x.strip()]:
        c = [p for p in per.values() if stem(p["file_Path"]) == N(o)]
        if not c:
            sys.exit(f"{o}: non è fra i media importati nel progetto. Va importato dall'interfaccia di CapCut.")
        riprese.append(c[0])
    for f in copie(cart):
        d = json.load(open(f))
        if not any(t["type"] == "video" for t in d["tracks"]):   # progetto appena creato: la traccia principale si copia dal modello
            tr = copy.deepcopy(principale(mod)); tr.update({"id": uid(), "segments": []}); d["tracks"].insert(0, tr)
        vecchie = {r for t in d["tracks"] if t is principale(d) for s in t["segments"] for r in s["extra_material_refs"]}
        for k, l in d["materials"].items():
            if isinstance(l, list):
                d["materials"][k] = [m for m in l if not (isinstance(m, dict) and m.get("id") in vecchie)]
        mp = principale(d); mp["segments"] = []; pos = 0
        for p in riprese:
            v = copy.deepcopy(tpl_video); v.update({"id": uid(), "path": p["file_Path"], "material_name": os.path.basename(p["file_Path"]),
                                                   "duration": p["duration"], "width": p["width"], "height": p["height"],
                                                   "local_material_id": p["id"], "unique_id": ""})
            d["materials"]["videos"].append(v)
            refs = []
            for rid in tpl["extra_material_refs"]:
                if rid not in midx or midx[rid][0] not in TENGO_PARLATO:
                    continue
                k, orig = midx[rid]; m = copy.deepcopy(orig); m["id"] = uid()
                if k == "speeds": m["speed"] = a.velocita
                if k == "realtime_denoises": m["is_denoise"] = False
                if k == "vocal_beautifys":
                    m.update({"enable": True, "ambient_sound_level": 75, "time_range": {"start": 0, "duration": p["duration"]},
                              "production_path": f"{SEGNAPOSTO}/Resources/audioAlg/_0_{p['duration']}.wav"})
                d["materials"].setdefault(k, []).append(m); refs.append(m["id"])
            s = copy.deepcopy(tpl); s.update({"id": uid(), "material_id": v["id"], "extra_material_refs": refs, "speed": a.velocita,
                                              "render_index": 0, "track_render_index": 0, "keyframe_refs": [], "common_keyframes": []})
            dur_t = int(round(round(p["duration"] / a.velocita / FR) * FR))
            s["source_timerange"] = {"start": 0, "duration": min(p["duration"], int(round(dur_t * a.velocita)))}
            s["target_timerange"] = {"start": pos, "duration": dur_t}
            mp["segments"].append(s); pos += dur_t
        d["duration"] = pos; d["canvas_config"] = copy.deepcopy(mod["canvas_config"])
        json.dump(d, open(f, "w"), ensure_ascii=False)
    scrivi_meta_durata(cart, pos)
    print(f"{len(riprese)} riprese intere scritte su {len(copie(cart))} copie ({pos/1e6:.1f} s): "
          + ", ".join(os.path.basename(p["file_Path"]) for p in riprese)
          + "\nOra apri il progetto in CapCut e aspetta \"Enhance voice applied\": una elaborazione per ripresa.")


def taglia(a):
    cart = trova(a.progetto); serve_chiuso(cart); T = json.load(open(a.tagli))
    for f in copie(cart):
        d = json.load(open(f)); idx = indice(d); vids = {v["id"]: v for v in d["materials"]["videos"]}
        tolte = 0
        mp = principale(d)
        # modello per ripresa: il segmento più lungo di quella ripresa (la ripresa intera, se c'è ancora)
        modelli = {}
        for s in mp["segments"]:
            v = vids.get(s["material_id"])
            if v and v.get("has_audio"):
                r = stem(v["material_name"])
                if r not in modelli or s["source_timerange"]["duration"] > modelli[r][0]["source_timerange"]["duration"]:
                    modelli[r] = (s, v)
        manca = sorted({x["ripresa"] for x in T} - set(modelli))
        if manca:
            sys.exit(f"{f}: sulla traccia principale non ci sono le riprese {manca}. Prima capcut.py prepara.")
        vecchie = {r for s in mp["segments"] if vids.get(s["material_id"], {}).get("has_audio") for r in s["extra_material_refs"]}
        vecchi_video = {s["material_id"] for s in mp["segments"] if vids.get(s["material_id"], {}).get("has_audio")}
        nuovi_segmenti = []; pos = 0; nuovi_mat = {}
        for x in T:
            s0, v0 = modelli[x["ripresa"]]
            kinds = {idx[r][0]: idx[r][1] for r in s0["extra_material_refs"] if r in idx}
            v = copy.deepcopy(v0); v["id"] = uid(); nuovi_mat.setdefault("videos", []).append(v)
            dur_t = int(round(round((x["a"] - x["da"]) / a.velocita * 1e6 / FR) * FR))
            src = {"start": int(round(x["da"] * 1e6)), "duration": int(round(dur_t * a.velocita))}
            refs = []
            for rid in s0["extra_material_refs"]:
                if rid not in idx:
                    continue
                k, orig = idx[rid]
                if k == "loudnesses":        # normalizzazione mai: il taglio non la riporta
                    tolte += 1
                    continue
                m = copy.deepcopy(orig); m["id"] = uid()
                if k == "speeds": m["speed"] = a.velocita
                # vocal_beautifys: percorso e tratto restano quelli che CapCut ha scritto elaborando la ripresa intera.
                # Ricostruirli dalla durata del materiale non funziona: all'apertura CapCut ricalcola la durata
                # (IMG_8608: 46266666 nel materiale, file voce _0_46247000.wav) e i tagli non trovano più il file.
                nuovi_mat.setdefault(k, []).append(m); refs.append(m["id"])
            s = copy.deepcopy(s0)
            s.update({"id": uid(), "material_id": v["id"], "extra_material_refs": refs, "speed": a.velocita,
                      "source_timerange": src, "target_timerange": {"start": pos, "duration": dur_t},
                      "render_index": 0, "track_render_index": 0, "keyframe_refs": [], "common_keyframes": []})
            nuovi_segmenti.append(s); pos += dur_t
        for k, l in d["materials"].items():
            if isinstance(l, list):
                d["materials"][k] = [m for m in l if not (isinstance(m, dict) and (m.get("id") in vecchie or (k == "videos" and m.get("id") in vecchi_video)))]
        for k, l in nuovi_mat.items():
            d["materials"].setdefault(k, []).extend(l)
        mp["segments"] = nuovi_segmenti          # l'outro, se c'era, lo rimette broll
        d["duration"] = pos
        json.dump(d, open(f, "w"), ensure_ascii=False)
        pronti = sum(os.path.exists(m["production_path"].replace(SEGNAPOSTO, cart)) for m in nuovi_mat.get("vocal_beautifys", []))
    scrivi_meta_durata(cart, pos)
    print(f"{len(T)} tagli su {len(copie(cart))} copie, {pos/1e6:.2f} s | Migliora voce già elaborato per {pronti} tagli su {len(T)}"
          + ("" if pronti == len(T) else " (gli altri li elabora CapCut all'apertura)")
          + (f"\nnormalizzazione loudness tolta da {tolte} tagli" if tolte else ""))


def broll(a):
    cart = trova(a.progetto); serve_chiuso(cart); piano = json.load(open(a.piano)); _, per = media_importati(cart)
    def media(nome):
        cand = [p for k, p in per.items() if os.path.dirname(k) == N(os.path.abspath(a.cartella_clip)) and
                (os.path.basename(k) == N(nome) or stem(k) == stem(N(nome)) or os.path.basename(k).startswith(N(nome)))]
        if not cand:
            sys.exit(f"{nome}: non è fra i media importati nel progetto da {a.cartella_clip}. Va importato dall'interfaccia di CapCut.")
        return cand[0]
    for x in piano:
        p = media(x["clip"]); a_us = int(round(x["da"] * 30)) * 1_000_000 // 30; b_us = int(round(x["a"] * 30)) * 1_000_000 // 30
        if b_us - a_us + int(x.get("offset", 0) * 1e6) > p["duration"]:
            sys.exit(f"{x['clip']}: servono {(b_us - a_us)/1e6 + x.get('offset', 0):.2f} s, la clip ne ha {p['duration']/1e6:.2f}")
    for f in copie(cart):
        d = json.load(open(f)); idx = indice(d); vids = {v["id"]: v for v in d["materials"]["videos"]}
        uid_media = {N(v["path"]): v["unique_id"] for v in vids.values() if v.get("unique_id")}
        mp = principale(d)
        tpl = next(s for s in mp["segments"] if vids.get(s["material_id"], {}).get("has_audio"))
        tpl_v = vids[tpl["material_id"]]
        def segmento(p, t0, dur, off, render):
            v = copy.deepcopy(tpl_v); v.update({"id": uid(), "path": p["file_Path"], "material_name": os.path.basename(p["file_Path"]),
                                               "duration": p["duration"], "width": p["width"], "height": p["height"],
                                               "local_material_id": p["id"], "unique_id": uid_media.get(N(p["file_Path"]), ""), "has_audio": False})
            d["materials"]["videos"].append(v)
            s = copy.deepcopy(tpl)
            s.update({"id": uid(), "material_id": v["id"], "extra_material_refs": clona_riferimenti(d, idx, tpl, TENGO_BROLL, 1.0),
                      "speed": 1.0, "volume": 0.0, "last_nonzero_volume": 0.0, "render_index": render, "track_render_index": render,
                      "keyframe_refs": [], "common_keyframes": []})
            for k in list(s):
                if k.startswith("enable_"):
                    s[k] = False
            off = max(0, min(off, p["duration"] - dur))
            s["source_timerange"] = {"start": off, "duration": dur}; s["target_timerange"] = {"start": t0, "duration": dur}
            return s
        # via la traccia b-roll vecchia e l'outro vecchio
        d["tracks"] = [t for t in d["tracks"] if t.get("name") != a.traccia]
        mp["segments"] = [s for s in mp["segments"] if vids.get(s["material_id"], {}).get("has_audio")]
        tr = {"id": uid(), "type": "video", "flag": 2, "attribute": 0, "name": a.traccia, "is_default_name": False, "segments": []}
        for x in piano:
            p = media(x["clip"]); a_us = int(round(x["da"] * 30)) * 1_000_000 // 30; b_us = int(round(x["a"] * 30)) * 1_000_000 // 30
            tr["segments"].append(segmento(p, a_us, b_us - a_us, int(x.get("offset", 0) * 1e6), 1))
        fine = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"] for s in mp["segments"])
        durata = fine
        if a.outro:
            po = per.get(N(os.path.abspath(a.outro)))
            if not po:
                sys.exit(f"outro {a.outro} non importato nel progetto")
            mp["segments"].append(segmento(po, fine, int(round(round(po["duration"] / FR) * FR)), 0, 0)); durata += mp["segments"][-1]["target_timerange"]["duration"]
            mp["segments"][-1]["source_timerange"]["duration"] = min(po["duration"], mp["segments"][-1]["target_timerange"]["duration"])
        d["tracks"].insert(d["tracks"].index(mp) + 1, tr); d["duration"] = durata
        json.dump(d, open(f, "w"), ensure_ascii=False)
    scrivi_meta_durata(cart, durata)
    print(f"{len(piano)} b-roll sulla traccia {a.traccia!r}{' e outro in coda' if a.outro else ''}, durata {durata/1e6:.2f} s, {len(copie(cart))} copie")


def spegni_loudness(a):
    cart = trova(a.progetto); serve_chiuso(cart)
    for f in copie(cart):
        d = json.load(open(f)); accese = [m for m in d["materials"].get("loudnesses", []) if m.get("enable", True)]
        for m in accese:
            m["enable"] = False
        if accese:
            json.dump(d, open(f, "w"), ensure_ascii=False)
        print(f"{f.replace(cart, '.')}: normalizzazione spenta su {len(accese)} segmenti")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    sub.add_parser("lista")
    x = sub.add_parser("stato"); x.add_argument("progetto")
    x = sub.add_parser("backup"); x.add_argument("progetto"); x.add_argument("--dest", required=True); x.add_argument("--etichetta", default="backup")
    x = sub.add_parser("chiudi"); x.add_argument("--forza", action="store_true")
    x = sub.add_parser("prepara"); x.add_argument("progetto"); x.add_argument("--modello", required=True)
    x.add_argument("--velocita", type=float, default=1.03); x.add_argument("--riprese", required=True, help="IMG_1,IMG_2 nell'ordine")
    x = sub.add_parser("taglia"); x.add_argument("progetto"); x.add_argument("--tagli", required=True); x.add_argument("--velocita", type=float, default=1.03)
    x = sub.add_parser("broll"); x.add_argument("progetto"); x.add_argument("--piano", required=True)
    x.add_argument("--cartella-clip", required=True); x.add_argument("--outro", default=""); x.add_argument("--traccia", default="b-roll")
    x = sub.add_parser("spegni-loudness"); x.add_argument("progetto")
    a = ap.parse_args()
    {"lista": lista, "stato": stato, "backup": backup, "chiudi": chiudi, "prepara": prepara, "taglia": taglia, "broll": broll,
     "spegni-loudness": spegni_loudness}[a.passo](a)
