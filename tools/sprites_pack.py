import json, base64, io, sys
import numpy as np
from PIL import Image
import os
d = os.environ.get('SPR_DIR', '/tmp/wallwar-sprites')
out = {}
for name in ['enemy', 'player']:
    im = Image.open(f'{d}/{name}_keyed.png')
    a = np.array(im)[..., 3]
    boxes = json.load(open(f'{d}/{name}_boxes.json'))
    frames = []
    for (x0, y0, x1, y1) in boxes:
        m = a[y0:y1, x0:x1] > 128
        h, w = m.shape
        if w / h > 1.2:
            xs = np.nonzero(m)[1]
        else:
            xs = np.nonzero(m[int(h * .8):, :])[1]
        ax = float(xs.mean()) if len(xs) else w / 2
        frames.append([x0, y0, x1 - x0, y1 - y0, round(ax, 1)])
    # trim: crop the sheet to used area, scale to 85% to keep the page small
    k = .85 if name == 'enemy' else 1.0
    sm = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    frames = [[round(v * k, 1) for v in f] for f in frames]
    buf = io.BytesIO(); sm.save(buf, 'WEBP', quality=88, method=6)
    data = base64.b64encode(buf.getvalue()).decode()
    stand_h = frames[0][3]
    out[name] = {'src': 'data:image/webp;base64,' + data, 'f': frames, 'ppm': round(stand_h / 1.78, 2)}
    print(name, 'webp KB', len(buf.getvalue()) // 1024, 'ppm', out[name]['ppm'])
open(f'{d}/sprites.js', 'w').write('const SPRITES=' + json.dumps(out, separators=(',', ':')) + ';\n')
