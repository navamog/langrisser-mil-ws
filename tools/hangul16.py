#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hangul16.py - 16x16 조합형 한글 글리프 생성기 (WonderSwan 4타일=2x2 8x8)
=====================================================================

이 게임의 텍스트 폰트는 16x16(2x2 타일, row-major TL,TR,BL,BR)이다.
16x16은 8x8보다 훨씬 가독성이 좋다 — 초·중·종성을 여유있게 배치한다.

glyph16(ch) -> 16x16 색인(0..3) 2D 리스트. 배경=1, 잉크=3(원본 폰트와 동일).
to_tiles(grid16) -> [TL,TR,BL,BR] 각 8x8 색인 2D 리스트.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from hangul8x8 import CHO, JUNG, JONG, CONS, JONG3, V_VERT, V_HORIZ

BG, INK = 1, 3
N = 16


def blank():
    return [[BG] * N for _ in range(N)]


def place(grid, pat, ox, oy, w, h):
    """문자열 패턴('#'=잉크)을 (ox,oy)에 w x h로 스케일해 그린다."""
    ph = len(pat)
    pw = max(len(r) for r in pat)
    for yy in range(h):
        sy = min(ph - 1, yy * ph // h)
        for xx in range(w):
            sx = min(pw - 1, xx * pw // w)
            row = pat[sy]
            if sx < len(row) and row[sx] == '#':
                gx, gy = ox + xx, oy + yy
                if 0 <= gx < N and 0 <= gy < N:
                    grid[gy][gx] = INK


def vbar(grid, x, y0, y1, t=2):
    for y in range(y0, y1 + 1):
        for dx in range(t):
            if 0 <= x + dx < N and 0 <= y < N:
                grid[y][x + dx] = INK


def hbar(grid, y, x0, x1, t=2):
    for x in range(x0, x1 + 1):
        for dy in range(t):
            if 0 <= y + dy < N and 0 <= x < N:
                grid[y + dy][x] = INK


DOUBLE = {'ㄲ': 'ㄱ', 'ㄸ': 'ㄷ', 'ㅃ': 'ㅂ', 'ㅆ': 'ㅅ', 'ㅉ': 'ㅈ'}


def paint_cho(grid, cho, group, has_jong):
    base = DOUBLE.get(cho, cho)
    pat = CONS[base]
    if group == 'V':
        if has_jong:
            place(grid, pat, 1, 1, 9, 9)
        else:
            place(grid, pat, 1, 2, 9, 12)
        if cho in DOUBLE:          # 쌍자음: 좌측 세로 마커
            vbar(grid, 0, 1, 10 if has_jong else 13, t=1)
    elif group == 'H':  # 가로모음: 위쪽 중앙
        if has_jong:
            place(grid, pat, 3, 0, 10, 5)
        else:
            place(grid, pat, 3, 0, 10, 7)
        if cho in DOUBLE:
            grid[0][2] = INK; grid[0][14] = INK
    else:  # M 섞임: 좌상단
        if has_jong:
            place(grid, pat, 1, 0, 9, 5)
        else:
            place(grid, pat, 1, 0, 9, 7)
        if cho in DOUBLE:
            grid[0][0] = INK


def paint_jung(grid, jung, has_jong):
    if jung in V_VERT:
        bottom = 9 if has_jong else 14
        stem = 12
        vbar(grid, stem, 1, bottom, t=2)
        my = (1 + bottom) // 2
        if jung in ('ㅏ', 'ㅐ'):
            hbar(grid, my, stem, stem + 3, t=2)
        if jung in ('ㅓ', 'ㅔ'):
            hbar(grid, my, stem - 3, stem, t=2)
        if jung in ('ㅑ', 'ㅒ'):
            hbar(grid, my - 3, stem, stem + 3, t=2); hbar(grid, my + 2, stem, stem + 3, t=2)
        if jung in ('ㅕ', 'ㅖ'):
            hbar(grid, my - 3, stem - 3, stem, t=2); hbar(grid, my + 2, stem - 3, stem, t=2)
        if jung in ('ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'):   # 이중모음: 오른쪽 추가 세로
            vbar(grid, 15, 1, bottom, t=1)
        # ㅣ: 세로만
    elif jung in V_HORIZ:
        # 가로모음: 위=자음, 아래=가로획(+틱)
        up = 11 if not has_jong else 8    # ㅗ계열 가로선 위치
        dn = 9 if not has_jong else 7     # ㅜ계열 가로선 위치
        if jung == 'ㅗ':
            hbar(grid, up, 1, 14, t=2); vbar(grid, 7, up - 3, up - 1, t=2)
        elif jung == 'ㅛ':
            hbar(grid, up, 1, 14, t=2); vbar(grid, 4, up - 3, up - 1, t=2); vbar(grid, 10, up - 3, up - 1, t=2)
        elif jung == 'ㅜ':
            hbar(grid, dn, 1, 14, t=2); vbar(grid, 7, dn + 1, min(15, dn + 4), t=2)
        elif jung == 'ㅠ':
            hbar(grid, dn, 1, 14, t=2); vbar(grid, 4, dn + 1, min(15, dn + 4), t=2); vbar(grid, 10, dn + 1, min(15, dn + 4), t=2)
        else:  # ㅡ
            hbar(grid, up, 1, 14, t=2)
    else:  # 섞임(ㅘㅙㅚㅝㅞㅟㅢ): 아래 가로모음 + 오른쪽 세로(ㅣ) [+ ㅏ/ㅓ 가지]
        rstem = 13
        vbar(grid, rstem, 0, (9 if has_jong else 14), t=2)   # 오른쪽 ㅣ
        up = 10 if not has_jong else 7
        dn = 9 if not has_jong else 6
        my = (up + 1) // 2 + 2
        if jung in ('ㅘ', 'ㅙ', 'ㅚ'):   # ㅗ 계열
            hbar(grid, up, 1, 9, t=2); vbar(grid, 4, up - 3, up - 1, t=2)
        elif jung in ('ㅝ', 'ㅞ', 'ㅟ'): # ㅜ 계열
            hbar(grid, dn, 1, 9, t=2); vbar(grid, 4, dn + 1, min(11, dn + 3), t=2)
        else:  # ㅢ
            hbar(grid, up, 1, 9, t=2)
        if jung in ('ㅘ', 'ㅙ'):          # +ㅏ 가지(오른쪽 stem 밖으로)
            grid[my][rstem + 2] = INK
        if jung in ('ㅝ', 'ㅞ'):          # +ㅓ 가지(stem 안쪽)
            grid[my][rstem - 2] = INK


def paint_jong(grid, jong):
    if not jong:
        return
    key = jong if jong in JONG3 else jong[0]
    pat = JONG3.get(key, JONG3['ㅇ'])
    place(grid, pat, 2, 10, 12, 6)


def glyph16(ch):
    code = ord(ch)
    if ch == ' ':
        return blank()
    if not (0xAC00 <= code <= 0xD7A3):
        return None
    s = code - 0xAC00
    cho = CHO[s // 588]; jung = JUNG[(s % 588) // 28]; jong = JONG[s % 28]
    has_jong = bool(jong)
    group = 'V' if jung in V_VERT else ('H' if jung in V_HORIZ else 'M')
    g = blank()
    paint_cho(g, cho, group, has_jong)
    paint_jung(g, jung, has_jong)
    paint_jong(g, jong)
    return g


def to_tiles(g16):
    """16x16 -> [TL,TR,BL,BR] 각 8x8."""
    def quad(oy, ox):
        return [[g16[oy + y][ox + x] for x in range(8)] for y in range(8)]
    return [quad(0, 0), quad(0, 8), quad(8, 0), quad(8, 8)]


if __name__ == '__main__':
    import wsfont
    from PIL import Image
    test = sys.argv[1] if len(sys.argv) > 1 else "새게임로드설정불러오기저장확인취소"
    glyphs = [glyph16(c) for c in test if glyph16(c)]
    scale = 8
    img = Image.new('L', (len(glyphs) * 16 * scale, 16 * scale), 20)
    for i, g in enumerate(glyphs):
        t = Image.new('L', (16, 16))
        p = t.load()
        for y in range(16):
            for x in range(16):
                p[x, y] = [30, 110, 190, 255][g[y][x]]
        img.paste(t.resize((16 * scale, 16 * scale), Image.NEAREST), (i * 16 * scale, 0))
    img.save("work/hangul16_test.png")
    print("saved work/hangul16_test.png :", test)
