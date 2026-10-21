# -*- coding: utf-8 -*-
"""Sottotitoli in CapCut con lo stile di un cliente (file di stile json, per esempio stile_sottotitoli_<cliente>.json).

Tre passaggi, da lanciare in ordine:

  1. proposta   scrive i blocchi in <cartella>/sottotitoli_blocchi.json. Le parole vengono dalle trascrizioni delle
                riprese intere (<cartella>/_build/trascrizioni/, Scribe): solo se mancano trascrive la timeline con
                Whisper, che anticipa le parole di 0,16 s in mediana. Nessun blocco scavalca un taglio.
                python3 sottotitoli_capcut.py proposta "Nome progetto" --cartella <cartella video> --stile <stile.json>
     ricalcola   rifà i blocchi dalle parole già trascritte della timeline, senza ritrascrivere
     riallinea   dopo tagli nuovi, o su sottotitoli già scritti: tiene i testi del progetto (corretti a mano) e rifà
                tempi e divisioni sulle trascrizioni delle riprese
  2. rilettura  si correggono a mano i testi nel json (i tempi si possono lasciare)
  3. scrivi     con CapCut CHIUSO, scrive la traccia dei sottotitoli in tutte le copie del progetto
                python3 sottotitoli_capcut.py scrivi "Nome progetto" --cartella <cartella video> --stile <stile.json> [--traccia "Sottotitoli"]

Il nome progetto è quello che si vede nella home di CapCut, oppure il nome della cartella.
La chiave fal si legge con chiavi.py (.env del kit o ~/.claude/settings.json).
"""
import argparse, base64, copy, difflib, glob, json, os, re, shutil, subprocess, sys, time, uuid, urllib.request, wave

QUI = os.path.dirname(os.path.abspath(__file__))
STILE = None   # si carica da --stile
R = None
PROGETTI = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
FF = os.path.expanduser("~/.local/bin/ffmpeg")
NOME_TRACCIA = "Sottotitoli"
FPS_US = 1_000_000 / 30
DEBOLI = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con", "su",
          "per", "tra", "fra", "e", "o", "che", "del", "della", "dei", "delle", "al", "alla", "ai",
          "nel", "nella", "sul", "sulla", "non", "ma", "se", "ci", "mi", "ti", "si", "è", "ed", "ad"}


def uid():
    return str(uuid.uuid4()).upper()


def trova_progetto(nome):
    if os.path.isdir(nome) and os.path.exists(os.path.join(nome, "draft_info.json")):
        return os.path.abspath(nome)
    for cart in glob.glob(os.path.join(PROGETTI, "*")):
        meta = os.path.join(cart, "draft_meta_info.json")
        if not os.path.exists(meta):
            continue
        if os.path.basename(cart) == nome:
            return cart
        try:
            if json.load(open(meta)).get("draft_name") == nome:
                return cart
        except Exception:
            pass
    sys.exit(f"progetto non trovato: {nome}")


def copie_progetto(cart):
    c = [f"{cart}/draft_info.json", f"{cart}/draft_info.json.bak", f"{cart}/template-2.tmp"]
    c += glob.glob(f"{cart}/Timelines/*/draft_info.json") + glob.glob(f"{cart}/Timelines/*/draft_info.json.bak")
    c += glob.glob(f"{cart}/Timelines/*/template-2.tmp")
    return [f for f in c if os.path.exists(f)]


def traccia_parlato(d):
    vids = {v["id"]: v for v in d["materials"]["videos"]}
    for t in d["tracks"]:
        if t["type"] == "video" and any(vids.get(s["material_id"], {}).get("has_audio") for s in t["segments"]):
            return t, vids
    sys.exit("nessuna traccia video con audio")


