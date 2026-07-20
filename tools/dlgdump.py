#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
import numpy as np
from PIL import Image, ImageDraw

ROM = bytes(wsfont.load_rom("랑그릿사 밀레니엄 WS - The Last Century.ws"))

def glyph16(code):
    if code == 0 or code >= 0xff00 or code > 0x7f9:
        return None
    b = wsfont.code_to_tilebase(code)
    img = np.full((16, 16), 25, np.uint8)
    pal = [0, 85, 170, 255]
    for k, (dy, dx) in enumerate([(0, 0), (0, 8), (8, 0), (8, 8)]):
        g = wsfont.decode_tile(ROM, (b + k) * 16)
        for y in range(8):
            for x in range(8):
                img[dy + y, dx + x] = pal[g[y][x]]
    return img

def parse(start, end, minlen):
    i = start; out = []
    while i < end:
        v = struct.unpack_from("<H", ROM, i)[0]
        if 1 <= v <= 0x7f9:
            s = i; c = []
            while i < end:
                v = struct.unpack_from("<H", ROM, i)[0]
                if 1 <= v <= 0x7f9:
                    c.append(v); i += 2
                else:
                    break
            if len(c) >= minlen:
                out.append((s, c))
        else:
            i += 2
    return out

def main():
    start = int(sys.argv[1], 0); end = int(sys.argv[2], 0)
    out = sys.argv[3] if len(sys.argv) > 3 else "work/dlg.png"
    minlen = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    lines = parse(start, end, minlen)
    cell = 18; H = len(lines) * (cell + 3) + 4; W = 90 + 34 * cell
    img = Image.new('L', (W, H), 10); d = ImageDraw.Draw(img); y = 3
    for s, codes in lines:
        d.text((2, y + 4), f"{s:x}:{len(codes)}", fill=200); x = 90
        for c in codes[:34]:
            g = glyph16(c)
            if g is not None:
                img.paste(Image.fromarray(g), (x, y))
            x += cell
        y += cell + 3
    img.save(out)
    print(f"{len(lines)} strings, saved {out}")

if __name__ == '__main__':
    main()
