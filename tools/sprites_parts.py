"""Colour-coded sheet → base sheet with default colours + gray shading layers for helmet (magenta), boots (cyan), rifle (yellow)."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
d = sys.argv[1]
im = np.array(Image.open(f'{d}/player_keyed.png')).astype(np.float32)
rgb = im[..., :3] / 255; a = im[..., 3]
mx = rgb.max(-1); mn = rgb.min(-1); S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0); V = mx
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.zeros_like(mx); dl = np.maximum(mx - mn, 1e-6)
hue = np.where(mx == r, ((g - b) / dl) % 6, np.where(mx == g, (b - r) / dl + 2, (r - g) / dl + 4)) * 60
op = a > 20
def band(h0, h1, smin=.35, vmin=.12): return op & (hue >= h0) & (hue <= h1) & (S >= smin) & (V >= vmin)
masks = {'helm': band(270, 340, .3), 'boot': band(160, 205, .3), 'gun': band(40, 76, .3)}
# grow by one pixel into the dark anti-aliased outline so edges recolour too
for k in masks: masks[k] = ndimage.binary_closing(masks[k], iterations=1) & op
DEF = {'helm': (90, 102, 80), 'boot': (138, 90, 48), 'gun': (60, 60, 62)}
base = im.copy()
for k, m in masks.items():
    shade = np.clip(V * .85 + (1 - S) * .5 * V, 0, 1)
    gray = (shade * 255)
    lay = np.zeros_like(im); lay[..., 0] = lay[..., 1] = lay[..., 2] = gray; lay[..., 3] = np.where(m, a, 0)
    Image.fromarray(lay.astype(np.uint8), 'RGBA').save(f'{d}/player_{k}.png')
    col = np.array(DEF[k], np.float32) / 255
    for c in range(3): base[..., c] = np.where(m, np.clip(col[c] * shade / .85 * 255, 0, 255), base[..., c])
    print(k, int(m.sum()))
Image.fromarray(base.astype(np.uint8), 'RGBA').save(f'{d}/player_keyed.png')
bg = Image.new('RGBA', (im.shape[1], im.shape[0]), (196, 149, 97, 255)); bg.alpha_composite(Image.fromarray(base.astype(np.uint8), 'RGBA'))
bg.convert('RGB').resize((im.shape[1] // 2, im.shape[0] // 2)).save(f'{d}/base_check.jpg')