# ---------------------------------------------------------------- 1. audio e trascrizione
def trascrivi(cart, lavoro):
    d = json.load(open(f"{cart}/draft_info.json"))
    tr, vids = traccia_parlato(d)
    vel = {s["id"]: s.get("speed", 1.0) for s in d["materials"].get("speeds", [])}
    segs = sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"])
    os.makedirs(f"{lavoro}/audio", exist_ok=True)
    tabella, lista = [], []
    pos = 0.0
    for i, s in enumerate(segs):
        m = vids[s["material_id"]]
        if not m.get("has_audio"):
            continue
        sr, tt = s["source_timerange"], s["target_timerange"]
        v = next((vel[r] for r in s["extra_material_refs"] if r in vel), s.get("speed", 1.0)) or 1.0
        out = f"{lavoro}/audio/{i:03d}.wav"
        subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-accurate_seek", "-ss", f"{sr['start']/1e6:.4f}",
                        "-i", m["path"], "-vn", "-af",
                        f"atrim=duration={sr['duration']/1e6:.6f},asetpts=N/SR/TB,atempo={v}",
                        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", out], check=True)
        with wave.open(out) as w:
            dur = w.getnframes() / w.getframerate()
        tabella.append({"audio_da": pos, "audio_a": pos + dur, "timeline_da": tt["start"] / 1e6,
                        "timeline_dur": tt["duration"] / 1e6})
        lista.append(out)
        pos += dur
    open(f"{lavoro}/audio/lista.txt", "w").write("\n".join(f"file '{p}'" for p in lista))
    mp3 = f"{lavoro}/parlato.mp3"
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                    f"{lavoro}/audio/lista.txt", "-c:a", "libmp3lame", "-b:a", "96k", mp3], check=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chiavi
    key = chiavi.fal()
    H = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    body = {"audio_url": "data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode(),
            "task": "transcribe", "language": "it", "chunk_level": "word"}
    sub = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://queue.fal.run/fal-ai/whisper", data=json.dumps(body).encode(), headers=H), timeout=120))
    for _ in range(240):
        time.sleep(5)
        st = json.load(urllib.request.urlopen(urllib.request.Request(sub["status_url"], headers=H), timeout=60))
        if st.get("status") == "COMPLETED":
            res = json.load(urllib.request.urlopen(urllib.request.Request(sub["response_url"], headers=H), timeout=60))
            break
        if st.get("status") in ("FAILED", "ERROR"):
            sys.exit(f"trascrizione fallita: {st}")
    else:
        sys.exit("trascrizione: timeout")

    # dal tempo dell'audio ricostruito al tempo della timeline, segmento per segmento
    def a_timeline(t):
        for r in tabella:
            if t <= r["audio_a"] + 1e-6:
                k = r["timeline_dur"] / max(r["audio_a"] - r["audio_da"], 1e-6)
                return r["timeline_da"] + (max(t, r["audio_da"]) - r["audio_da"]) * k
        r = tabella[-1]
        return r["timeline_da"] + r["timeline_dur"]

    parole = []
    for c in res.get("chunks", []):
        a, b = c["timestamp"]
        testo = c["text"].strip()
        if not testo:
            continue
        b = b if b is not None else a + 0.3
        # whisper spezza gli apostrofi: "C" + "'è", "mezz" + "'ora"
        if testo.startswith("'") and parole:
            parole[-1]["testo"] += testo
            parole[-1]["a"] = a_timeline(b)
            continue
        parole.append({"testo": testo, "da": a_timeline(a), "a": a_timeline(b)})
    fine_parlato = max(r["timeline_da"] + r["timeline_dur"] for r in tabella)
    json.dump({"parole": parole, "fine_parlato": fine_parlato}, open(f"{lavoro}/parole_timeline.json", "w"),
              ensure_ascii=False, indent=1)
    return parole, fine_parlato


