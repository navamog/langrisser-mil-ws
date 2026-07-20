#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
textdump.py - 16비트 글자코드 텍스트를 16×16 글리프 이미지로 렌더(일본어 읽기용)
================================================================================
코드 C(1..0x500) -> 16×16 글리프(타일 base=(C-1)*4). 0xFFxx = 구분자/제어(마커).
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
import numpy as np
from PIL import Image, ImageDraw

ROM = wsfont.load_rom("랑그릿사 밀레니엄 WS - The Last Century.ws")
LV = [0, 85, 170, 255]


def glyph16(code):
    """code -> 16x16 uint8 array (배경 어둡게). 구분자는 None.
    확정 매핑 사용: code_to_tilebase (C<=0x3FF:(C-1)*4, C>=0x400:(C+3)*4)."""
    if code == 0 or code >= 0xff00 or code > 0x7f9:
        return None
    b = wsfont.code_to_tilebase(code)
    img = np.full((16, 16), 25, np.uint8)
    for dx, dy, tt in [(0, 0, b), (8, 0, b + 1), (0, 8, b + 2), (8, 8, b + 3)]:
        g = wsfont.decode_tile(ROM, tt * 16)
        for y in range(8):
            for x in range(8):
                img[dy + y, dx + x] = LV[g[y][x]]
    return img


def render_region(off, ncodes, per_row=24, scale=2, path="work/textdump.png"):
    codes = struct.unpack_from("<%dH" % ncodes, ROM, off)
    cw = 16
    rows = []
    cur = []
    for c in codes:
        if c >= 0xff00:            # 구분자 -> 줄바꿈
            rows.append(cur); cur = []
        else:
            cur.append(c)
        if len(cur) >= per_row:
            rows.append(cur); cur = []
    if cur: rows.append(cur)
    H = len(rows) * (cw + 2) + 2
    W = per_row * cw + 60
    img = Image.new('L', (W, H), 10)
    d = ImageDraw.Draw(img)
    y = 2
    o = off
    for r in rows:
        d.text((2, y + 4), f"{o:05x}", fill=180)
        x = 60
        for c in r:
            g = glyph16(c)
            if g is not None:
                img.paste(Image.fromarray(g), (x, y))
            x += cw
        o += (len(r) * 2)  # approx (구분자 무시)
        y += cw + 2
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)
    return path


if __name__ == '__main__':
    off = int(sys.argv[1], 0)
    n = int(sys.argv[2], 0) if len(sys.argv) > 2 else 256
    out = sys.argv[3] if len(sys.argv) > 3 else "work/textdump.png"
    print(render_region(off, n, path=out))
