# /// script
# dependencies = ["playwright", "pillow", "requests"]
# ///
# -*- coding: utf-8 -*-
"""B-roll stock da Pexels: ricerca con provino, poi preparazione e controllo di un candidato.

  uv run stock.py cerca   <etichetta> "V:query solo verticali" "query" [--max 20] [--cartella <dir di lavoro>]
  uv run stock.py prepara <nome> --id <pexels id> [--da 0 --a 8] [--x 0.5 --y 0.5 --zoom 1] [--cartella <dir>]
  uv run stock.py prepara <nome> --file <video locale> ...

cerca apre Pexels con Chrome senza finestra (sul Mac non compare niente: mai usare Playwright MCP, apre
finestre), legge i risultati dalla pagina e scrive ricerche/<etichetta>.json e ricerche/<etichetta>.jpg, il provino con
numero, risoluzione del file migliore, durata e fps. Le query in inglese rendono meglio; "V:" filtra i verticali.
I file si scaricano direttamente da videos.pexels.com, senza chiave.

prepara scarica il file migliore in raw/, ritaglia a 9:16 (1080x1920, senza audio, fps della sorgente riportati a
24/25/30), scrive clip/<nome>_9x16.mp4 e clip/<nome>_strip.jpg (8 fotogrammi), stampa sorgente, ingrandimento e movimento.

Criteri che hanno retto sui video di un'azienda manifatturiera:
- sorgente verticale almeno 1080x1920 oppure orizzontale larga almeno 2560, ingrandimento al massimo 1.35;
- movimento sul tratto usato almeno 2 (1.2-2 solo sotto 1.5 s): misuralo con movimento_broll.py --da offset --durata;
- niente scritte leggibili, loghi, persone che guardano in camera, pose da spot (sorrisi, cappellino e badge), verniciatura
  a spruzzo sui video di cubicatura, saldature, scene da studio fotografico con fondale grigio;
- ogni clip controllata a piena risoluzione sui fotogrammi: il logo spesso entra a metà clip, si sceglie il tratto prima.
Licenza Pexels: uso commerciale libero, attribuzione non obbligatoria; si annota comunque id e autore nella libreria.
"""
import argparse, asyncio, glob, io, json, os, subprocess, sys, urllib.parse, urllib.request

FF = os.path.expanduser("~/.local/bin/ffmpeg"); FP = os.path.expanduser("~/.local/bin/ffprobe")
QUI = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def cammina(o, out):
    if isinstance(o, dict):
        a = o.get("attributes")
        if o.get("type") == "video" and isinstance(a, dict) and a.get("video"):
            out.append(a)
        for v in o.values():
            cammina(v, out)
    elif isinstance(o, list):
        for v in o:
            cammina(v, out)


async def pagine(queries):
    from playwright.async_api import async_playwright
    ris, visti = [], set()
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(user_agent=UA, viewport={"width": 1400, "height": 900}, locale="en-US")
        pg = await ctx.new_page()
        for q in queries:
            vert = q.startswith("V:"); qq = q[2:] if vert else q
            await pg.goto(f"https://www.pexels.com/search/videos/{urllib.parse.quote(qq)}/" + ("?orientation=portrait" if vert else ""),
                          wait_until="domcontentloaded", timeout=60000)
            await pg.wait_for_timeout(3500)
            nd = await pg.evaluate("() => { const e=document.getElementById('__NEXT_DATA__'); return e? e.textContent : null }")
            if not nd:
                print("nessun risultato leggibile per", q); continue
            out = []; cammina(json.loads(nd), out)
            for a in out:
                if a["id"] in visti:
                    continue
                visti.add(a["id"])
                files = sorted(a["video"]["video_files"], key=lambda f: f["width"] * f["height"])
                ris.append({"id": a["id"], "q": q, "slug": a.get("slug"), "desc": (a.get("description") or "")[:140],
                            "dur": a.get("duration"), "fps": a.get("fps"),
                            "autore": (a.get("user") or {}).get("username") or (a.get("user") or {}).get("first_name"),
                            "file": files[-1]["link"], "file_w": files[-1]["width"], "file_h": files[-1]["height"],
                            "thumb": a["video"]["thumbnail"]["medium"]})
        await b.close()
    return ris