def parole_riprese(d, cartella):
    """Parole del montato con i tempi della timeline, dalle trascrizioni delle riprese intere
    (<cartella>/_build/trascrizioni/<ripresa>.json, Scribe di trascrivi.py), segmento per segmento.
    Da preferire a trascrivi(): su un video di prova Whisper sulla timeline anticipava le parole
    di 0,16 s in mediana e di 0,29 nel 10% dei casi, mentre Scribe sulle riprese coincide con gli attacchi di voce
    misurati per i tagli. Ogni parola sa in quale clip sta ("clip", "clip_da"): un blocco non scavalca un taglio."""
    tr, vids = traccia_parlato(d)
    vel = {s["id"]: s.get("speed", 1.0) for s in d["materials"].get("speeds", [])}
    cache, parole, fine_parlato = {}, [], 0.0
    for i, s in enumerate(sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"])):
        m = vids[s["material_id"]]
        if not m.get("has_audio") or s.get("volume", 1.0) == 0:   # l'outro sta sulla traccia ma è muto
            continue
        rip = os.path.splitext(os.path.basename(m["path"]))[0]
        f = os.path.join(cartella, "_build", "trascrizioni", rip + ".json")
        if not os.path.exists(f):
            sys.exit(f"manca la trascrizione della ripresa {rip} ({f}): trascrivi.py --diarizza")
        if rip not in cache:
            cache[rip] = [w for w in json.load(open(f))["words"] if w.get("type", "word") == "word"]
        v = next((vel[r] for r in s["extra_material_refs"] if r in vel), s.get("speed", 1.0)) or 1.0
        s0, sd = s["source_timerange"]["start"] / 1e6, s["source_timerange"]["duration"] / 1e6
        t0, td = s["target_timerange"]["start"] / 1e6, s["target_timerange"]["duration"] / 1e6
        for w in cache[rip]:
            if s0 <= (w["start"] + w["end"]) / 2 <= s0 + sd:
                parole.append({"testo": w["text"].strip(), "da": t0 + max(0.0, w["start"] - s0) / v,
                               "a": t0 + min(sd, w["end"] - s0) / v, "clip": i, "clip_da": t0})
        fine_parlato = max(fine_parlato, t0 + td)
    return parole, fine_parlato


# ---------------------------------------------------------------- 2. blocchi
def pulisci(t):
    t = re.sub(r"[^\w\s'’àèéìíòóùúÀÈÉÌÍÒÓÙÚ]", "", t).replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def a_capo(t):
    if len(t) <= R["a_capo_oltre_caratteri"]:
        return t
    w = t.split(" ")
    def peso(i):
        return abs(len(" ".join(w[:i])) - len(" ".join(w[i:]))) + (8 if w[i - 1].lower() in DEBOLI else 0)
    migliore = min(range(1, len(w)), key=peso)
    return " ".join(w[:migliore]) + " \n" + " ".join(w[migliore:])


# parole su cui un blocco non deve finire: articoli, preposizioni, dimostrativi, numeri e ausiliari
# che reggono la parola dopo ("sullo stesso | pezzo", "viene | diviso", "tre | costi")
DEBOLI_FINE = DEBOLI | {"quello", "quella", "questo", "questa", "quelle", "quei", "questi", "queste",
                        "quelli", "quegli", "mio", "mia", "nostro", "nostra", "suo", "sua", "più", "molto", "tutta", "tutto",
                        "sullo", "sugli", "sulle", "dello", "degli", "nello", "negli", "allo", "agli",
                        "alle", "dal", "dalla", "dai", "dagli", "col", "stesso", "stessa", "stessi", "stesse",
                        "ogni", "qualche", "quale", "quali", "due", "tre", "quattro", "cinque", "sei",
                        "viene", "vengono", "sono", "ha", "hanno", "ho", "abbiamo", "deve", "devono", "può",
                        "possono", "dobbiamo", "possiamo", "stato", "stata", "essere", "sia"}


def blocchi(parole, fine_parlato):
    """Divide le parole in blocchi scegliendo i tagli migliori su tutta la sequenza (programmazione dinamica)."""
    n = len(parole)
    txt = [pulisci(p["testo"]) for p in parole]
    fine_frase = [bool(re.search(r"[.?!…]$", p["testo"])) for p in parole]
    virgola = [bool(re.search(r"[,;:]$", p["testo"])) for p in parole]
    pausa = [(parole[i + 1]["da"] - parole[i]["a"]) if i + 1 < n else 9 for i in range(n)]
    IDEALE, MAX = R.get("caratteri_ideali_blocco", 22), R["caratteri_max_blocco"]

    def costo(i, j):  # blocco con le parole i..j comprese
        if j - i + 1 > R["parole_max_blocco"]:
            return None
        if any(fine_frase[k] for k in range(i, j)):  # una frase finita non continua nello stesso blocco
            return None
        if parole[i].get("clip") != parole[j].get("clip"):  # né scavalca un taglio: mostrerebbe la clip dopo in anticipo
            return None
        car = len(" ".join(txt[i:j + 1]))
        if car > MAX:
            return None
        c = ((car - IDEALE) / 9.0) ** 2
        ultima = txt[j].lower()
        if j < n - 1:
            if ultima in DEBOLI_FINE and not virgola[j]:
                c += 4
            if not (fine_frase[j] or virgola[j] or pausa[j] > 0.25):
                c += 2.5
            if pausa[j] > 0.25:
                c -= 1
            if virgola[j]:
                c -= 1.5
        if j == i and car < 9 and not (virgola[j] or fine_frase[j]):
            c += 3
        if parole[j]["a"] - parole[i]["da"] > 3.2:
            c += 3
        if j < n - 1 and parole[j]["a"] - parole[i]["da"] < R["durata_min_s"]:  # "MA QUANDO" a video 0,45 s
            c += 4
        return c

    best = [0.0] + [float("inf")] * n
    da = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - R["parole_max_blocco"]), j):
            c = costo(i, j - 1)
            if c is not None and best[i] + c < best[j]:
                best[j], da[j] = best[i] + c, i
    tagli, j = [], n
    while j > 0:
        tagli.append((da[j], j - 1)); j = da[j]
    tagli.reverse()
    out = []
    for i, j in tagli:
        g = parole[i:j + 1]
        testo = pulisci(" ".join(x["testo"] for x in g)).upper()
        if testo:
            out.append(blocco(testo, g))
    return tempi(out, fine_parlato)


