# /// script
# dependencies = ["pyobjc-framework-Quartz"]
# ///
"""Collega i media mancanti di un progetto CapCut, uno per volta, aspettando le finestre.

    uv run link_media.py "<cartella con i file>"

CapCut apre il dialogo "Link media" quando un progetto non trova i suoi media. Chiede
un file alla volta: qui gli si passano a turno tutti quelli della cartella, aspettando
che ogni finestra compaia davvero prima del passo dopo.
"""
import subprocess, sys, time, pathlib
import Quartz

def finestre():
    lst = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID)
    return {w.get("kCGWindowName", ""): w for w in lst if w.get("kCGWindowOwnerName") == "CapCut"}

def aspetta(nome, secondi=12):
    for _ in range(int(secondi * 4)):
        f = finestre()
        if nome in f:
            return f[nome]
        time.sleep(0.25)
    return None

def clic(x, y):
    for tipo in (Quartz.kCGEventMouseMoved, Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,
                           Quartz.CGEventCreateMouseEvent(None, tipo, (x, y), Quartz.kCGMouseButtonLeft))
        time.sleep(0.12)

def osa(s):
    subprocess.run(["osascript", "-e", s], capture_output=True)

def davanti():
    osa('tell application "CapCut" to activate'); time.sleep(0.8)

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
cartella = pathlib.Path(sys.argv[1])
files = sorted([p for p in cartella.iterdir() if p.suffix.upper() in (".MOV", ".MP4")])
print(f"{len(files)} file da passare a CapCut")

for i, f in enumerate(files, 1):
    w = finestre().get("Link media")
    if w is None:
        print(f"  dialogo sparito dopo {i-1} file: probabilmente ha finito")
        break
    b = w["kCGWindowBounds"]
    davanti()
    # il pulsante "Link media" sta in basso a destra del dialogo
    clic(b["X"] + b["Width"] - 63, b["Y"] + b["Height"] - 31)
    if aspetta("Open", 12) is None:
        print(f"  {f.name}: la finestra Open non si e' aperta"); continue
    time.sleep(0.6)
    osa('tell application "System Events" to keystroke "g" using {command down, shift down}')
    time.sleep(1.2)
    osa(f'tell application "System Events" to keystroke "{f}"')
    time.sleep(1.2)
    osa('tell application "System Events" to key code 36')   # conferma il percorso
    time.sleep(1.2)
    osa('tell application "System Events" to key code 36')   # Open
    for _ in range(40):
        if "Open" not in finestre(): break
        time.sleep(0.25)
    time.sleep(1.0)
    print(f"  {i}/{len(files)} passato {f.name}")
print("fine")
