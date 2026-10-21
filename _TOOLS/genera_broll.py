# -*- coding: utf-8 -*-
"""B-roll: fotogrammi e ritagli dal girato vero del cliente, immagini e video generati su fal.

  python3 genera_broll.py fotogramma <video> --t 30.55 --out base.jpg [--verticale]
  python3 genera_broll.py ritaglia <video> --da 26 --a 33.2 --out clip_9x16.mp4 [--verticale]
  python3 genera_broll.py immagine --prompt "..." --out base.jpg [--formato 9:16]
  python3 genera_broll.py ingrandisci-immagine <immagine> --out base_hd.jpg [--modello "Low Resolution V2"] [--fattore 2]
  python3 genera_broll.py anima <immagine> --prompt "..." --out clip.mp4 [--durata 6s] [--formato 9:16] [--modello veo|kling]
  python3 genera_broll.py ingrandisci-video <video> --out clip_hd.mp4 [--modello Proteus] [--fattore 2]

Endpoint fal: fal-ai/nano-banana, fal-ai/topaz/upscale/image, fal-ai/veo3.1/image-to-video,
fal-ai/kling-video/v2.5-turbo/pro/image-to-video, fal-ai/topaz/upscale/video.
I file in ingresso si caricano sullo storage di fal: Topaz rifiuta i data URI ("URL too long").
La chiave fal si legge con chiavi.py (.env del kit o ~/.claude/settings.json).

Cosa regge (lezioni sui video di un'azienda manifatturiera):
- la base migliore è un fotogramma VERO del cliente (video del canale, foto Drive), animato con Veo: le scene
  generate da zero sono state bocciate come finte ("sembra un pavimento di legno lucido");
- prompt di movimento sobrio, per esempio "Camera locked off or a very slow push in, no cut, no zoom blur.
  Nothing new enters the frame. Quiet documentary footage, real time." Veo non accetta durate scritte senza "s";
- per le immagini: niente testo, loghi, volti; mani in guanti con il braccio intero che entra dal bordo;
- oggetti rigidi e fermi (rastrelliere, pile di pezzi) con la camera che si muove: Kling (--modello kling, 5 o 10 s).
  Su una rastrelliera di pezzi Veo li ha fatti staccare e oscillare tre volte su tre, Kling l'ha tenuta rigida al primo
  tentativo. Veo resta buono su acqua, nebbia, film che scorre;
- se il girato vero si muove già ed è nitido, niente AI: ritaglia e passa da ingrandisci-video (Topaz). Le mani vere
  vanno sempre prese così, con l'AI si deformano;
- dopo ogni clip: movimento_broll.py (sotto 1 sembra una foto) e controllo a occhio dei difetti che compaiono
  a metà clip (pezzi che volano, mani che si deformano): si tiene solo il tratto pulito.
"""
import argparse, json, mimetypes, os, shutil, subprocess, sys, time, urllib.request

FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")


def chiave():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chiavi
    return chiavi.fal()


def req(url, body=None):
    H = {"Authorization": f"Key {chiave()}", "Content-Type": "application/json"}
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=H)
    return json.load(urllib.request.urlopen(r, timeout=300))


def carica(p):
    tipo = mimetypes.guess_type(p)[0] or "application/octet-stream"
    r = req("https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3", {"content_type": tipo, "file_name": os.path.basename(p)})
    urllib.request.urlopen(urllib.request.Request(r["upload_url"], data=open(p, "rb").read(), method="PUT",
                                                  headers={"Content-Type": tipo}), timeout=900).read()
    return r["file_url"]


def coda(endpoint, corpo, attesa_max=1800):
    sub = req(f"https://queue.fal.run/{endpoint}", corpo)
    t0 = time.time()
    while time.time() - t0 < attesa_max:
        time.sleep(5)
        st = req(sub["status_url"])
        if st.get("status") == "COMPLETED":
            return req(sub["response_url"])
        if st.get("status") in ("FAILED", "ERROR"):
            sys.exit(f"{endpoint}: fallito {json.dumps(st)[:300]}")
    sys.exit(f"{endpoint}: nessuna risposta in {attesa_max} s")


