"""Colore diverso su alcune parole dei sottotitoli già scritti in un progetto CapCut.

  python3 evidenzia_sottotitoli.py <progetto> --stile <stile.json> [--traccia "Sottotitoli"]

`sottotitoli_capcut.py scrivi` mette un colore solo su tutto il blocco: dentro CapCut il testo di un
segmento è un json (`content`) con una lista di `styles`, ognuno con il suo `range` di caratteri, quindi
più colori nello stesso blocco si ottengono spezzando quella lista.

Lo stile del cliente deve avere:
  "parole_in_giallo": ["AI", "3D", "<MARCHIO>", ...]   le parole da colorare, in maiuscolo
  "stile_giallo": {"fill": {...}}                  cosa cambia rispetto a "stile_testo"

Si scrive in tutte e sei le copie del progetto, con CapCut chiuso, dopo un backup fatto da chi chiama.
Rilanciarlo è sicuro: ricostruisce gli stili dal testo ogni volta.
"""
import argparse, copy, json, os, re, subprocess, sys

PROGETTI = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")


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


def tratti(testo, parole):
    """i tratti di `testo` da colorare, come coppie (inizio, fine) su indici di carattere"""
    fuori = []
    for p in parole:
        for m in re.finditer(rf"(?<![0-9A-ZÀ-Ù]){re.escape(p)}(?![0-9A-ZÀ-Ù])", testo):
            fuori.append((m.start(), m.end()))
    fuori.sort()
    unite = []
    for a, b in fuori:
        if unite and a <= unite[-1][1]:
            unite[-1] = (unite[-1][0], max(unite[-1][1], b))
        else:
            unite.append((a, b))
    return unite


def stili(testo, parole, base, acceso):
    """la lista di styles: tratti normali e tratti colorati, contigui e senza buchi"""
    out, pos = [], 0
    for a, b in tratti(testo, parole):
        if a > pos:
            s = copy.deepcopy(base); s["range"] = [pos, a]; out.append(s)
        s = copy.deepcopy(base)
        for k, v in acceso.items():
            s[k] = copy.deepcopy(v)
        s["range"] = [a, b]; out.append(s)
        pos = b
    if pos < len(testo):
        s = copy.deepcopy(base); s["range"] = [pos, len(testo)]; out.append(s)
    return out or [dict(copy.deepcopy(base), range=[0, len(testo)])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("progetto")
    ap.add_argument("--stile", required=True)
    ap.add_argument("--traccia", default="Sottotitoli")
    a = ap.parse_args()

    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        sys.exit("CapCut è aperto: va chiuso prima di scrivere")

    st = json.load(open(a.stile))
    parole = st.get("parole_in_giallo") or []
    acceso = st.get("stile_giallo")
    if not parole or not acceso:
        sys.exit("lo stile non ha 'parole_in_giallo' e 'stile_giallo'")
    base = st["stile_testo"]

    cart = cartella_progetto(a.progetto)
    tocchi = colorate = 0
    for f in copie(cart):
        d = json.load(open(f))
        tr = next((t for t in d["tracks"] if t["type"] == "text" and t.get("name") == a.traccia), None)
        if tr is None:
            continue
        ids = {s["material_id"] for s in tr["segments"]}
        for m in d["materials"].get("texts", []):
            if m["id"] not in ids:
                continue
            c = json.loads(m["content"])
            testo = c.get("text", "")
            c["styles"] = stili(testo, parole, base, acceso)
            m["content"] = json.dumps(c, ensure_ascii=False)
            tocchi += 1
            colorate += sum(1 for s in c["styles"] if s.get("fill") == acceso.get("fill"))
        json.dump(d, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{tocchi} blocchi riscritti su {len(copie(cart))} copie, {colorate} tratti colorati")


if __name__ == "__main__":
    main()
