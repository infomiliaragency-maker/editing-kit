# -*- coding: utf-8 -*-
"""Metodo Remotion: il montaggio scritto in codice e renderizzato a file, senza CapCut.
Il progetto Remotion sta in _REMOTION/ accanto a _TOOLS/.

Usa gli stessi file del metodo CapCut, quindi tagli, piano b-roll e sottotitoli si decidono con le skill di sempre:

  python3 remotion.py parlato     <cartella video> [--tagli _build/tagli.json] [--velocita 1.03] [--audio auto|elaborato|grezzo] [--loudness -14]
  python3 remotion.py da-capcut   <cartella video> --progetto "<progetto CapCut>" --export <export di CapCut.mp4>
  python3 remotion.py sottotitoli <cartella video> --stile <stile.json> [--rifai]
  python3 remotion.py montaggio   <cartella video> [--piano piano_broll.json] [--cartella-clip DIR] [--outro FILE]
                                  [--sottotitoli blocchi|ref2|nessuno] [--stile stile.json] [--transizioni auto|nessuna] [--senza-zoom]
  python3 remotion.py render      <cartella video> [--anteprima]
  python3 remotion.py studio      <cartella video>

parlato     riprese tagliate e unite in <video>/_remotion/public/parlato.mp4 (1080x1920, 30 fps). Durata di ogni taglio
            identica a capcut.py taglia (fotogrammi interi, sorgente = timeline x velocità), quindi piani b-roll e
            sottotitoli fatti per CapCut cadono negli stessi punti. Girato HDR (iPhone, HLG) convertito in SDR bt709:
            senza conversione esce grigio e slavato. Audio: <video>/_build/elaborato/<ripresa>.wav se c'è (la voce
            passata da "Migliora voce" di CapCut), altrimenti quello del girato. Loudness: nessuna normalizzazione se
            non si chiede (regola 8 dell'area).
da-capcut   metodo ibrido: tagli, velocità, color e "Migliora voce" fatti in CapCut,
            export pulito (senza sottotitoli, b-roll né outro). L'export diventa public/parlato.mp4 così com'è, e i
            tagli si leggono dalla traccia principale del progetto, compresi i ritocchi fatti a mano dall'utente:
            parlato.json esce uguale a quello di `parlato`, quindi sottotitoli, montaggio e render non cambiano.
sottotitoli blocchi con la stessa divisione di sottotitoli_capcut.py (parole da _build/trascrizioni/, Scribe), scritti in
            <video>/sottotitoli_blocchi.json. Se il file c'è già (riletto a mano) non si tocca senza --rifai.
montaggio   <video>/_remotion/montaggio.json e props.json, con le grafiche animate di <video>/grafiche.json se c'è; b-roll, outro ed effetti sonori collegati in _remotion/public/
            (link fisici, nessuno spazio in più; i b-roll HDR vengono convertiti). Transizioni con effetto sonoro
            all'entrata e all'uscita di ogni b-roll, alternando swoosh e flash.
render      export in <video>/EXPORT_remotion.mp4, oppure anteprima 540p in <video>/ANTEPRIMA_remotion_540p.mp4.
studio      apre Remotion Studio sul video, per guardarlo e ritoccare a mano.
"""
import argparse, json, os, shutil, subprocess, sys, time, wave
from concurrent.futures import ThreadPoolExecutor

QUI = os.path.dirname(os.path.abspath(__file__))
REMOTION = os.path.join(os.path.dirname(QUI), "_REMOTION")
FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
FP = shutil.which("ffprobe") or os.path.expanduser("~/.local/bin/ffprobe")
FPS = 30
SR = 48000
# HDR (HLG/PQ) -> SDR bt709. Saturazione e gamma tarate su un fotogramma esportato da CapCut con la correzione colore
# dell'area: scarto medio 6 su 255 per canale su quattro zone; hable da solo era rosso e scuro
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,"
           "format=yuv420p,eq=saturation=0.65:gamma=1.1")
