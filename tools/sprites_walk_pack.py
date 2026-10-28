"""Pack the side-step walk sheet (4 rows × 6) with hip-centred anchors and recolour layers → walk.js"""
import json, base64, io, sys, numpy as np
from PIL import Image
d = sys.argv[1]
im = Image.open(f'{d}/player_keyed.png'); a = np.array(im)[..., 3]
gun = np.array(Image.open(f'{d}/player_gun.png'))[..., 3] > 20
boxes = json.load(open(f'{d}/player_boxes.json'))
frames = []
for (x0, y0, x1, y1) in boxes:
    h = y1 - y0
    m = (a[y0:y1, x0:x1] > 128) & ~gun[y0:y1, x0:x1]
    band = m[int(h * .56):int(h * .68), :]
    xs = np.nonzero(band)[1]
    ax = float(xs.mean()) if len(xs) else (x1 - x0) / 2
    frames.append([x0, y0, x1 - x0, h, round(ax, 1)])
def enc(img):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=88, method=6); return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), len(b.getvalue()) // 1024
src, kb = enc(im); print('walk sheet', kb, 'KB')
parts = {}
for p in ('helm', 'boot', 'gun'):
    parts[p], kb = enc(Image.open(f'{d}/player_{p}.png')); print(' part', p, kb, 'KB')
stand_h = np.mean([f[3] for f in frames[0:6]])
out = {'src': src, 'f': frames, 'ppm': round(stand_h / 1.78, 2), 'parts': parts}
open(f'{d}/walk.js', 'w').write('const WALKSHEET=' + json.dumps(out, separators=(',', ':')) + ';\n')
print('ppm', out['ppm'])