def blocco(testo, g):
    # mai prima dell'inizio della sua clip
    return {"da": round(max(g[0].get("clip_da", 0.0), g[0]["da"] - 0.05), 3), "a": round(g[-1]["a"] + 0.20, 3),
            "testo": a_capo(testo), "parole": [[x["testo"], round(x["da"], 3), round(x["a"], 3)] for x in g]}


def tempi(out, fine_parlato):
    # attaccati come nel video 06: se il buco col successivo è breve, il blocco arriva fino a lì; mai sovrapposti
    for i, b in enumerate(out):
        b["a"] = min(max(b["a"], b["da"] + R["durata_min_s"]), fine_parlato)
        if i + 1 < len(out):
            nxt = out[i + 1]["da"]
            if nxt - b["a"] < 0.6:
                b["a"] = nxt - R["stacco_fra_blocchi_s"]
            b["a"] = round(min(b["a"], nxt - R["stacco_fra_blocchi_s"]), 3)
    return out


def blocchi_progetto(d):
    """Testi dei sottotitoli già nel progetto, in ordine: [(inizio, testo)]."""
    texts = {m["id"]: m for m in d["materials"].get("texts", [])}
    tr = traccia_sottotitoli(d)
    if tr is None:
        sys.exit(f"nel progetto non trovo la traccia '{NOME_TRACCIA}'")
    out = []
    for s in sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"]):
        c = texts[s["material_id"]]["content"]
        out.append((s["target_timerange"]["start"] / 1e6, json.loads(c)["text"] if c.startswith("{") else c))
    return out


