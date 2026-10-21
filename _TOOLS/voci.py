# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "librosa", "soundfile"]
# ///
"""Analisi dell'audio di una ripresa per separare le voci e decidere i tagli.

  uv run voci.py analizza <ripresa.MOV|wav> --out <cartella>
      scrive <nome>_livelli.json (RMS ogni 5 ms, dB) e <nome>_altezza.json (F0 ogni 10 ms, Hz, 0 = senza voce)
      e stampa il fondo della ripresa.

  uv run voci.py parlanti <cartella> <nome> <diarizzazione.json>
      per ogni parlante della diarizzazione (trascrivi.py --diarizza): picchi delle parole e altezza della voce.
      Il frontman di solito è il più forte; chi detta fuori campo sta 7-12 dB sotto.

Le soglie che servono dopo: silenzio vero = sotto il fondo + 7 dB (fondo -86 -> -79). L'altezza separa le voci
meglio del volume, ma non da sola: chi detta chiude le frasi con la voce che scende, il frontman la alza quando
enfatizza. I confini dubbi si guardano con spettrogrammi.py.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
import numpy as np, librosa, soundfile as sf

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")


def wav_mono(sorgente, sr):
    if sorgente.lower().endswith(".wav"):
        y, s = librosa.load(sorgente, sr=sr, mono=True)
        return y
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-i", sorgente, "-vn", "-ac", "1", "-ar", str(sr),
                    "-c:a", "pcm_s16le", tmp], check=True)
    y, _ = sf.read(tmp, dtype="float32")
    os.unlink(tmp)
    return y


def analizza(a):
    nome = os.path.splitext(os.path.basename(a.ripresa))[0]
    os.makedirs(a.out, exist_ok=True)
    # 48 kHz perché 5 ms siano un numero intero di campioni (240). A 44,1 kHz il blocco veniva 220 campioni,
    # cioè 4,99 ms dichiarati 5: tagli.py e spettrogrammi.py leggono 200 livelli al secondo e restavano
    # indietro dello 0,23% (0,12 s a 52 s, 0,19 s a 82 s). Scoperto su una ripresa unica lunga.
    SR = 48000
    y = wav_mono(a.ripresa, SR)
    H = SR // 200; n = len(y) // H
    blocchi = y[:n * H].reshape(n, H)
    rms = 20 * np.log10(np.maximum(np.sqrt((blocchi ** 2).mean(1)), 1e-7))
    json.dump({"passo_s": 0.005, "rms_db": [round(float(v), 1) for v in rms]},
              open(f"{a.out}/{nome}_livelli.json", "w"))
    y16 = librosa.resample(y, orig_sr=SR, target_sr=16000)
    f0, vf, _ = librosa.pyin(y16, fmin=60, fmax=400, sr=16000, frame_length=1024, hop_length=160)
    f0 = np.where(vf, f0, 0.0)
    json.dump({"passo_s": 0.01, "f0_hz": [round(float(v), 1) for v in f0]},
              open(f"{a.out}/{nome}_altezza.json", "w"))
    vivi = rms[rms > -139]
    istogramma = np.histogram(vivi[(vivi > -100) & (vivi < -60)], bins=np.arange(-100, -58, 2))
    fondo = float(istogramma[1][int(np.argmax(istogramma[0]))]) + 1
    print(f"{nome}: {len(y)/SR:.1f} s | fondo della ripresa circa {fondo:.0f} dB | silenzio vero sotto {fondo+7:.0f} dB"
          f" | frame a zero digitale {(np.abs(blocchi).max(1)==0).mean()*100:.1f}%")


def parlanti(a):
    liv = json.load(open(f"{a.cartella}/{a.nome}_livelli.json"))["rms_db"]
    alt = json.load(open(f"{a.cartella}/{a.nome}_altezza.json"))["f0_hz"]
    parole = [w for w in json.load(open(a.diarizzazione))["words"] if w.get("type") == "word"]
    per = {}
    for w in parole:
        i0, i1 = int(w["start"] * 200), int(w["end"] * 200) + 1
        if i1 <= i0 or i0 >= len(liv):
            continue
        p = per.setdefault(w.get("speaker_id", "?"), {"picchi": [], "f0": [], "n": 0})
        p["n"] += 1
        p["picchi"].append(max(liv[i0:min(i1, len(liv))]))
        p["f0"] += [v for v in alt[int(w["start"] * 100):int(w["end"] * 100) + 1] if v > 0]
    q = lambda z: [round(float(np.percentile(z, k))) for k in (10, 50, 90)] if z else None
    for s, p in sorted(per.items(), key=lambda kv: -np.median(kv[1]["picchi"])):
        print(f"{s}: {p['n']} parole | picco parole p10/p50/p90 {q(p['picchi'])} dB | altezza p10/p50/p90 {q(p['f0'])} Hz")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    x = sub.add_parser("analizza"); x.add_argument("ripresa"); x.add_argument("--out", required=True)
    x = sub.add_parser("parlanti"); x.add_argument("cartella"); x.add_argument("nome"); x.add_argument("diarizzazione")
    a = ap.parse_args()
    {"analizza": analizza, "parlanti": parlanti}[a.passo](a)
