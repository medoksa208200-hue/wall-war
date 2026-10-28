"""Pack the crawl sheet (2 rows × 6: back, front) → crawl.js; per-row scale matched to the prone poses of the main sheet."""
import json, base64, io, sys, numpy as np
from PIL import Image
d = sys.argv[1]
im = Image.open(f'{d}/player_keyed.png'); a = np.array(im)[..., 3]
gun = np.array(Image.open(f'{d}/player_gun.png'))[..., 3] > 20
boxes = json.load(open(f'{d}/player_boxes.json'))
AREA = {0: 1.27, 1: 1.468}            # m² of the main sheet prone back / front frames
row0 = boxes[0]; row1 = boxes[6]
ppm = {0: (row0[2]-row0[0])*(row0[3]-row0[1]), 1: (row1[2]-row1[0])*(row1[3]-row1[1])}
ppm = {r: round((ppm[r] / AREA[r]) ** .5, 2) for r in ppm}
frames = []
for i, (x0, y0, x1, y1) in enumerate(boxes):
    m = (a[y0:y1, x0:x1] > 128) & ~gun[y0:y1, x0:x1]
    xs = np.nonzero(m)[1]
    frames.append([x0, y0, x1 - x0, y1 - y0, round(float(xs.mean()), 1), ppm[0 if i < 6 else 1]])
def enc(img):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=88, method=6); return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), len(b.getvalue()) // 1024
src, kb = enc(im); print('crawl sheet', kb, 'KB', 'ppm', ppm)
parts = {}
for p in ('helm', 'boot', 'gun'):
    parts[p], kb = enc(Image.open(f'{d}/player_{p}.png')); print(' part', p, kb, 'KB')
open(f'{d}/crawl.js', 'w').write('const CRAWLSHEET=' + json.dumps({'src': src, 'f': frames, 'parts': parts}, separators=(',', ':')) + ';\n')
