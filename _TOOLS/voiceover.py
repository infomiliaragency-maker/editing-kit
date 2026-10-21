# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = ["kokoro-onnx", "soundfile", "numpy"]
# ///
"""Voiceover con cinque motori.

  "motore": "chatterbox-fal"  Chatterbox Multilingual (MIT) eseguito su fal, circa 0,025 $ ogni 1000 caratteri.
                              Più naturale: intonazione e pause vere. Timbro preso da "riferimento" (10-15 s di voce).
                              Default: Kokoro è stata bocciata come "troppo robotica".
  "motore": "kokoro"          Kokoro-82M (Apache 2.0) in locale, gratis, più piatta. Modello non incluso nel kit.
  "motore": "gemini-tts-fal"  Gemini 3.1 Flash TTS su fal, voce "voce" (default Achernar), "stile" (istruzioni di tono in
                              italiano, default STILE_GEMINI), "temperatura" (default 1). Una registrazione per tutte le
                              battute, tagliata sulle parole di Scribe. Scelta alla cieca fra nove voci per reel di una
                              clinica. Non serve accelerarla.
  "motore": "gemini-38"       Gemini 3.8 Flash TTS chiamato direttamente da Google (Gemini API, quota gratuita di AI Studio;
                              dall'Italia valgono i termini del piano a pagamento, i testi non addestrano i modelli). Chiave
                              GEMINI_API_KEY nel .env del kit (aistudio.google.com). "voce" è una voce pronta
                              (Kore, Achernar, Aoede...) o l'id "voice_..." di una voce disegnata con `disegna`; "stile" è una
                              frase breve (la guida Google sconsiglia istruzioni lunghe: la voce deriva). Stesso taglio sulle
                              parole di Scribe di gemini-tts-fal. Ogni audio porta il watermark SynthID.
                              Le voci disegnate appartengono all'account Google che le crea: quelle di un
                              altro account non funzionano.
  "motore": "eleven-v3-fal"   ElevenLabs v3 su fal, voce "voce" (default Laura), lingua "lingua" (default it), "stabilita"
                              0-1 (default 0.5). Preferito a Chatterbox, che usciva piatta, in una prova
                              su otto voci. Tutte le battute escono da UNA sola
                              registrazione, così l'intonazione scorre da una frase all'altra, poi si tagliano sui tempi dei
                              caratteri che ElevenLabs restituisce; le battute con "a_parte": true (la firma) si registrano da
                              sole. Ogni battuta può avere "tag" (es. "[curious]"), messo davanti al testo, oppure
                              "testo_voce" con i tag dentro la frase: il "testo" resta quello pulito per sottotitoli e verifica.

  uv run voiceover.py genera   <testo.json> --out <cartella>   # una battuta per file, più voiceover.json con le durate
  uv run voiceover.py verifica <cartella>                       # ritrascrive con Scribe e confronta col testo
  uv run voiceover.py disegna --nome "Sara" --genere female --descrizione "..." --out <cartella>
                                                                # crea una voce Gemini 3.8 da una descrizione, salva
                                                                # l'id in _modelli/voci/gemini_voci.json e l'anteprima

testo.json:
  {"voce": "if_sara", "velocita": 1.0,
   "pronuncia": {"Patient Care": "Pèiscent Chèr", ...},     # grafia fonetica data alla voce, il testo resta quello vero
   "battute": [{"scena": "logo", "testo": "..."}, ...]}

Chatterbox: "riferimento" (default _modelli/voci/sara_kokoro_rif.wav, voce femminile generata con Kokoro, nessun
diritto di terzi), "espressivita" 0.25-2 (default 0.65), "guida" 0-1 (default 0.4), "seed". Massimo 300 caratteri a battuta.
La voce "italian" già pronta di fal è maschile (137 Hz).
Kokoro: voci italiane if_sara (femminile), im_nicola (maschile). Modello in _TOOLS/_modelli/kokoro/.
Le parole inglesi lette da una voce italiana escono all'italiana: si correggono in "pronuncia", poi verifica.
Claude non ascolta: verifica misura quanto Scribe riconosce il testo, l'ascolto finale spetta all'utente.
"""
import argparse, difflib, json, os, re, subprocess, sys
import numpy as np, soundfile as sf

