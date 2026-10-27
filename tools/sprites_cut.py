import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
src, outdir = sys.argv[1], sys.argv[2]
name = src.split('/')[-1].split('.')[0]
a = np.array(Image.open(src).convert('RGB')).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
gr = g - np.maximum(r, b)
alpha = np.clip(1 - (gr - 60) / 120, 0, 1)
edge = ndimage.binary_dilation(alpha < .98, iterations=3)
g2 = np.where(edge & (gr > 10), np.maximum(r, b) + 10, g)
rgba = np.dstack([r, g2, b, alpha * 255]).clip(0, 255).astype(np.uint8)
mask = alpha > .5
mask = ndimage.binary_closing(mask, iterations=3)
lab, n = ndimage.label(mask)
objs = ndimage.find_objects(lab)
boxes = []
for i, sl in enumerate(objs):
    ys, xs = sl
    area = (lab[sl] == i + 1).sum()
    if area < 1500: continue
    boxes.append([xs.start, ys.start, xs.stop, ys.stop, int(area)])
# merge boxes that overlap horizontally inside the same row (detached rifle bits, raised fists)
H = a.shape[0]
def row(bx): return 0 if (bx[1] + bx[3]) / 2 < H / 2 else 1
boxes.sort(key=lambda b: (row(b), b[0]))
merged = []
for bx in boxes:
    if merged and row(merged[-1]) == row(bx) and bx[0] < merged[-1][2] - 10 and min(bx[2], merged[-1][2]) - max(bx[0], merged[-1][0]) > 0.35 * min(bx[2]-bx[0], merged[-1][2]-merged[-1][0]):
        m = merged[-1]; merged[-1] = [min(m[0], bx[0]), min(m[1], bx[1]), max(m[2], bx[2]), max(m[3], bx[3]), m[4] + bx[4]]
    else:
        merged.append(bx)
print(name, len(merged), 'sprites')
for i, bx in enumerate(merged):
    print(i, row(bx), bx[:4], bx[2]-bx[0], bx[3]-bx[1])
img = Image.fromarray(rgba, 'RGBA')
img.save(f'{outdir}/{name}_keyed.png')
json.dump([bx[:4] for bx in merged], open(f'{outdir}/{name}_boxes.json', 'w'))