def scarica(url, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    urllib.request.urlretrieve(url, out)
    print("salvato", out)


VERTICALE = "crop=trunc(ih*9/16/2)*2:ih,scale=1080:1920:flags=lanczos,setsar=1"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    x = sub.add_parser("fotogramma"); x.add_argument("video"); x.add_argument("--t", type=float, required=True)
    x.add_argument("--out", required=True); x.add_argument("--verticale", action="store_true")
    x = sub.add_parser("ritaglia"); x.add_argument("video"); x.add_argument("--da", type=float, required=True)
    x.add_argument("--a", type=float, required=True); x.add_argument("--out", required=True); x.add_argument("--verticale", action="store_true")
    x = sub.add_parser("immagine"); x.add_argument("--prompt", required=True); x.add_argument("--out", required=True)
    x.add_argument("--formato", default="9:16")
    x = sub.add_parser("ingrandisci-immagine"); x.add_argument("immagine"); x.add_argument("--out", required=True)
    x.add_argument("--modello", default="Low Resolution V2"); x.add_argument("--fattore", type=float, default=2)
    x = sub.add_parser("anima"); x.add_argument("immagine"); x.add_argument("--prompt", required=True); x.add_argument("--out", required=True)
    x.add_argument("--durata", default="6s", choices=["4s", "5s", "6s", "8s", "10s"]); x.add_argument("--formato", default="9:16")
    x.add_argument("--modello", default="veo", choices=["veo", "kling"])
    x = sub.add_parser("ingrandisci-video"); x.add_argument("video"); x.add_argument("--out", required=True)
    x.add_argument("--modello", default="Proteus"); x.add_argument("--fattore", type=float, default=2)
    a = ap.parse_args()

    if a.passo == "fotogramma":
        vf = ["-vf", VERTICALE] if a.verticale else []
        subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-ss", str(a.t), "-i", a.video, "-frames:v", "1", "-q:v", "2"] + vf + [a.out], check=True)
        print("salvato", a.out)
    elif a.passo == "ritaglia":
        vf = ["-vf", VERTICALE] if a.verticale else []
        subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-ss", str(a.da), "-i", a.video, "-t", f"{a.a - a.da:.3f}", "-an"] + vf +
                       ["-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", a.out], check=True)
        print("salvato", a.out)
    elif a.passo == "immagine":
        r = coda("fal-ai/nano-banana", {"prompt": a.prompt, "num_images": 1, "aspect_ratio": a.formato, "output_format": "jpeg"})
        scarica(r["images"][0]["url"], a.out)
    elif a.passo == "ingrandisci-immagine":
        r = coda("fal-ai/topaz/upscale/image", {"image_url": carica(a.immagine), "model": a.modello, "upscale_factor": a.fattore,
                                                "output_format": "jpeg", "face_enhancement": False})
        scarica(r["image"]["url"], a.out)
    elif a.passo == "anima" and a.modello == "kling":
        # Kling accetta solo 5 o 10 secondi e prende il formato dall'immagine
        r = coda("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", {"image_url": carica(a.immagine), "prompt": a.prompt,
                 "duration": "10" if a.durata in ("8s", "10s") else "5", "cfg_scale": 0.5,
                 "negative_prompt": "blur, distort, morphing, swinging parts, moving objects, text, watermark"})
        scarica(r["video"]["url"], a.out)
    elif a.passo == "anima":
        r = coda("fal-ai/veo3.1/image-to-video", {"image_url": carica(a.immagine), "prompt": a.prompt, "duration": a.durata,
                                                  "resolution": "1080p", "aspect_ratio": a.formato, "generate_audio": False})
        scarica(r["video"]["url"], a.out)
    elif a.passo == "ingrandisci-video":
        r = coda("fal-ai/topaz/upscale/video", {"video_url": carica(a.video), "model": a.modello, "upscale_factor": a.fattore, "H264_output": True})
        scarica(r["video"]["url"], a.out)