QUI = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(QUI, "_modelli", "kokoro")
SR = 48000


def per_voce(testo, pron):
    for k in sorted(pron, key=len, reverse=True):
        testo = re.sub(re.escape(k), pron[k], testo)
    return testo


def chatterbox(cfg):
    import time, urllib.request, tempfile
    sys.path.insert(0, QUI)
    from trascrivi import req, carica
    rif = cfg.get("riferimento") or os.path.join(QUI, "_modelli", "voci", "sara_kokoro_rif.wav")
    if not os.path.exists(rif):
        sys.exit(f"manca la voce di riferimento {rif}: metti in testo.json \"riferimento\" con 10-15 s di voce pulita")
    mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", rif, "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k", mp3], check=True)
    url = carica(mp3)

    def crea(testo, b):
        if len(testo) > 300:
            sys.exit(f"battuta di {len(testo)} caratteri, Chatterbox ne accetta 300: dividerla")
        corpo = {"text": testo, "voice": url, "custom_audio_language": "italian",
                 "exaggeration": b.get("espressivita", cfg.get("espressivita", 0.65)),
                 "cfg_scale": b.get("guida", cfg.get("guida", 0.4)), "seed": b.get("seed", cfg.get("seed", 7))}
        sub = req("https://queue.fal.run/fal-ai/chatterbox/text-to-speech/multilingual", corpo)
        for _ in range(150):
            time.sleep(2)
            st = req(sub["status_url"])
            if st["status"] == "COMPLETED":
                break
            if st["status"] in ("FAILED", "ERROR"):
                sys.exit(f"fal: {st}")
        f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        urllib.request.urlretrieve(req(sub["response_url"])["audio"]["url"], f)
        s, sr = sf.read(f)
        os.remove(f)
        return (s.mean(1) if s.ndim > 1 else s), sr
    return crea


