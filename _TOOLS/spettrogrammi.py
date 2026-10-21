# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "librosa", "soundfile", "matplotlib"]
# ///
"""Pagine di spettrogrammi per decidere a vista i confini delle frasi.

  uv run spettrogrammi.py --ripresa IMG_8598.MOV --analisi <cartella di voci.py> --diar IMG_8598.json \\
      --frontman speaker_1 --punti "24.63:inizio frase 1,30.785:fine frase 2" --out <cartella>/pagina

Per ogni punto un pannello di 1.8 s (0.8 s con --stretto): spettrogramma fino a 2 kHz, parole diarizzate
(blu il frontman, rosso gli altri), altezza della voce (punti blu sotto 185 Hz, bianchi fra 185 e 225, rossi sopra),
livello in verde con la soglia del silenzio tratteggiata, linea gialla sul punto. Griglia ogni 100 ms (20 ms stretto).
Le pagine si leggono come immagini: il confine giusto è dove finisce l'energia di una voce e parte l'altra.
"""
import argparse, json, os, shutil, subprocess, tempfile
import numpy as np, librosa, soundfile as sf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--ripresa", required=True); ap.add_argument("--analisi", required=True)
ap.add_argument("--diar", required=True); ap.add_argument("--frontman", required=True)
ap.add_argument("--punti", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--silenzio", type=float, default=-79); ap.add_argument("--per-pagina", type=int, default=6)
ap.add_argument("--stretto", action="store_true")
a = ap.parse_args()

nome = os.path.splitext(os.path.basename(a.ripresa))[0]
liv = np.array(json.load(open(f"{a.analisi}/{nome}_livelli.json"))["rms_db"])
f0 = np.array(json.load(open(f"{a.analisi}/{nome}_altezza.json"))["f0_hz"])
parole = [w for w in json.load(open(a.diar))["words"] if w.get("type") == "word"]
tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-i", a.ripresa, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", tmp], check=True)
y, _ = sf.read(tmp, dtype="float32"); os.unlink(tmp)
punti = []
for p in a.punti.split(","):
    t, _, etichetta = p.partition(":")
    punti.append((float(t), etichetta))
mezza, passo, fmax = (0.4, 0.02, 3125) if a.stretto else (0.9, 0.1, 2000)
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
for pg in range(0, len(punti), a.per_pagina):
    blocco = punti[pg:pg + a.per_pagina]
    fig, axs = plt.subplots(len(blocco), 1, figsize=(16, 2.9 * len(blocco)))
    axs = np.atleast_1d(axs)
    for ax, (t, etichetta) in zip(axs, blocco):
        x0, x1 = max(0.0, t - mezza), t + mezza
        seg = y[int(x0 * 16000):int(x1 * 16000)]
        nbin = int(fmax / (16000 / 1024))
        D = librosa.amplitude_to_db(np.abs(librosa.stft(seg, n_fft=1024, hop_length=64)), ref=np.max)
        ax.imshow(D[:nbin], origin="lower", aspect="auto", extent=[x0, x1, 0, fmax], cmap="magma", vmin=-80, vmax=0)
        ff = f0[int(x0 * 100):int(x1 * 100)]; tt = np.arange(len(ff)) / 100 + x0
        k = fmax / 2000
        for lo, hi, col in ((1, 185, "deepskyblue"), (185, 225, "white"), (225, 999, "red")):
            m = (ff >= lo) & (ff < hi); ax.plot(tt[m], ff[m] * k, ".", color=col, ms=4)
        rr = liv[int(x0 * 200):int(x1 * 200)]
        scala = fmax / 80 * 0.6
        ax.plot(np.arange(len(rr)) / 200 + x0, (np.clip(rr, -90, -10) + 90) * scala, color="lime", lw=1)
        ax.axhline((a.silenzio + 90) * scala, color="lime", lw=0.5, ls=":")
        ax.axvline(t, color="yellow", lw=1.5, ls="--")
        for w in parole:
            if w["end"] > x0 and w["start"] < x1:
                col = "deepskyblue" if w.get("speaker_id") == a.frontman else "red"
                ax.plot([w["start"], w["end"]], [fmax * 0.965] * 2, color=col, lw=4)
                ax.text(max(w["start"], x0), fmax * 0.89, w["text"], color=col, fontsize=9)
        ax.set_xticks(np.arange(np.ceil(x0 / passo) * passo, x1, passo)); ax.tick_params(labelsize=7)
        ax.grid(axis="x", color="gray", lw=0.3); ax.set_xlim(x0, x1); ax.set_ylim(0, fmax)
        ax.set_title(f"{nome} {t:.3f} s  {etichetta}", fontsize=10)
    plt.tight_layout(); plt.savefig(f"{a.out}_{pg // a.per_pagina:02d}.png", dpi=60); plt.close()
print(f"{(len(punti) + a.per_pagina - 1) // a.per_pagina} pagine in {a.out}_*.png")
