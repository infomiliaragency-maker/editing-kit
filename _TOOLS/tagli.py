# -*- coding: utf-8 -*-
"""Dai confini della voce del frontman ai tagli per CapCut, e controllo dei tagli.

  python3 tagli.py calcola confini.json --analisi <cartella di voci.py> --out tagli.json [--velocita 1.03]
  python3 tagli.py verifica tagli.json --analisi <cartella>

confini.json è una lista, una voce per frase, nell'ordine del montaggio:
  {"ripresa": "IMG_8598", "voce_da": 24.63, "voce_a": 28.46, "testo": "...", "fine_fissa": false}
voce_da è il primo istante della voce del frontman (consonante compresa), voce_a la fine della sua coda,
letti sugli spettrogrammi (spettrogrammi.py). fine_fissa=true tiene voce_a com'è, senza rifinitura.

Regole:
- rifinitura: l'inizio si allarga all'indietro solo lungo l'attacco che sale verso la voce (max 40 ms);
  la fine scende sulla coda fino al silenzio entro 100 ms, e si ferma se il livello risale di 6 dB o se
  compare un'altezza da chi detta (sopra 185 Hz, a qualunque livello). Se subito dopo la fine compare
  un'altezza oltre 225 Hz mentre il frontman chiudeva più basso, la fine arretra fino a 25 ms prima.
- margine: al massimo 0.08 s prima e 0.05 s dopo, solo attraverso silenzio vero (sotto -79 dB, mediana su
  15 ms, nessun frame oltre -76) e senza altezza di voce, fermandosi 25 ms prima di qualunque suono.
- durata: a 30 fps e velocità V ogni taglio dura un numero intero di fotogrammi. Il fotogramma in più si
  prende dal silenzio; se non c'è, si toglie prima dal margine e poi dalla coda.
"""
import argparse, json, os, statistics, sys


def carica(analisi, ripresa, cache={}):
    if ripresa not in cache:
        cache[ripresa] = (json.load(open(f"{analisi}/{ripresa}_livelli.json"))["rms_db"],
                          json.load(open(f"{analisi}/{ripresa}_altezza.json"))["f0_hz"])
    return cache[ripresa]