def eleven_v3(cfg, cartella):
    """Una registrazione per tutte le battute (più una per ogni battuta "a_parte"), tagliata sui tempi dei caratteri."""
    import tempfile, urllib.request
    sys.path.insert(0, QUI)
    import genera_broll as g
    os.makedirs(cartella, exist_ok=True)
    def frase(b):
        t = b.get("testo_voce") or ((b["tag"] + " ") if b.get("tag") else "") + b["testo"]
        return per_voce(t, cfg.get("pronuncia", {}))
    def registra(battute):
        pezzi, testo = [], ""
        for b in battute:
            if testo: testo += " "
            pezzi.append((len(testo), len(testo) + len(frase(b)))); testo += frase(b)
        r = g.coda("fal-ai/elevenlabs/tts/eleven-v3", {"text": testo, "voice": cfg.get("voce", "Laura"), "language_code": cfg.get("lingua", "it"),
                                                       "stability": cfg.get("stabilita", 0.5), "timestamps": True}, attesa_max=600)
        mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        urllib.request.urlretrieve(r["audio"]["url"], mp3)
        wav = mp3[:-4] + ".wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
        s, sr = sf.read(wav); os.remove(mp3); os.remove(wav)
        car, ini, fin = [], [], []
        for blocco in r["timestamps"]:
            car += blocco["characters"]; ini += blocco["character_start_times_seconds"]; fin += blocco["character_end_times_seconds"]
        if "".join(car) != testo:
            sys.exit("i tempi di ElevenLabs non corrispondono al testo inviato: controllare a mano")
        # taglio a metà della pausa fra l'ultima lettera di una battuta e la prima della successiva
        tagli = [0.0]
        for (a0, a1), (b0, b1) in zip(pezzi, pezzi[1:]):
            fine_a = fin[max(i for i in range(a0, a1) if car[i].strip())]
            # la prima lettera vera della battuta dopo, saltando spazi e tag fra parentesi quadre
            i, dentro = b0, False
            while i < b1:
                if car[i] == "[": dentro = True
                elif car[i] == "]": dentro = False
                elif not dentro and car[i].strip(): break
                i += 1
            tagli.append((fine_a + ini[i]) / 2)
        tagli.append(len(s) / sr)
        out = []
        for k in range(len(battute)):
            pezzo = s[int(tagli[k] * sr): int(tagli[k + 1] * sr)]
            idx = np.where(np.abs(pezzo) > 0.01)[0]
            pezzo = pezzo[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else pezzo
            out.append(pezzo)
        return out
    insieme = [b for b in cfg["battute"] if not b.get("a_parte")]
    audio = dict(zip([id(b) for b in insieme], registra(insieme))) if insieme else {}
    for b in cfg["battute"]:
        if b.get("a_parte"): audio[id(b)] = registra([b])[0]
    res = []
    for i, b in enumerate(cfg["battute"]):
        f = os.path.join(cartella, f"vo_{i + 1:02d}_{b['scena']}.wav")
        sf.write(f, audio[id(b)], SR)
        res.append({"scena": b["scena"], "file": os.path.basename(f), "testo": b["testo"], "durata": round(len(audio[id(b)]) / SR, 3)})
        print(f"{b['scena']:12s} {len(audio[id(b)]) / SR:5.2f} s  {b['testo'][:70]}")
    json.dump({"motore": "eleven-v3-fal", "voce": cfg.get("voce", "Laura"), "battute": res}, open(os.path.join(cartella, "voiceover.json"), "w"), ensure_ascii=False, indent=1)
    print(f"totale parlato {sum(x['durata'] for x in res):.1f} s")


STILE_GEMINI = ("Parla in italiano naturale, con accento italiano neutro. Sei un'amica calda e rassicurante che racconta una "
                "cosa di tutti i giorni: ritmo sciolto, un sorriso nella voce, pause naturali, niente tono da pubblicità o da "
                "annunciatrice.")


API_GEMINI = "https://generativelanguage.googleapis.com/v1beta"
STILE_GEMINI_38 = "italiano naturale, calda e sicura, ritmo sciolto, sorriso nella voce, niente tono da spot"


def chiave_gemini():
    sys.path.insert(0, QUI)
    import chiavi
    return chiavi.gemini()


def post_gemini(percorso, corpo):
    import urllib.request, urllib.error
    rq = urllib.request.Request(API_GEMINI + percorso, data=json.dumps(corpo).encode(), method="POST",
                                headers={"x-goog-api-key": chiave_gemini(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(rq, timeout=600) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Gemini API {e.code}: {e.read().decode(errors='replace')[:800]}")


def gemini_38(testo, cfg, uscita):
    """Una richiesta a /interactions con gemini-3.8-flash-tts, WAV mono 24 kHz scritto in `uscita`."""
    import base64
    corpo = {"model": cfg.get("modello", "gemini-3.8-flash-tts"),
             "input": [{"type": "user_input", "content": [{"type": "text", "text": testo,
                        "annotations": [{"type": "speech_metadata", "style": cfg.get("stile", STILE_GEMINI_38)}]}]}],
             "response_format": {"type": "audio"},
             "generation_config": {"speech_config": [{"voice": cfg.get("voce", "Kore")}]}}
    r = post_gemini("/interactions", corpo)
    audio = [c for st in r.get("steps", []) if st.get("type") == "model_output"
             for c in st.get("content", []) if c.get("type") == "audio"]
    if not audio:
        sys.exit("nessun audio nella risposta di Gemini: " + json.dumps(r)[:800])
    open(uscita, "wb").write(base64.b64decode(audio[-1]["data"]))


def disegna(a):
    """Voce nuova da una descrizione (Voice design di Gemini 3.8): id permanente e anteprima WAV."""
    import base64
    corpo = {"store": True, "voice": {"model": "gemini-3.8-flash-tts", "type": "prompted", "display_name": a.nome,
                                      "gender": a.genere, "language_code": a.lingua, "prompted": {"input": a.descrizione}}}
    r = post_gemini("/voices", corpo)
    os.makedirs(a.out, exist_ok=True)
    nome_file = re.sub(r"[^a-z0-9]+", "_", a.nome.lower()).strip("_")
    if r.get("sample_audio", {}).get("data"):
        open(os.path.join(a.out, f"anteprima_{nome_file}.wav"), "wb").write(base64.b64decode(r["sample_audio"]["data"]))
    archivio = os.path.join(QUI, "_modelli", "voci", "gemini_voci.json")
    voci = json.load(open(archivio)) if os.path.exists(archivio) else {}
    voci[a.nome] = {"id": r["id"], "genere": a.genere, "lingua": a.lingua, "descrizione": a.descrizione}
    os.makedirs(os.path.dirname(archivio), exist_ok=True)
    json.dump(voci, open(archivio, "w"), ensure_ascii=False, indent=1)
    print(f"{a.nome}: {r['id']}")


def gemini(cfg, cartella):
    """Gemini 3.1 Flash TTS su fal: una registrazione per tutte le battute, tagliata a metà delle pause fra una battuta e
    l'altra sui tempi delle parole di Scribe (Gemini non restituisce tempi). Voce di default «Achernar»,
    con lo stile di STILE_GEMINI, scelta alla cieca fra nove voci."""
    import tempfile, urllib.request
    sys.path.insert(0, QUI)
    import genera_broll as g
    os.makedirs(cartella, exist_ok=True)
    battute = cfg["battute"]
    testi = [per_voce(b["testo"], cfg.get("pronuncia", {})) for b in battute]
    tmp = tempfile.mkdtemp()
    grezzo = os.path.join(tmp, "presa.wav")
    if cfg.get("motore") == "gemini-38":
        gemini_38("\n\n".join(testi), cfg, grezzo)
    else:
        corpo = {"prompt": "\n\n".join(testi), "voice": cfg.get("voce", "Achernar"), "language_code": cfg.get("lingua", "Italian (Italy)"),
                 "style_instructions": cfg.get("stile", STILE_GEMINI), "temperature": cfg.get("temperatura", 1), "output_format": "wav"}
        r = g.coda("fal-ai/gemini-3.1-flash-tts", corpo, attesa_max=600)
        urllib.request.urlretrieve(r["audio"]["url"], grezzo)
    wav = os.path.join(tmp, "presa48.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", grezzo, "-ar", str(SR), "-ac", "1", wav], check=True)
    s, sr = sf.read(wav)
    subprocess.run(["python3", os.path.join(QUI, "trascrivi.py"), wav, "--out", tmp], check=True, stdout=subprocess.DEVNULL)
    parole = [w for w in json.load(open(os.path.join(tmp, "presa48.json")))["words"] if w.get("type") == "word"]
    # allineo le parole del copione a quelle sentite, per sapere dove finisce ogni battuta
    copione, di_chi = [], []
    for k, t in enumerate(testi):
        for p in norm(t):
            copione.append(p); di_chi.append(k)
    sentite = [(norm(w["text"]) or [""])[0] for w in parole]
    corr = {}
    for blocco in difflib.SequenceMatcher(None, copione, sentite, autojunk=False).get_matching_blocks():
        for j in range(blocco.size):
            corr[blocco.a + j] = blocco.b + j
    tagli = [0.0]
    for k in range(len(battute) - 1):
        ultime = [i for i in range(len(copione)) if di_chi[i] == k and i in corr]
        prime = [i for i in range(len(copione)) if di_chi[i] == k + 1 and i in corr]
        if not ultime or not prime:
            sys.exit(f"battuta {k + 1}: parole non ritrovate nella presa, rigenerare o controllare a mano")
        fine, inizio = parole[corr[max(ultime)]]["end"], parole[corr[min(prime)]]["start"]
        tagli.append((fine + inizio) / 2)
    tagli.append(len(s) / sr)
    res = []
    for k, b in enumerate(battute):
        pezzo = s[int(tagli[k] * sr): int(tagli[k + 1] * sr)]
        idx = np.where(np.abs(pezzo) > 0.01)[0]
        pezzo = pezzo[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else pezzo
        f = os.path.join(cartella, f"vo_{k + 1:02d}_{b['scena']}.wav")
        sf.write(f, pezzo, SR)
        res.append({"scena": b["scena"], "file": os.path.basename(f), "testo": b["testo"], "durata": round(len(pezzo) / SR, 3)})
        print(f"{b['scena']:12s} {len(pezzo) / SR:5.2f} s  {b['testo'][:70]}")
    json.dump({"motore": cfg.get("motore", "gemini-tts-fal"), "voce": cfg.get("voce", "Achernar"), "battute": res},
              open(os.path.join(cartella, "voiceover.json"), "w"), ensure_ascii=False, indent=1)
    print(f"totale parlato {sum(x['durata'] for x in res):.1f} s")


def genera(a):
    cfg = json.load(open(a.testo))
    motore = cfg.get("motore", "chatterbox-fal")
    if motore in ("gemini-tts-fal", "gemini-38"):
        return gemini(cfg, a.out)
    if motore == "eleven-v3-fal":
        return eleven_v3(cfg, a.out)
    if motore == "kokoro":
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(MOD, "kokoro-v1.0.onnx"), os.path.join(MOD, "voices-v1.0.bin"))
        crea = lambda testo, b: k.create(testo, voice=cfg.get("voce", "if_sara"), speed=b.get("velocita", cfg.get("velocita", 1.0)), lang="it")
    else:
        crea = chatterbox(cfg)
    os.makedirs(a.out, exist_ok=True)
    out = []
    for i, b in enumerate(cfg["battute"]):
        s, sr = crea(per_voce(b["testo"], cfg.get("pronuncia", {})), b)
        # silenzio in testa e in coda tolto, poi 48 kHz
        idx = np.where(np.abs(s) > 0.01)[0]
        s = s[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else s
        f = os.path.join(a.out, f"vo_{i + 1:02d}_{b['scena']}.wav")
        tmp = f + ".tmp.wav"
        sf.write(tmp, s, sr)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ar", str(SR), "-ac", "1", f], check=True)
        os.remove(tmp)
        out.append({"scena": b["scena"], "file": os.path.basename(f), "testo": b["testo"], "durata": round(len(s) / sr, 3)})
        print(f"{b['scena']:12s} {len(s) / sr:5.2f} s  {b['testo'][:70]}")
    json.dump({"motore": motore, "battute": out}, open(os.path.join(a.out, "voiceover.json"), "w"), ensure_ascii=False, indent=1)
    print(f"totale parlato {sum(x['durata'] for x in out):.1f} s")


def norm(t):
    t = t.lower().replace("’", "'")
    return re.sub(r"[^\w\s]", " ", t).split()


def verifica(a):
    vo = json.load(open(os.path.join(a.cartella, "voiceover.json")))
    tr = os.path.join(a.cartella, "_trascrizioni")
    files = [os.path.join(a.cartella, b["file"]) for b in vo["battute"]]
    subprocess.run(["python3", os.path.join(QUI, "trascrivi.py"), *files, "--out", tr], check=True,
                   stdout=subprocess.DEVNULL)
    tot = []
    for b in vo["battute"]:
        j = json.load(open(os.path.join(tr, os.path.splitext(b["file"])[0] + ".json")))
        sentito = j.get("text", "")
        r = difflib.SequenceMatcher(None, norm(b["testo"]), norm(sentito)).ratio()
        tot.append(r)
        segno = "ok" if r >= 0.85 else "DA SENTIRE"
        print(f"{b['scena']:12s} {r:5.0%} {segno}\n   testo:   {b['testo']}\n   sentito: {sentito.strip()}")
    print(f"media {np.mean(tot):.0%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    x = sub.add_parser("genera"); x.add_argument("testo"); x.add_argument("--out", required=True)
    x = sub.add_parser("verifica"); x.add_argument("cartella")
    x = sub.add_parser("disegna"); x.add_argument("--nome", required=True); x.add_argument("--descrizione", required=True)
    x.add_argument("--genere", default="female"); x.add_argument("--lingua", default="it-IT"); x.add_argument("--out", required=True)
    a = ap.parse_args()
    {"genera": genera, "verifica": verifica, "disegna": disegna}[a.passo](a)
