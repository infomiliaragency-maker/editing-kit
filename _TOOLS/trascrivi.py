# -*- coding: utf-8 -*-
"""Trascrizione parola per parola con ElevenLabs Scribe v2 su fal, anche con separazione dei parlanti.

  python3 trascrivi.py <file audio o video> [altri file] --out <cartella> [--diarizza] [--parole-chiave "a,b,c"]

Scrive <cartella>/<nome>.json con la risposta completa (words: text, start, end, type, speaker_id).
Se il json esiste già non ritrascrive. I file partono in parallelo.
Il file viene convertito in mp3 mono e caricato sullo storage di fal: i data URI su file lunghi falliscono.
La chiave fal si legge con chiavi.py (.env del kit o ~/.claude/settings.json), non si chiede mai.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, threading, time, urllib.request

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chiavi  # noqa: E402
KEY = chiavi.fal()
H = {"Authorization": f"Key {KEY}", "Content-Type": "application/json"}


def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=H)
    return json.load(urllib.request.urlopen(r, timeout=300))


def carica(percorso):
    r = req("https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3",
            {"content_type": "audio/mpeg", "file_name": os.path.basename(percorso)})
    urllib.request.urlopen(urllib.request.Request(r["upload_url"], data=open(percorso, "rb").read(), method="PUT",
                                                  headers={"Content-Type": "audio/mpeg"}), timeout=600).read()
    return r["file_url"]


def uno(sorgente, a, esiti):
    nome = os.path.splitext(os.path.basename(sorgente))[0]
    out = os.path.join(a.out, f"{nome}.json")
    if os.path.exists(out):
        esiti[nome] = "già fatto"; return
    mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-i", sorgente, "-vn", "-ac", "1", "-ar", "44100",
                    "-c:a", "libmp3lame", "-b:a", "128k", mp3], check=True)
    corpo = {"audio_url": carica(mp3), "language_code": a.lingua, "diarize": a.diarizza, "tag_audio_events": a.diarizza}
    if a.parole_chiave:
        corpo["keyterms"] = [k.strip() for k in a.parole_chiave.split(",") if k.strip()]
    sub = req("https://queue.fal.run/fal-ai/elevenlabs/speech-to-text/scribe-v2", corpo)
    for _ in range(450):
        time.sleep(4)
        st = req(sub["status_url"])
        if st.get("status") == "COMPLETED":
            json.dump(req(sub["response_url"]), open(out, "w"), ensure_ascii=False)
            esiti[nome] = "ok"; break
        if st.get("status") in ("FAILED", "ERROR"):
            esiti[nome] = f"fallito: {st}"; break
    else:
        esiti[nome] = "timeout"
    os.unlink(mp3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="+"); ap.add_argument("--out", required=True)
    ap.add_argument("--diarizza", action="store_true"); ap.add_argument("--parole-chiave", default="")
    ap.add_argument("--lingua", default="ita")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    esiti = {}
    th = [threading.Thread(target=uno, args=(f, a, esiti)) for f in a.file]
    [t.start() for t in th]; [t.join() for t in th]
    for n, e in esiti.items():
        print(n, e)
    for n in esiti:
        p = os.path.join(a.out, f"{n}.json")
        if os.path.exists(p):
            w = [x for x in json.load(open(p))["words"] if x["type"] == "word"]
            parl = sorted({x.get("speaker_id") for x in w if x.get("speaker_id")})
            print(f"  {n}: {len(w)} parole, parlanti {parl or '-'}")
    sys.exit(0 if all(e in ("ok", "già fatto") for e in esiti.values()) else 1)