def cerca(a):
    import requests
    from PIL import Image, ImageDraw, ImageFont
    ris = asyncio.run(pagine(a.query))[:a.max]
    os.makedirs(f"{a.cartella}/ricerche", exist_ok=True)
    json.dump(ris, open(f"{a.cartella}/ricerche/{a.etichetta}.json", "w"), indent=1, ensure_ascii=False)
    W, H, cols = 360, 240, 4
    sheet = Image.new("RGB", (W * cols, (H + 34) * ((len(ris) + cols - 1) // cols or 1)), "black"); dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    for i, r in enumerate(ris):
        try:
            im = Image.open(io.BytesIO(requests.get(r["thumb"], timeout=30).content)).convert("RGB"); im.thumbnail((W, H))
        except Exception:
            im = Image.new("RGB", (W, H), "gray")
        x, y = (i % cols) * W, (i // cols) * (H + 34)
        sheet.paste(im, (x + (W - im.width) // 2, y + (H - im.height) // 2))
        dr.text((x + 4, y + H + 2), f"{i} {r['file_w']}x{r['file_h']} {r['dur']}s {r['fps']}fps", fill="yellow", font=font)
        dr.text((x + 4, y + H + 17), (r["slug"] or "")[:44], fill="white", font=font)
    sheet.save(f"{a.cartella}/ricerche/{a.etichetta}.jpg", quality=82)
    for i, r in enumerate(ris):
        print(i, r["id"], f"{r['file_w']}x{r['file_h']}", f"{r['dur']}s", r["autore"], "|", r["desc"][:100])
    print("provino:", f"{a.cartella}/ricerche/{a.etichetta}.jpg")


def prepara(a):
    B = a.cartella
    os.makedirs(f"{B}/raw", exist_ok=True); os.makedirs(f"{B}/clip", exist_ok=True)
    info = {}
    if a.id:
        for f in glob.glob(f"{B}/ricerche/*.json"):
            for r in json.load(open(f)):
                if str(r["id"]) == str(a.id):
                    info = r
        if not info:
            sys.exit(f"id {a.id} non trovato nelle ricerche di {B}: lancia prima cerca")
        src = f"{B}/raw/{a.id}.mp4"
        if not os.path.exists(src):
            with urllib.request.urlopen(urllib.request.Request(info["file"], headers={"User-Agent": UA}), timeout=600) as r, open(src + ".part", "wb") as o:
                while True:
                    blocco = r.read(1 << 20)
                    if not blocco:
                        break
                    o.write(blocco)
            os.rename(src + ".part", src)
    elif a.file:
        src = a.file
    else:
        sys.exit("serve --id o --file")
    pr = json.loads(subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                                    "-of", "json", src], capture_output=True, text=True).stdout)
    W, H = pr["streams"][0]["width"], pr["streams"][0]["height"]
    num, den = map(int, pr["streams"][0]["r_frame_rate"].split("/")); fps = num / den; dur = float(pr["format"]["duration"])
    rot = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream_side_data=rotation", "-of", "csv=p=0", src],
                         capture_output=True, text=True).stdout.strip()
    if rot and abs(int(float(rot.split()[0]))) in (90, 270):
        W, H = H, W
    fin = min(a.a, dur)
    out_fps = 30 if round(fps) in (30, 60, 120) else 25 if round(fps) in (25, 50, 100) else 24 if round(fps) in (24, 48) else 30
    if W / H > 9 / 16:
        ch = H; cw = H * 9 / 16
    else:
        cw = W; ch = W * 16 / 9
    cw /= a.zoom; ch /= a.zoom
    cx = min(max(a.x * W - cw / 2, 0), W - cw); cy = min(max(a.y * H - ch / 2, 0), H - ch)
    out = f"{B}/clip/{a.nome}_9x16.mp4"
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-ss", f"{a.da}", "-i", src, "-t", f"{fin - a.da}", "-an", "-vf",
                    f"crop={int(cw)//2*2}:{int(ch)//2*2}:{int(cx)}:{int(cy)},scale=1080:1920:flags=lanczos,fps={out_fps},setsar=1,format=yuv420p",
                    "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-profile:v", "high", "-movflags", "+faststart", out], check=True)
    d = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    tiles = []
    for i in range(8):
        img = f"{B}/clip/_{a.nome}_t{i}.jpg"  # nome legato alla clip: più ricerche in parallelo non si mescolano
        subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-ss", f"{d * (i + 0.5) / 8:.3f}", "-i", out, "-frames:v", "1", "-vf", "scale=270:480", img], check=True)
        tiles.append(img)
    subprocess.run([FF, "-nostdin", "-v", "error", "-y"] + sum([["-i", t] for t in tiles], []) +
                   ["-filter_complex", "xstack=inputs=8:layout=" + "|".join(f"{(i % 4) * 270}_{(i // 4) * 480}" for i in range(8)), f"{B}/clip/{a.nome}_strip.jpg"], check=True)
    for t in tiles:
        os.remove(t)
    mov = subprocess.run(["python3", f"{QUI}/movimento_broll.py", out], capture_output=True, text=True).stdout.strip()
    print(json.dumps({"nome": a.nome, "id": a.id, "autore": info.get("autore"),
                      "pagina": f"https://www.pexels.com/video/{info.get('slug')}-{a.id}/" if a.id else None,
                      "sorgente": f"{W}x{H} {fps:.2f}fps {dur:.1f}s", "tratto": [a.da, round(fin, 2)], "durata_clip": round(d, 2),
                      "ingrandimento": round(1920 / ch, 2), "ritaglio": {"x": a.x, "y": a.y, "zoom": a.zoom}, "movimento": mov,
                      "striscia": f"{B}/clip/{a.nome}_strip.jpg"}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    x = sub.add_parser("cerca"); x.add_argument("etichetta"); x.add_argument("query", nargs="+")
    x.add_argument("--max", type=int, default=20); x.add_argument("--cartella", default=os.getcwd())
    x = sub.add_parser("prepara"); x.add_argument("nome"); x.add_argument("--id"); x.add_argument("--file")
    x.add_argument("--da", type=float, default=0); x.add_argument("--a", type=float, default=8)
    x.add_argument("--x", type=float, default=0.5); x.add_argument("--y", type=float, default=0.5)
    x.add_argument("--zoom", type=float, default=1.0); x.add_argument("--cartella", default=os.getcwd())
    a = ap.parse_args()
    cerca(a) if a.passo == "cerca" else prepara(a)