def riallinea(cart, cartella):
    """Dopo tagli nuovi, o per rifare i tempi: tiene i testi dei sottotitoli nel progetto (corretti a mano, anche
    dall'utente) e rifà tempi e divisioni sulle parole delle riprese. Un blocco che scavalca un taglio si divide, e il
    pezzo corto che ne nasce (sotto 9 caratteri o 0,5 s) va col blocco vicino della stessa clip, se ci sta."""
    d = json.load(open(f"{cart}/draft_info.json"))
    parole, fine = parole_riprese(d, cartella)
    vecchi = blocchi_progetto(d)
    tok = [(bi, x) for bi, (_, t) in enumerate(vecchi) for x in t.split()]
    norm = lambda s: re.sub(r"[^\w']", "", s.lower().replace("’", "'"))
    sm = difflib.SequenceMatcher(None, [norm(x) for _, x in tok], [norm(p["testo"]) for p in parole], autojunk=False)
    dove, sciolte = [None] * len(tok), 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("equal", "replace"):
            for k in range(i1, i2):
                dove[k] = j1 + min(j2 - j1 - 1, (k - i1) * (j2 - j1) // (i2 - i1))
        elif op == "delete":
            sciolte += i2 - i1
    for k in range(len(dove)):  # parole del testo che l'audio non ha: prendono il posto della vicina
        if dove[k] is None:
            dove[k] = dove[k - 1] if k and dove[k - 1] is not None else next((x for x in dove[k:] if x is not None), 0)
    pezzi = []
    for k, (bi, x) in enumerate(tok):
        c = parole[dove[k]]["clip"]
        if pezzi and pezzi[-1]["bi"] == bi and pezzi[-1]["clip"] == c:
            pezzi[-1]["k"].append(k)
        else:
            pezzi.append({"bi": bi, "clip": c, "k": [k], "diviso": bool(pezzi) and pezzi[-1]["bi"] == bi})
    # le clip toccate da un blocco a cavallo di un taglio si ridividono per intero con le regole del cliente, sui testi
    # corretti (dividere e basta lascia pezzi da 0,3 s: "PRIMA", "SE C'È"); le altre restano come erano state riviste
    rifare = {p["clip"] for p in pezzi if p["diviso"]} | {pezzi[i - 1]["clip"] for i, p in enumerate(pezzi) if p["diviso"]}
    punto = lambda s: re.search(r"[.,;:?!…]*$", s).group(0)
    nuovi, i = [], 0
    while i < len(pezzi):
        c = pezzi[i]["clip"]
        if c not in rifare:
            nuovi.append(pezzi[i]); i += 1
            continue
        ks = []
        while i < len(pezzi) and pezzi[i]["clip"] == c:
            ks += pezzi[i]["k"]; i += 1
        pos = 0
        for b in blocchi([dict(parole[dove[k]], testo=tok[k][1] + punto(parole[dove[k]]["testo"])) for k in ks], fine):
            n = len(b["parole"]); nuovi.append({"clip": c, "k": ks[pos:pos + n]}); pos += n
    testo = lambda p: " ".join(tok[k][1] for k in p["k"])
    out = [blocco(testo(p), [parole[dove[k]] for k in p["k"]]) for p in nuovi]
    print(f"{len(vecchi)} sottotitoli nel progetto, {len(tok)} parole ({sciolte} senza corrispondenza nell'audio), "
          f"{len(rifare)} clip ridivise perché un blocco scavalcava un taglio: {len(out)} blocchi")
    return tempi(out, fine), fine


def traccia_sottotitoli(d):
    for t in d["tracks"]:
        if t.get("name") == NOME_TRACCIA:
            return t
    testo = [t for t in d["tracks"] if t["type"] == "text"]
    # CapCut a volte toglie il nome alla traccia : se c'è una sola traccia di testo
    # e ha l'aria dei sottotitoli, è quella
    if len(testo) == 1 and len(testo[0]["segments"]) >= 10:
        return testo[0]
    return None


# ---------------------------------------------------------------- 3. scrittura nel progetto
def contenuto(testo):
    st = copy.deepcopy(STILE["stile_testo"])
    st["range"] = [0, len(testo)]
    return json.dumps({"styles": [st], "text": testo}, ensure_ascii=False)


def scrivi(cart, blocchi_, cartella):
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0 and \
            os.path.realpath(cart).startswith(os.path.realpath(PROGETTI)):
        sys.exit("CapCut è aperto: va chiuso prima di scrivere, altrimenti al salvataggio sovrascrive tutto")
    bk = os.path.join(cartella, time.strftime("_BACKUP_CAPCUT_prima-sottotitoli_%Y-%m-%d_%H%M"))
    shutil.copytree(cart, bk)
    gruppo = f"it-IT_{int(time.time()*1000)}"
    for f in copie_progetto(cart):
        d = json.load(open(f))
        # se lo script è già passato, via la traccia vecchia e i suoi materiali
        vecchi = set()
        vecchia = traccia_sottotitoli(d)
        if vecchia is not None:
            for s in vecchia["segments"]:
                vecchi.add(s["material_id"]); vecchi.update(s.get("extra_material_refs", []))
        d["tracks"] = [t for t in d["tracks"] if t is not vecchia]
        for k, l in d["materials"].items():
            if isinstance(l, list):
                d["materials"][k] = [m for m in l if not (isinstance(m, dict) and m.get("id") in vecchi)]
        d["materials"].setdefault("texts", []); d["materials"].setdefault("material_animations", [])
        tr = copy.deepcopy(STILE["traccia"]); tr["id"] = uid(); tr["name"] = NOME_TRACCIA
        tr["is_default_name"] = False; tr["segments"] = []
        for i, b in enumerate(blocchi_):
            da = int(round(round(b["da"] * 1e6 / FPS_US) * FPS_US)); a = int(round(round(b["a"] * 1e6 / FPS_US) * FPS_US))
            if a - da < FPS_US:
                continue
            m = copy.deepcopy(STILE["materiale_testo"]); m["id"] = uid(); m["group_id"] = gruppo
            m["content"] = contenuto(b["testo"])
            m["recognize_text"] = " ".join(p[0] for p in b.get("parole", [])).lower()
            m["words"] = {"start_time": [int((p[1] - b["da"]) * 1000) for p in b.get("parole", [])],
                          "end_time": [int((p[2] - b["da"]) * 1000) for p in b.get("parole", [])],
                          "text": [p[0] for p in b.get("parole", [])]}
            base = json.loads(m.get("base_content") or '{"styles":[{}],"text":""}')
            base["text"] = m["recognize_text"]
            if base.get("styles"):
                base["styles"][0]["range"] = [0, len(m["recognize_text"])]
            m["base_content"] = json.dumps(base, ensure_ascii=False)
            d["materials"]["texts"].append(m)
            an = copy.deepcopy(STILE["animazione"]); an["id"] = uid()
            d["materials"]["material_animations"].append(an)
            s = copy.deepcopy(STILE["segmento"]); s["id"] = uid(); s["material_id"] = m["id"]
            s["extra_material_refs"] = [an["id"]]
            s["target_timerange"] = {"start": da, "duration": a - da}
            s["render_index"] = 14000 + i
            tr["segments"].append(s)
        d["tracks"].append(tr)
        json.dump(d, open(f, "w"), ensure_ascii=False)
    print(f"scritti {len(blocchi_)} sottotitoli su {len(copie_progetto(cart))} copie; backup in {bk}")


def srt(blocchi_, percorso):
    def tc(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); mi, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{mi:02d}:{s:02d},{ms:03d}"
    with open(percorso, "w") as f:
        for i, b in enumerate(blocchi_, 1):
            f.write(f"{i}\n{tc(b['da'])} --> {tc(b['a'])}\n{b['testo'].replace(' ' + chr(10), chr(10))}\n\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("passo", choices=["proposta", "ricalcola", "riallinea", "scrivi"])
    ap.add_argument("progetto")
    ap.add_argument("--cartella", required=True, help="cartella del video, dove vanno json, srt e backup")
    ap.add_argument("--stile", required=True, help="json di stile del cliente (regole, stile_testo, materiale_testo, segmento, animazione, traccia)")
    ap.add_argument("--traccia", default="Sottotitoli", help="nome della traccia testo nel progetto")
    a = ap.parse_args()
    STILE = json.load(open(a.stile)); R = STILE["regole"]; NOME_TRACCIA = a.traccia
    cart = trova_progetto(a.progetto)
    os.makedirs(a.cartella, exist_ok=True)
    fjson = os.path.join(a.cartella, "sottotitoli_blocchi.json")
    if a.passo in ("proposta", "ricalcola", "riallinea"):
        lavoro = os.path.join(a.cartella, "_build", "sottotitoli")
        os.makedirs(lavoro, exist_ok=True)
        if os.path.exists(fjson):  # la versione precedente non si perde
            shutil.copy(fjson, os.path.join(lavoro, time.strftime("sottotitoli_blocchi_fino_al_%Y-%m-%d_%H%M.json")))
        if a.passo == "riallinea":
            bl, fine = riallinea(cart, a.cartella)
        else:
            if a.passo == "ricalcola":
                pt = json.load(open(os.path.join(lavoro, "parole_timeline.json")))
                parole, fine = pt["parole"], pt["fine_parlato"]
            elif os.path.isdir(os.path.join(a.cartella, "_build", "trascrizioni")):
                parole, fine = parole_riprese(json.load(open(f"{cart}/draft_info.json")), a.cartella)
            else:
                parole, fine = trascrivi(cart, lavoro)
            bl = blocchi(parole, fine)
        json.dump(bl, open(fjson, "w"), ensure_ascii=False, indent=1)
        srt(bl, os.path.join(a.cartella, "sottotitoli.srt"))
        for b in bl:
            print(f"{b['da']:7.2f} {b['a']:7.2f}  {b['testo']!r}")
        print(f"\n{len(bl)} blocchi in {fjson}: rileggili, correggi i testi, poi passo 'scrivi' con CapCut chiuso")
    else:
        bl = json.load(open(fjson))
        srt(bl, os.path.join(a.cartella, "sottotitoli.srt"))
        scrivi(cart, bl, a.cartella)
