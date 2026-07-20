#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scenedump.py - ROM 텍스트 영역을 '정확한 오프셋별 문자열'로 파싱하고 16×16 글리프로 렌더.
사용: python tools/scenedump.py 0xA3260 0xA3800 work/scene.png
각 줄 왼쪽에 오프셋(hex), 오른쪽에 그 문자열의 글리프. 일본어를 눈으로 읽어 번역에 사용.
확정 매핑(code_to_tilebase) 적용 — 고코드도 정확.
"""
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


def parse(start, end):
    i = start; out = []
    while i < end:
        v = struct.unpack_from("<H", ROM, i)[0]
        if 1 <= v <= 0x7f9 and v not in (0,):
            s = i; c = []
            while i < end:
                v = struct.unpack_from("<H", ROM, i)[0]
                if 1 <= v <= 0x7f9:
                    c.append(v); i += 2
                else:
                    break
            if c:
                out.append((s, c))
        else:
            i += 2
    return out


def main():
    start = int(sys.argv[1], 0); end = int(sys.argv[2], 0)
    out = sys.argv[3] if len(sys.argv) > 3 else "work/scene.png"
    lines = parse(start, end)
    cell = 17; H = len(lines) * (cell + 2) + 2; W = 80 + 34 * cell
    img = Image.new('L', (W, H), 10); d = ImageDraw.Draw(img); y = 2
    for s, codes in lines:
        d.text((2, y + 4), f"{s:x}", fill=180); x = 80
        for c in codes[:34]:
            g = glyph16(c)
            if g is not None:
                img.paste(Image.fromarray(g), (x, y))
            x += cell
        y += cell + 2
    img.save(out)
    print(f"{len(lines)} strings, saved {out}")
    for s, c in lines:
        print(f"0x{s:x} ({len(c)})")


if __name__ == '__main__':
    main()
