# /// script
# dependencies = ["opencv-python-headless"]
# ///
"""Dove stanno i volti in un video verticale, per non metterci sopra grafiche e sottotitoli.

  uv run volti.py <video> [--passo 0.25] [--out volti.json]

Scrive per ogni istante campionato i riquadri dei volti in pixel su 1080x1920 (x0, y0, x1, y1).
Rilevatore: YuNet di OpenCV (se il modello non c'è lo scarica), soglia 0.6.
"""
import argparse, json, os, sys, urllib.request
import cv2
ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--passo", type=float, default=0.25); ap.add_argument("--out")
a = ap.parse_args()
M = os.path.expanduser("~/.cache/yunet/face_detection_yunet_2023mar.onnx")
if not os.path.exists(M):
    os.makedirs(os.path.dirname(M), exist_ok=True)
    urllib.request.urlretrieve("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx", M)
c = cv2.VideoCapture(a.video); fps = c.get(cv2.CAP_PROP_FPS); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT))
det = cv2.FaceDetectorYN.create(M, "", (540, 960), 0.6, 0.3, 50)
out, t = [], 0.0
while t < n / fps:
    c.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = c.read()
    if not ok: break
    f = cv2.resize(f, (540, 960)); _, r = det.detect(f)
    out.append({"t": round(t, 2), "volti": [[int(x * 2), int(y * 2), int((x + w) * 2), int((y + h) * 2)] for x, y, w, h, *_ in (r if r is not None else [])]})
    t += a.passo
json.dump(out, open(a.out, "w")) if a.out else None
print(len(out), "istanti,", sum(1 for o in out if o["volti"]), "con volti")