VERTICALE = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1"
X264 = ["-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def lavoro(video):
    d = os.path.join(video, "_remotion")
    os.makedirs(os.path.join(d, "public"), exist_ok=True)
    return d


def primo(*percorsi):
    return next((p for p in percorsi if p and os.path.exists(p)), None)


def sonda(f):
    out = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=color_transfer:format=duration", "-of", "json", f], capture_output=True, text=True).stdout
    j = json.loads(out or "{}")
    trc = (j.get("streams") or [{}])[0].get("color_transfer", "")
    return {"hdr": trc in ("arib-std-b67", "smpte2084"), "durata": float(j.get("format", {}).get("duration", 0))}


def girato(video, ripresa, cartella):
    for c in [cartella, os.path.join(video, "GIRATO")] + [os.path.join(video, x) for x in os.listdir(video) if x.startswith("VIDEO_")]:
        if c and os.path.isdir(c):
            for f in sorted(os.listdir(c)):
                if os.path.splitext(f)[0] == ripresa and f.lower().endswith((".mov", ".mp4", ".m4v")):
                    return os.path.join(c, f)
    sys.exit(f"ripresa {ripresa}: non trovata in GIRATO/ né in --girato")


# ---------------------------------------------------------------- parlato
def parlato(a):
    w = lavoro(a.video); tmp = os.path.join(w, "_pezzi"); os.makedirs(tmp, exist_ok=True)
    tagli = json.load(open(primo(a.tagli, os.path.join(a.video, "_build", "tagli.json"), os.path.join(a.video, "tagli.json")) or sys.exit("manca tagli.json")))
    v = a.velocita
    pezzi, t = [], 0
    for i, x in enumerate(tagli):
        n = int(round((x["a"] - x["da"]) / v * FPS))           # come capcut.py taglia
        sorg = girato(a.video, x["ripresa"], a.girato)
        el = os.path.join(a.video, "_build", "elaborato", x["ripresa"] + ".wav")
        audio = el if (a.audio == "elaborato" or (a.audio == "auto" and os.path.exists(el))) else sorg
        if a.audio == "elaborato" and not os.path.exists(el):
            sys.exit(f"manca {el}")
        pezzi.append({"i": i, "ripresa": x["ripresa"], "da": x["da"], "n": n, "sorg": sorg, "audio": audio,
                      "start": round(t / FPS, 4), "end": round((t + n) / FPS, 4), "testo": x.get("testo", "")})
        t += n
    hdr = {p["sorg"]: sonda(p["sorg"])["hdr"] for p in pezzi}
    print(f"{len(pezzi)} tagli, {t} fotogrammi = {t / FPS:.2f} s a velocità {v}; "
          f"girato HDR: {sum(hdr.values())}/{len(hdr)} riprese; audio: {'elaborato' if any(p['audio'].endswith('.wav') for p in pezzi) else 'grezzo'}")

    def video_pezzo(p):
        out = os.path.join(tmp, f"v{p['i']:03d}.mp4")
        vf = ",".join(([TONEMAP] if hdr[p["sorg"]] else []) + [VERTICALE, f"setpts=(PTS-STARTPTS)/{v}", f"fps={FPS}",
                                                               "tpad=stop_mode=clone:stop_duration=1"])
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{p['da']:.4f}", "-i", p["sorg"], "-t", f"{p['n'] * v / FPS + 0.3:.4f}",
                        "-an", "-vf", vf, "-frames:v", str(p["n"]), "-r", str(FPS), *X264, out], check=True)
        return out

    def audio_pezzo(p):
        # PCM esatto al campione: niente AAC per pezzo, che a ogni giunzione aggiungerebbe il suo ritardo
        cam = round(p["n"] / FPS * SR)
        af = f"atempo={v},afade=t=in:d=0.005,afade=t=out:st={max(0, p['n'] / FPS - 0.005):.4f}:d=0.005" if v != 1 else \
             f"afade=t=in:d=0.005,afade=t=out:st={max(0, p['n'] / FPS - 0.005):.4f}:d=0.005"
        raw = subprocess.run([FF, "-v", "error", "-ss", f"{p['da']:.4f}", "-i", p["audio"], "-t", f"{p['n'] * v / FPS:.4f}",
                              "-vn", "-af", af, "-ar", str(SR), "-ac", "2", "-f", "s16le", "-"], capture_output=True, check=True).stdout
        return raw[:cam * 4].ljust(cam * 4, b"\0")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        vids = list(ex.map(video_pezzo, pezzi))
    with ThreadPoolExecutor(max_workers=8) as ex:
        pcm = b"".join(ex.map(audio_pezzo, pezzi))
    lista = os.path.join(tmp, "lista.txt")
    open(lista, "w").write("".join(f"file '{f}'\n" for f in vids))
    wav = os.path.join(tmp, "voce.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm)
    af = ["-af", f"loudnorm=I={a.loudness}:TP=-1.5:LRA=11"] if a.loudness is not None else []
    out = os.path.join(w, "public", "parlato.mp4")
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", *af, "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-t", f"{t / FPS:.4f}", out], check=True)
    shutil.rmtree(tmp)
    json.dump({"velocita": v, "durata": round(t / FPS, 4), "fotogrammi": t, "loudness": a.loudness, "pezzi": pezzi},
              open(os.path.join(w, "parlato.json"), "w"), ensure_ascii=False, indent=1)
    reale = sonda(out)["durata"]
    print(f"{out}: {reale:.3f} s (atteso {t / FPS:.3f}), in {time.time() - t0:.0f} s")


# ---------------------------------------------------------------- da-capcut (metodo ibrido)
def da_capcut(a):
    sys.path.insert(0, QUI)
    import capcut
    cart = capcut.trova(a.progetto)
    d = json.load(open(os.path.join(cart, "draft_info.json")))
    vids = {v["id"]: v for v in d["materials"]["videos"]}
    spd = {x["id"]: x.get("speed", 1.0) for x in d["materials"].get("speeds", [])}
    pezzi, vel = [], set()
    for s in sorted(capcut.principale(d)["segments"], key=lambda s: s["target_timerange"]["start"]):
        mat = vids[s["material_id"]]
        v = s.get("speed") or next((spd[r] for r in s.get("extra_material_refs", []) if r in spd), 1.0)
        vel.add(round(v, 4))
        t0, td = s["target_timerange"]["start"] / 1e6, s["target_timerange"]["duration"] / 1e6
        pezzi.append({"i": len(pezzi), "ripresa": os.path.splitext(os.path.basename(mat["path"]))[0],
                      "da": round(s["source_timerange"]["start"] / 1e6, 4), "n": int(round(td * FPS)),
                      "sorg": mat["path"], "audio": "export CapCut", "start": round(t0, 4), "end": round(t0 + td, 4), "testo": ""})
    if len(vel) > 1:
        print(f"attenzione: velocità diverse nei tagli {sorted(vel)}: i sottotitoli usano la prima")
    durata = pezzi[-1]["end"]
    buchi = [(p["end"], q["start"]) for p, q in zip(pezzi, pezzi[1:]) if abs(q["start"] - p["end"]) > 0.001]
    if buchi:
        print(f"attenzione: la traccia principale non è contigua in {len(buchi)} punti: {buchi[:3]}")
    reale = sonda(a.export)["durata"]
    if abs(reale - durata) > 0.1:
        sys.exit(f"l'export dura {reale:.2f} s, il progetto {durata:.2f} s: export vecchio o di un altro progetto?")
    w = lavoro(a.video)
    nota = collega(a.export, os.path.join(w, "public", "parlato.mp4"))
    json.dump({"velocita": sorted(vel)[0], "durata": round(durata, 4), "fotogrammi": int(round(durata * FPS)), "loudness": None,
               "origine": {"progetto": os.path.basename(cart), "export": os.path.abspath(a.export)}, "pezzi": pezzi},
              open(os.path.join(w, "parlato.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(pezzi)} tagli dal progetto {os.path.basename(cart)}, {durata:.2f} s; export {reale:.2f} s collegato come parlato.mp4 {nota}")


# ---------------------------------------------------------------- sottotitoli
def parole_montato(video, pz):
    cache, parole = {}, []
    for i, p in enumerate(pz["pezzi"]):
        rip = p["ripresa"]
        if rip not in cache:
            f = primo(os.path.join(video, "_build", "trascrizioni", rip + ".json"), os.path.join(video, "_build", "trascrizione", rip + ".json"))
            if not f:
                sys.exit(f"manca la trascrizione della ripresa {rip}: trascrivi.py --diarizza")
            cache[rip] = [w for w in json.load(open(f))["words"] if w.get("type", "word") == "word"]
        s0, sd, v = p["da"], p["n"] * pz["velocita"] / FPS, pz["velocita"]
        for w in cache[rip]:
            if s0 <= (w["start"] + w["end"]) / 2 <= s0 + sd:
                parole.append({"testo": w["text"].strip(), "da": p["start"] + max(0.0, w["start"] - s0) / v,
                               "a": p["start"] + min(sd, w["end"] - s0) / v, "clip": i, "clip_da": p["start"]})
    return parole


def sottotitoli(a):
    sys.path.insert(0, QUI)
    import sottotitoli_capcut as sc
    fjson = os.path.join(a.video, "sottotitoli_blocchi.json")
    if os.path.exists(fjson) and not a.rifai:
        sys.exit(f"{fjson} c'è già (forse riletto a mano): lo uso così com'è. Per rifarlo --rifai")
    pz = json.load(open(os.path.join(lavoro(a.video), "parlato.json")))
    sc.R = json.load(open(a.stile))["regole"]
    if os.path.exists(fjson):
        os.makedirs(os.path.join(a.video, "_build", "sottotitoli"), exist_ok=True)
        shutil.copy(fjson, os.path.join(a.video, "_build", "sottotitoli", time.strftime("sottotitoli_blocchi_fino_al_%Y-%m-%d_%H%M.json")))
    bl = sc.blocchi(parole_montato(a.video, pz), pz["durata"])
    json.dump(bl, open(fjson, "w"), ensure_ascii=False, indent=1)
    sc.srt(bl, os.path.join(a.video, "sottotitoli.srt"))
    for b in bl:
        print(f"{b['da']:7.2f} {b['a']:7.2f}  {b['testo']!r}")
    print(f"\n{len(bl)} blocchi in {fjson}: rileggili e correggi i testi prima del montaggio")


# ---------------------------------------------------------------- montaggio
def collega(sorg, dest):
    """Link fisico (stesso disco, nessuno spazio in più); se il file è HDR lo converte invece di collegarlo."""
    if os.path.exists(dest):
        os.remove(dest)
    if sonda(sorg)["hdr"]:
        subprocess.run([FF, "-v", "error", "-y", "-i", sorg, "-an", "-vf", f"{TONEMAP},{VERTICALE}", *X264, dest], check=True)
        return "convertito da HDR"
    try:
        os.link(sorg, dest)
    except OSError:
        shutil.copy2(sorg, dest)
    return ""


def trova_clip(nome, cartelle):
    for c in cartelle:
        if c and os.path.exists(os.path.join(c, nome)):
            return os.path.join(c, nome)
    sys.exit(f"b-roll {nome}: non trovato in {[c for c in cartelle if c]}")


def chunks_ref2(blocchi):
    out = []
    for b in blocchi:
        p = b["parole"]
        k, car = 0, 0
        while k < len(p) and (k == 0 or car + len(p[-1 - k][0]) + 1 <= 16):
            car += len(p[-1 - k][0]) + 1; k += 1
        small, big = p[:len(p) - k], p[len(p) - k:]
        out.append({"start": b["da"], "end": b["a"], "small": [{"t": x[0], "at": round(x[1], 3)} for x in small],
                    "big": {"t": " ".join(x[0] for x in big), "at": round(big[0][1], 3)}, "red": False})
    return out


def aspetto(stile_json, video=None):
    a = {"font": "Inter", "peso": 900, "dimensione": 52, "colore": "#FFFFFF", "bordo": "#000000", "bordo_px": 4,
         "evidenza": None, "y": 1240}
    if stile_json:
        s = json.load(open(stile_json))
        y = s.get("regole", {}).get("posizione_y")
        if y is not None:                                  # CapCut: y da -1 (fondo) a 1 (cima)
            a["y"] = round(960 - y * 960)
        st = s.get("stile_testo", {})
        col = st.get("fill", {}).get("content", {}).get("solid", {}).get("color")
        if col:
            a["colore"] = "#%02X%02X%02X" % tuple(round(c * 255) for c in col)
        if st.get("strokes"):
            sc = st["strokes"][0]["content"]["solid"]["color"]
            a["bordo"] = "#%02X%02X%02X" % tuple(round(c * 255) for c in sc)
        font = os.path.basename(st.get("font", {}).get("path", "")).lower()
        a["font"] = "Montserrat" if "montserrat" in font else "Poppins" if "poppins" in font else "Inter"
        blu = s.get("stile_blu", {}).get("fill", {}).get("content", {}).get("solid", {}).get("color")
        if blu:                                            # keyword fisse del brand: cifre e parole di parole_in_blu
            a["colore_blu"] = "#%02X%02X%02X" % tuple(round(c * 255) for c in blu)
            a["parole_blu"] = [w.upper() for w in s.get("parole_in_blu", []) if " " not in w and not w[0].isdigit()]
        a.update(s.get("remotion", {}))                    # ritocchi propri del metodo Remotion, se il cliente li ha
    if video and os.path.exists(os.path.join(video, "_build", "parole_blu.json")):
        a["parole_blu"] = json.load(open(os.path.join(video, "_build", "parole_blu.json")))   # scelta del singolo video
    return a


def montaggio(a):
    w = lavoro(a.video); pub = os.path.join(w, "public")
    pz = json.load(open(os.path.join(w, "parlato.json")))
    durata = pz["durata"]
    m = {"titolo": os.path.basename(os.path.abspath(a.video)), "durata": durata, "parlato": {"file": "parlato.mp4", "durata": durata},
         "segmenti": [{"start": p["start"], "end": p["end"]} for p in pz["pezzi"]],
         "zoom": {"attivo": not a.senza_zoom, "livelli": [1.0, a.zoom], "rampa_s": 0.6, "deriva": a.deriva},
         "broll": [], "transizioni": [], "outro": None, "sottotitoli": {"stile": "nessuno"}}

    # effetti sonori delle transizioni
    os.makedirs(os.path.join(pub, "sfx"), exist_ok=True)
    for f in os.listdir(os.path.join(REMOTION, "public", "sfx")):
        collega(os.path.join(REMOTION, "public", "sfx", f), os.path.join(pub, "sfx", f))

    piano = primo(a.piano, os.path.join(a.video, "piano_broll.json"), os.path.join(a.video, "_build", "piano_broll.json"))
    if piano:
        os.makedirs(os.path.join(pub, "broll"), exist_ok=True)
        cartelle = [a.cartella_clip, os.path.join(a.video, "BROLL_USATI"), os.path.join(a.video, "BROLL")]
        for x in json.load(open(piano)):
            sorg = trova_clip(x["clip"], cartelle)
            nota = collega(sorg, os.path.join(pub, "broll", x["clip"]))
            serve = x["a"] - x["da"] + x.get("offset", 0)
            if sonda(sorg)["durata"] + 0.02 < serve:
                sys.exit(f"{x['clip']}: servono {serve:.2f} s, la clip ne ha {sonda(sorg)['durata']:.2f}")
            m["broll"].append({"file": f"broll/{x['clip']}", "da": x["da"], "a": min(x["a"], durata), "offset": x.get("offset", 0),
                               "push_in": x.get("push_in", True)})
            if nota:
                print(f"  {x['clip']}: {nota}")
        print(f"{len(m['broll'])} b-roll da {piano}")
    else:
        print("nessun piano b-roll: montaggio senza b-roll")

    if a.transizioni == "auto":
        tagli = []
        for b in sorted(m["broll"], key=lambda b: b["da"]):
            for t in (b["da"], b["a"]):
                if 0.3 < t < durata - 0.05 and not any(abs(t - u) < 0.25 for u in tagli):
                    tagli.append(round(t, 3))
        for i, t in enumerate(sorted(tagli)):
            m["transizioni"].append({"at": t, "kind": "swoosh", "dir": -1 if i % 4 == 0 else 1} if i % 2 == 0 else {"at": t, "kind": "flash"})

    if a.outro:
        nota = collega(a.outro, os.path.join(pub, "outro" + os.path.splitext(a.outro)[1]))
        m["outro"] = {"file": "outro" + os.path.splitext(a.outro)[1], "da": durata, "durata": round(round(sonda(a.outro)["durata"] * FPS) / FPS, 4)}
        m["durata"] = round(durata + m["outro"]["durata"], 4)
        print(f"outro {os.path.basename(a.outro)} {m['outro']['durata']:.2f} s {nota}")

    fg = os.path.join(a.video, "grafiche.json")
    if os.path.exists(fg):                                   # grafiche animate: nome, etichetta, scheda (_REMOTION/src/templates/grafiche)
        m["grafiche"] = json.load(open(fg))
        print(f"{len(m['grafiche']['elenco'])} grafiche da {fg}")

    fm = os.path.join(a.video, "musica.json")
    if os.path.exists(fm):                                   # musica di sottofondo: {"file", "offset", "punti": [[s, volume], ...]}
        mu = json.load(open(fm))
        collega(os.path.join(a.video, mu["file"]), os.path.join(pub, "musica" + os.path.splitext(mu["file"])[1]))
        m["musica"] = {"file": "musica" + os.path.splitext(mu["file"])[1], "offset": mu.get("offset", 0), "punti": mu["punti"]}
        print(f"musica {mu['file']}, {len(mu['punti'])} punti di volume")

    fs = os.path.join(a.video, "sottotitoli_blocchi.json")
    if a.sottotitoli != "nessuno":
        if not os.path.exists(fs):
            sys.exit(f"manca {fs}: prima remotion.py sottotitoli, oppure --sottotitoli nessuno")
        bl = json.load(open(fs))
        schede = [(g["da"], g["a"]) for g in (m.get("grafiche") or {}).get("elenco", []) if g["tipo"] == "scheda"]
        # I sottotitoli restano anche sopra le schede ("chi lo vede non sempre ha l'audio
        # attivo"); la scheda tiene il suo contenuto sopra i 1150 px. La vecchia regola si riattiva con --via-sotto-schede.
        if schede and a.via_sotto_schede:
            # nessun sottotitolo sopra una scheda: quelli a cavallo partono quando la scheda è uscita, o finiscono quando
            # entra (tolto del tutto lasciava il b-roll senza la sua frase), o si tolgono
            tenuti, via = [], 0
            for b in bl:
                b = dict(b)
                for s_da, s_a in schede:
                    if b["da"] < s_a and b["a"] > s_da:
                        if b["a"] - s_a >= 0.5 and b["da"] >= s_da:
                            b["da"] = round(s_a + 0.02, 3)
                        elif s_da - b["da"] >= 0.5 and b["a"] <= s_a:
                            b["a"] = round(s_da, 3)
                        else:
                            b = None
                            break
                if b is None:
                    via += 1
                else:
                    tenuti.append(b)
            bl = tenuti
            print(f"{via} sottotitoli tolti sotto le schede")
        if a.sottotitoli == "dinamici":                      # parole a tempo davanti, parole chiave enormi dietro la persona
            dietro, fd = [], os.path.join(a.video, "dietro.json")
            if os.path.exists(fd):
                os.makedirs(os.path.join(pub, "dietro"), exist_ok=True)
                for d in json.load(open(fd)):
                    collega(os.path.join(a.video, d["file"]), os.path.join(pub, "dietro", os.path.basename(d["file"])))
                    dietro.append({**d, "file": "dietro/" + os.path.basename(d["file"])})
            m["sottotitoli"] = {"stile": "dinamici", "blocchi": bl, "aspetto": aspetto(a.stile, a.video), "dietro": dietro}
            print(f"{len(bl)} sottotitoli dinamici, {len(dietro)} parole dietro la persona")
            json.dump(m, open(os.path.join(w, "montaggio.json"), "w"), ensure_ascii=False, indent=1)
            json.dump({"m": m}, open(os.path.join(w, "props.json"), "w"), ensure_ascii=False)
            print(f"{os.path.join(w, 'montaggio.json')}: {m['durata']:.2f} s, {len(m['transizioni'])} transizioni")
            return
        m["sottotitoli"] = ({"stile": "blocchi", "blocchi": bl, "aspetto": aspetto(a.stile, a.video)} if a.sottotitoli == "blocchi"
                            else {"stile": "ref2", "chunks": chunks_ref2(bl), "y": 1170})
        print(f"{len(bl)} sottotitoli, stile {a.sottotitoli}")

    json.dump(m, open(os.path.join(w, "montaggio.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"m": m}, open(os.path.join(w, "props.json"), "w"), ensure_ascii=False)
    print(f"{os.path.join(w, 'montaggio.json')}: {m['durata']:.2f} s, {len(m['transizioni'])} transizioni")


# ---------------------------------------------------------------- render e studio
def props(video):
    w = os.path.abspath(lavoro(video))
    p = os.path.join(w, "props.json")
    if not os.path.exists(p):
        sys.exit("manca props.json: prima remotion.py montaggio")
    return w, p


def render(a):
    w, p = props(a.video)
    out = os.path.abspath(os.path.join(a.video, "ANTEPRIMA_remotion_540p.mp4" if a.anteprima else "EXPORT_remotion.mp4"))
    if os.path.exists(out):
        vecchi = os.path.join(a.video, "_build", "export_precedenti"); os.makedirs(vecchi, exist_ok=True)
        shutil.move(out, os.path.join(vecchi, time.strftime("%Y-%m-%d_%H%M_") + os.path.basename(out)))
    cmd = ["npx", "remotion", "render", "Montaggio", out, f"--props={p}", f"--public-dir={os.path.join(w, 'public')}",
           "--codec=h264", "--audio-codec=aac", "--audio-bitrate=256k"]
    cmd += ["--scale=0.5", "--crf=26"] if a.anteprima else ["--crf=17"]
    t0 = time.time()
    subprocess.run(cmd, cwd=REMOTION, check=True)
    print(f"{out}: {sonda(out)['durata']:.2f} s, {os.path.getsize(out) / 1e6:.1f} MB, in {time.time() - t0:.0f} s")


def studio(a):
    w, p = props(a.video)
    subprocess.run(["npx", "remotion", "studio", f"--props={p}", f"--public-dir={os.path.join(w, 'public')}"], cwd=REMOTION)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    x = sub.add_parser("parlato"); x.add_argument("video"); x.add_argument("--tagli"); x.add_argument("--girato")
    x.add_argument("--velocita", type=float, default=1.03); x.add_argument("--audio", choices=["auto", "elaborato", "grezzo"], default="auto")
    x.add_argument("--loudness", type=float, default=None, help="es. -14: normalizza la voce. Di default no (regola 8)")
    x = sub.add_parser("da-capcut"); x.add_argument("video"); x.add_argument("--progetto", required=True); x.add_argument("--export", required=True)
    x = sub.add_parser("sottotitoli"); x.add_argument("video"); x.add_argument("--stile", required=True); x.add_argument("--rifai", action="store_true")
    x = sub.add_parser("montaggio"); x.add_argument("video"); x.add_argument("--piano"); x.add_argument("--cartella-clip")
    x.add_argument("--outro"); x.add_argument("--sottotitoli", choices=["blocchi", "dinamici", "ref2", "nessuno"], default="blocchi")
    x.add_argument("--stile"); x.add_argument("--transizioni", choices=["auto", "nessuna"], default="auto")
    x.add_argument("--senza-zoom", action="store_true")
    # girato a bassa risoluzione o volto basso nell'inquadratura: zoom più leggero (su un reel girato così: 1.08 e 0.003)
    x.add_argument("--zoom", type=float, default=1.12, help="secondo livello dello zoom sui tagli (il primo è 1.0)")
    x.add_argument("--deriva", type=float, default=0.006, help="push-in lento dentro ogni pezzo, in zoom al secondo")
    x.add_argument("--via-sotto-schede", action="store_true", help="toglie i sottotitoli sotto le schede (la vecchia regola)")
    x = sub.add_parser("render"); x.add_argument("video"); x.add_argument("--anteprima", action="store_true")
    x = sub.add_parser("studio"); x.add_argument("video")
    a = ap.parse_args()
    a.video = os.path.abspath(a.video)
    {"parlato": parlato, "da-capcut": da_capcut, "sottotitoli": sottotitoli, "montaggio": montaggio, "render": render, "studio": studio}[a.passo](a)
