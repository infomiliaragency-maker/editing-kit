# /// script
# dependencies = ["pyobjc-framework-Quartz"]
# ///
"""Interfaccia di CapCut, con le regole dell'area: niente clic né tasti se CapCut non è in primo piano,
catture solo della finestra di CapCut.

  uv run ui.py finestra                 id, posizione e dimensione della finestra di CapCut
  uv run ui.py cattura out.png          cattura della sola finestra
  uv run ui.py clic X Y                 clic in coordinate della finestra (punti, origine in alto a sinistra)
  uv run ui.py doppio X Y
  uv run ui.py destro X Y                clic destro: nella home apre il menu del progetto (Rename, Duplicate)
  uv run ui.py tasti "testo"            digita testo
  uv run ui.py combo cmd,shift g        combinazione di tasti
  uv run ui.py giu N [shift]           freccia giu' N volte (con Maiusc estende la selezione)
  uv run ui.py invio | esc
"""
import subprocess, sys, time
import Quartz

def primo_piano():
    r = subprocess.run(["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
                       capture_output=True, text=True)
    return r.stdout.strip()

def finestre():
    lst = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
    out = []
    for w in lst:
        if w.get("kCGWindowOwnerName") == "CapCut" and w.get("kCGWindowLayer", 0) == 0:
            b = w["kCGWindowBounds"]
            out.append((int(w["kCGWindowNumber"]), b["X"], b["Y"], b["Width"], b["Height"], w.get("kCGWindowName", "")))
    return sorted(out, key=lambda x: -x[3] * x[4])

def serve_davanti():
    p = primo_piano()
    if p != "CapCut":
        sys.exit(f"FERMO: in primo piano c'è {p!r}, non CapCut. Niente clic.")

def mouse(x, y, doppio=False, flags=0):
    serve_davanti()
    f = finestre()
    if not f:
        sys.exit("nessuna finestra di CapCut")
    _, fx, fy, _, _, _ = f[0]
    pt = (fx + x, fy + y)
    ev = lambda t, n=1: Quartz.CGEventCreateMouseEvent(None, t, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev(Quartz.kCGEventMouseMoved)); time.sleep(0.15)
    for k in range(2 if doppio else 1):
        d = ev(Quartz.kCGEventLeftMouseDown); u = ev(Quartz.kCGEventLeftMouseUp)
        Quartz.CGEventSetIntegerValueField(d, Quartz.kCGMouseEventClickState, k + 1)
        Quartz.CGEventSetIntegerValueField(u, Quartz.kCGMouseEventClickState, k + 1)
        if flags:
            Quartz.CGEventSetFlags(d, flags); Quartz.CGEventSetFlags(u, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, d); time.sleep(0.05); Quartz.CGEventPost(Quartz.kCGHIDEventTap, u); time.sleep(0.08)

def destro(x, y):
    """Clic destro: nella home di CapCut apre il menu del progetto (Rename, Duplicate, Delete).
    Il clic sinistro sulla riga aprirebbe il progetto."""
    serve_davanti()
    f = finestre()
    if not f:
        sys.exit("nessuna finestra di CapCut")
    _, fx, fy, _, _, _ = f[0]
    pt = (fx + x, fy + y)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, pt, 0)); time.sleep(0.2)
    for t in (Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateMouseEvent(None, t, pt, Quartz.kCGMouseButtonRight)); time.sleep(0.06)


def osa(script):
    serve_davanti()
    subprocess.run(["osascript", "-e", f'tell application "System Events" to {script}'], check=True)

cmd = sys.argv[1]
if cmd == "finestra":
    print("primo piano:", primo_piano())
    for f in finestre():
        print(f)
elif cmd == "cattura":
    f = finestre()
    if not f:
        sys.exit("nessuna finestra di CapCut")
    subprocess.run(["screencapture", "-x", "-o", "-l", str(f[0][0]), sys.argv[2]], check=True)
    print("catturata finestra", f[0])
elif cmd == "clic":
    mouse(float(sys.argv[2]), float(sys.argv[3]))
elif cmd == "clicshift":
    mouse(float(sys.argv[2]), float(sys.argv[3]), flags=Quartz.kCGEventFlagMaskShift)
elif cmd == "scorri":   # scorri X Y righe (negativo = verso il basso)
    serve_davanti(); f = finestre(); pt = (f[0][1] + float(sys.argv[2]), f[0][2] + float(sys.argv[3]))
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, pt, 0)); time.sleep(0.2)
    for _ in range(abs(int(sys.argv[4]))):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 1, -1 if int(sys.argv[4]) < 0 else 1)); time.sleep(0.03)
elif cmd == "doppio":
    mouse(float(sys.argv[2]), float(sys.argv[3]), doppio=True)
elif cmd == "destro":
    destro(float(sys.argv[2]), float(sys.argv[3]))
elif cmd == "tasti":
    t = sys.argv[2].replace("\\", "\\\\").replace('"', '\\"')
    osa(f'keystroke "{t}"')
elif cmd == "combo":
    mods = ", ".join(f"{m} down" for m in sys.argv[2].split(","))
    osa(f'keystroke "{sys.argv[3]}" using {{{mods}}}')
elif cmd == "giu":       # giu N [shift]: freccia giu' N volte, con o senza Maiusc
    n = int(sys.argv[2]); mod = " using {shift down}" if len(sys.argv) > 3 and sys.argv[3] == "shift" else ""
    for _ in range(n):
        osa(f"key code 125{mod}"); time.sleep(0.05)
elif cmd == "invio":
    osa("key code 36")
elif cmd == "esc":
    osa("key code 53")
