"""python contact_sheet.py <dir> [--cols 2] [--w 640]  ->  <dir>/sheet.png of all CAM_*.png (labelled)."""
import argparse, glob, os
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--cols', type=int, default=2)
ap.add_argument('--w', type=int, default=640); ap.add_argument('--pattern', default='CAM_*.png')
a = ap.parse_args()
fs = sorted(glob.glob(os.path.join(a.dir, a.pattern)))
if not fs:
    raise SystemExit('no images')
W = a.w; H = int(W * 9 / 16); rows = (len(fs) + a.cols - 1) // a.cols
sheet = Image.new('RGB', (W * a.cols, H * rows))
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').resize((W, H))
    ImageDraw.Draw(im).text((6, 6), os.path.basename(f)[:-4], fill=(255, 255, 0))
    sheet.paste(im, ((i % a.cols) * W, (i // a.cols) * H))
sheet.save(os.path.join(a.dir, 'sheet.png')); print('sheet', len(fs), 'images')