def calcola(a):
    C = json.load(open(a.confini))
    PASSO = a.velocita / a.fps
    SIL = a.silenzio

    def muto(r, F0, i, confine):
        if not (1 <= i < len(r) - 1):
            return False
        if r[i] > SIL + 3 or sorted((r[i - 1], r[i], r[i + 1]))[1] > SIL:
            return False
        k = i // 2
        v = F0[k] if k < len(F0) else 0
        if v <= 0:
            return True
        if v > 185:
            return False
        return abs(i - confine) <= 8

    out = []
    for c in C:
        r, F0 = carica(a.analisi, c["ripresa"])
        N = len(r)
        # ---- rifinitura della fine
        e0 = int(round(c["voce_a"] * 200)); e = None; stop = min(N - 2, e0 + 20); mn = 1e9
        if not c.get("fine_fissa"):
            for z in range(e0 - 3, min(N - 2, e0 + 20)):
                if z >= e0 and F0[z // 2] > 185:
                    stop = z - 5; break
                if r[z] <= SIL + 3 and sorted((r[z - 1], r[z], r[z + 1]))[1] <= SIL:
                    e = z; break
                if z >= e0 and r[z] > mn + 6:
                    stop = z; break
                mn = min(mn, r[z])
            if e is None:
                fin = range(max(1, e0 - 3), max(e0 - 2, min(stop, e0 + 5)))
                m = min(r[z] for z in fin); e = min(z for z in fin if r[z] <= m + 3)
            voce_a = round(e / 200, 3)
        else:
            voce_a = c["voce_a"]
        # ---- rifinitura dell'inizio
        i0 = int(round(c["voce_da"] * 200)); i = i0
        while i > 0 and SIL < r[i - 1] < r[i] - 0.5 and i0 - i < 8 and F0[(i - 1) // 2] <= 185:
            i -= 1
        voce_da = round(i / 200, 3)
        # ---- altezza da chi detta subito dopo la fine
        k = int(round(voce_a * 100))
        suo = [v for v in F0[k - 6:k - 1] if v > 0]
        alto = next((z for z in range(k - 2, min(len(F0), k + 6)) if F0[z] > 225), None)
        if alto is not None and (not suo or max(suo) <= 200):
            voce_a = round(max(alto / 100 - 0.025, voce_a - 0.03, voce_da + 0.2), 3)
        # ---- margini
        i = int(round(voce_da * 200)); j = i
        while j > 0 and muto(r, F0, j - 1, i) and (i - j) * 0.005 < a.testa + a.guardia:
            j -= 1
        libero_prima = (i - j) * 0.005 - (a.guardia if (j > 0 and not muto(r, F0, j - 1, i)) else 0)
        m_testa = max(0.0, min(a.testa, libero_prima))
        e = int(round(voce_a * 200)); j = e
        while muto(r, F0, j, e) and (j - e) * 0.005 < a.coda + a.guardia:
            j += 1
        libero_dopo = (j - e) * 0.005 - (a.guardia if not muto(r, F0, j, e) else 0)
        m_coda = max(0.0, min(a.coda, libero_dopo))
        da_i, a_i = voce_da - m_testa, voce_a + m_coda
        extra_prima, extra_dopo = max(0.0, libero_prima - m_testa), max(0.0, libero_dopo - m_coda)
        L = a_i - da_i; k_giu = int(L / PASSO + 1e-9); su = (k_giu + 1) * PASSO - L
        if su <= extra_dopo + extra_prima + 1e-9:
            e2 = min(su, extra_dopo); da, fine = da_i - (su - e2), a_i + e2
        else:
            manca = L - k_giu * PASSO
            t1 = min(manca, m_testa); manca -= t1
            t2 = min(manca, m_coda); manca -= t2
            da, fine = da_i + t1, a_i - t2 - manca
        out.append({"ripresa": c["ripresa"], "da": round(da, 6), "a": round(fine, 6), "testo": c.get("testo", ""),
                    "voce_da": voce_da, "voce_a": voce_a,
                    "margine_testa": round(voce_da - da, 3), "margine_coda": round(fine - voce_a, 3)})
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    mt = [x["margine_testa"] for x in out]; mc = [x["margine_coda"] for x in out]
    print(f"{len(out)} tagli, {sum(x['a'] - x['da'] for x in out) / a.velocita:.2f} s in timeline")
    print(f"margine prima: mediana {statistics.median(mt)}, a zero {sum(m <= 0.001 for m in mt)}")
    print(f"margine dopo: mediana {statistics.median(mc)}, a zero {sum(m <= 0.001 for m in mc)}, "
          f"code accorciate nella voce {sum(m < -0.001 for m in mc)} (max {-min(mc + [0]) * 1000:.0f} ms)")


def verifica(a):
    T = json.load(open(a.tagli)); PASSO = a.velocita / a.fps; problemi = []
    voce = {}
    for x in T:
        voce.setdefault(x["ripresa"], []).append((int(round(x["voce_da"] * 200)), int(round(x["voce_a"] * 200))))
    suono = 0; alto = 0
    for n, x in enumerate(T):
        r, F0 = carica(a.analisi, x["ripresa"])
        for z in range(int(round(x["da"] * 200)), int(round(x["a"] * 200))):
            if any(p <= z < q for p, q in voce[x["ripresa"]]):
                continue
            if r[z] > a.silenzio + 3:
                suono += 5; problemi.append(f"{n} {x['testo'][:30]}: suono a {z/200:.3f} ({r[z]:.0f} dB)")
            if F0[z // 2] > 185:
                alto += 5; problemi.append(f"{n} {x['testo'][:30]}: altezza {F0[z//2]:.0f} Hz a {z/200:.3f} fuori dalla voce")
        k = int(x["a"] * 100)
        dopo = next((z for z in range(k, min(len(F0), k + 2)) if F0[z] > 225), None)
        if dopo is not None:
            problemi.append(f"{n} {x['testo'][:30]}: altezza oltre 225 Hz entro 20 ms dopo la fine ({dopo/100:.2f})")
        q = (x["a"] - x["da"]) / PASSO
        if abs(q - round(q)) > 1e-3:
            problemi.append(f"{n} {x['testo'][:30]}: durata non intera in fotogrammi ({q:.3f})")
    for i, x in enumerate(T):
        for j, y in enumerate(T):
            if i < j and x["ripresa"] == y["ripresa"] and x["a"] > y["da"] and y["a"] > x["da"]:
                problemi.append(f"tagli {i} e {j} si sovrappongono nella stessa ripresa")
    print(f"suono fuori dalla voce dentro i tagli: {suono} ms | altezza da chi detta fuori dalla voce: {alto} ms")
    print("\n".join(problemi) if problemi else "nessun problema")
    sys.exit(1 if alto or any("sovrappongono" in p or "non intera" in p for p in problemi) else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="passo", required=True)
    for nome in ("calcola", "verifica"):
        x = sub.add_parser(nome)
        x.add_argument("confini" if nome == "calcola" else "tagli")
        x.add_argument("--analisi", required=True); x.add_argument("--velocita", type=float, default=1.03)
        x.add_argument("--fps", type=float, default=30); x.add_argument("--silenzio", type=float, default=-79)
        if nome == "calcola":
            x.add_argument("--out", required=True); x.add_argument("--testa", type=float, default=0.08)
            x.add_argument("--coda", type=float, default=0.05); x.add_argument("--guardia", type=float, default=0.025)
    a = ap.parse_args()
    {"calcola": calcola, "verifica": verifica}[a.passo](a)
