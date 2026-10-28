"""Split the player sheet into recolourable layers: helmet, boots, gun (pixels copied from the keyed sheet)."""
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage
d = sys.argv[1]
im = np.array(Image.open(f'{d}/player_keyed.png')).astype(int)
boxes = json.load(open(f'{d}/player_boxes.json'))
r, g, b, a = [im[..., i] for i in range(4)]
v = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
opaque = a > 160
olive = opaque & (v >= 35) & (v <= 150) & (g >= b + 10) & (np.abs(r - g) <= 16)
brown = opaque & (r > g + 18) & (g > b + 4) & (v >= 55) & (v <= 200)
gray = opaque & ((v - mn) <= 14) & (v >= 36) & (v <= 160)
H = np.zeros(a.shape, bool); B = np.zeros(a.shape, bool); G = np.zeros(a.shape, bool)
NO_BOOTS = {2, 10, 15}
HEAD = {0:(90,20),1:(111,18),2:(160,18),3:(105,20),4:(60,20),5:(62,20),6:(70,20),7:(103,52),8:(85,18),9:(69,20),10:(146,22),11:(83,18),12:(96,20),13:(103,25),14:(120,45),15:(70,15)}
for i, (x0, y0, x1, y1) in enumerate(boxes):
    h = y1 - y0
    sl = (slice(y0, y1), slice(x0, x1))
    zone = np.zeros((h, x1 - x0), bool); zone[:int(h * (.5 if i in (2, 10, 15) else .42))] = True
    cx, cy = HEAD[i]
    yy, xx = np.mgrid[0:h, 0:x1 - x0]
    near = (xx - cx) ** 2 + (yy - cy) ** 2 < 46 ** 2
    hm = (olive[sl] | gray[sl]) & near & ~brown[sl]
    lab, n = ndimage.label(hm)
    best, bestk = None, 0
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(ys) < 40: continue
        dist = np.hypot(xs.mean() - cx, ys.mean() - cy)
        if best is None or dist < best: best, bestk = dist, k
    if bestk:
        hm = ndimage.binary_fill_holes(ndimage.binary_closing(lab == bestk, iterations=3)) & opaque[sl] & near
        H[sl] |= hm
    print('frame', i, 'helmet px', int(hm.sum()) if bestk else 0)
    if i not in NO_BOOTS:
        bz = np.zeros_like(zone); bz[int(h * .8):] = True
        B[sl] |= brown[sl] & bz
    if i == 3:
        gz = np.zeros_like(zone); gz[:int(h * .42), :int((x1 - x0) * .3)] = True
        G[sl] |= opaque[sl] & gz & ~H[sl] & ((v[sl] - mn[sl]) <= 22) & (v[sl] < 170)
for name, m in (('helm', H), ('boot', B), ('gun', G)):
    m = ndimage.binary_dilation(m, iterations=1) & opaque
    out = np.zeros_like(im); out[m] = im[m]
    Image.fromarray(out.astype(np.uint8), 'RGBA').save(f'{d}/player_{name}.png')
    print(name, int(m.sum()))
# visual check: paint the three layers in loud colours
chk = im.copy()
chk[H] = [255, 0, 255, 255]; chk[B] = [0, 160, 255, 255]; chk[G] = [255, 220, 0, 255]
bg = Image.new('RGBA', (im.shape[1], im.shape[0]), (196, 149, 97, 255)); bg.alpha_composite(Image.fromarray(chk.astype(np.uint8), 'RGBA'))
bg.convert('RGB').resize((im.shape[1] // 2, im.shape[0] // 2)).save(f'{d}/parts_check.jpg')
