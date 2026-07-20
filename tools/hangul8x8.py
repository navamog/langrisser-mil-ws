#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hangul8x8.py - 8x8 조합형(초·중·종성 합성) 한글 글리프 생성기
============================================================

WonderSwan 폰트에 맞춰 각 한글 음절을 8x8 2bpp 타일 색인 배열(0..3)로 생성한다.
색 배정은 원본 일본어 폰트와 동일: 배경=1, 잉크=3 (요청 시 가장자리=2 앤티에일리어싱).

8x8은 한글에 매우 좁으므로 완벽한 미려함보다 "판독 가능"을 목표로 한다.
초성/중성 배치는 세로모임(ㅏ계)·가로모임(ㅗ계)·섞임(ㅘ계)으로 나눈다.

사용:
  from hangul8x8 import glyph_for
  g = glyph_for('한')          # 8x8 색인 2D 리스트
"""

BG, INK = 1, 3

CHO = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONG = [''] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")

# 세로모임(오른쪽 세로획): ㅏㅐㅑㅒㅓㅔㅕㅖㅣ
V_VERT = {'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅣ'}
# 가로모임(아래 가로획): ㅗㅛㅜㅠㅡ
V_HORIZ = {'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ'}
# 섞임: ㅘㅙㅚㅝㅞㅟㅢ (나머지)


def blank():
    return [[BG] * 8 for _ in range(8)]


def _put5(grid, pat5, ox, oy, w=5, h=5):
    """5xN 문자열 패턴('#'=잉크)을 grid의 (ox,oy)에 w x h로 (필요시 리샘플) 그린다."""
    ph = len(pat5)
    pw = max(len(r) for r in pat5)
    for yy in range(h):
        sy = min(ph - 1, yy * ph // h)
        for xx in range(w):
            sx = min(pw - 1, xx * pw // w)
            row = pat5[sy]
            ch = row[sx] if sx < len(row) else '.'
            if ch == '#':
                gx, gy = ox + xx, oy + yy
                if 0 <= gx < 8 and 0 <= gy < 8:
                    grid[gy][gx] = INK


# 초성/종성 공용 자음 5x5 패턴
CONS = {
    'ㄱ': ["#####", "....#", "....#", "....#", "....#"],
    'ㄴ': ["#....", "#....", "#....", "#....", "#####"],
    'ㄷ': ["#####", "#....", "#....", "#....", "#####"],
    'ㄹ': ["#####", "....#", "#####", "#....", "#####"],
    'ㅁ': ["#####", "#...#", "#...#", "#...#", "#####"],
    'ㅂ': ["#...#", "#...#", "#####", "#...#", "#####"],
    'ㅅ': ["..#..", ".#.#.", ".#.#.", "#...#", "#...#"],
    'ㅇ': [".###.", "#...#", "#...#", "#...#", ".###."],
    'ㅈ': ["#####", "..#..", ".#.#.", "#...#", "#...#"],
    'ㅊ': ["..#..", "#####", ".#.#.", "#...#", "#...#"],
    'ㅋ': ["#####", "....#", "#####", "....#", "....#"],
    'ㅌ': ["#####", "#....", "#####", "#....", "#####"],
    'ㅍ': ["#####", ".#.#.", ".#.#.", ".#.#.", "#####"],
    'ㅎ': ["..#..", "#####", ".###.", "#...#", ".###."],
}
# 쌍자음은 기본 자음으로 근사(POC). 필요 시 좌우 반복으로 구분 가능.
for a, b in [('ㄲ', 'ㄱ'), ('ㄸ', 'ㄷ'), ('ㅃ', 'ㅂ'), ('ㅆ', 'ㅅ'), ('ㅉ', 'ㅈ')]:
    CONS[a] = CONS[b]

# 종성 전용 3행(높이3) 6-wide 패턴 — 눌림 방지용 깔끔한 받침.
JONG3 = {
    'ㄱ': ["######", ".....#", ".....#"],
    'ㄴ': ["#.....", "#.....", "######"],
    'ㄷ': ["######", "#.....", "######"],
    'ㄹ': ["######", ".#####", "######"],
    'ㅁ': ["######", "#....#", "######"],
    'ㅂ': ["#....#", "######", "######"],
    'ㅅ': ["#.##.#", ".#..#.", "#....#"],
    'ㅇ': [".####.", "#....#", ".####."],
    'ㅈ': ["######", ".#..#.", "#....#"],
    'ㅊ': ["##..##", "######", "#....#"],
    'ㅋ': ["######", "..####", ".....#"],
    'ㅌ': ["######", "###...", "######"],
    'ㅍ': ["######", "#.##.#", "######"],
    'ㅎ': ["##..##", "######", ".####."],
}


DOUBLE_CHO = {'ㄲ': 'ㄱ', 'ㄸ': 'ㄷ', 'ㅃ': 'ㅂ', 'ㅆ': 'ㅅ', 'ㅉ': 'ㅈ'}


def paint_cho(grid, cho, group, has_jong):
    is_double = cho in DOUBLE_CHO
    if group == 'V':
        # 왼쪽. 종성 있으면 세로 약간 압축.
        h = 5 if has_jong else 7
        _put5(grid, CONS[cho], 0, 0, w=5, h=h)
        if is_double:  # 쌍자음: 좌측에 세로 마커
            for y in range(0, min(h, 6)):
                grid[y][0] = INK
    else:  # H / M : 위쪽
        h = 3 if has_jong else 4
        _put5(grid, CONS[cho], 1, 0, w=6, h=h)
        if is_double:  # 쌍자음: 상단에 이중 점 마커
            grid[0][0] = INK
            grid[0][7] = INK


def paint_jung(grid, jung, has_jong):
    def vline(x, y0, y1):
        for y in range(y0, y1 + 1):
            if 0 <= x < 8 and 0 <= y < 8:
                grid[y][x] = INK

    def hline(y, x0, x1):
        for x in range(x0, x1 + 1):
            if 0 <= x < 8 and 0 <= y < 8:
                grid[y][x] = INK

    bottom = 4 if has_jong else 6   # 세로획 하단
    if jung in V_VERT:
        stem = 6
        vline(stem, 0, bottom)
        y = (bottom) // 2
        if jung in ('ㅏ', 'ㅐ'):
            grid[y][stem + 1] = INK
        if jung == 'ㅐ':
            vline(7, 0, bottom)
        if jung in ('ㅓ', 'ㅔ'):
            grid[y][stem - 1] = INK
        if jung == 'ㅔ':
            vline(7, 0, bottom)
        if jung in ('ㅑ', 'ㅒ'):
            grid[y - 1][stem + 1] = INK
            grid[y + 1][stem + 1] = INK
        if jung == 'ㅒ':
            vline(7, 0, bottom)
        if jung in ('ㅕ', 'ㅖ'):
            grid[y - 1][stem - 1] = INK
            grid[y + 1][stem - 1] = INK
        if jung == 'ㅖ':
            vline(7, 0, bottom)
        # ㅣ: stem만
    elif jung in V_HORIZ:
        ybar = 6 if not has_jong else 5
        hline(ybar, 1, 6)
        cx = 3
        if jung == 'ㅗ':
            vline(cx, ybar - 2, ybar - 1)
        elif jung == 'ㅛ':
            vline(2, ybar - 2, ybar - 1)
            vline(4, ybar - 2, ybar - 1)
        elif jung == 'ㅜ':
            vline(cx, ybar + 1, ybar + 2)
        elif jung == 'ㅠ':
            vline(2, ybar + 1, ybar + 2)
            vline(4, ybar + 1, ybar + 2)
        # ㅡ: 가로선만
    else:
        # 섞임(ㅘㅙㅚㅝㅞㅟㅢ) 근사: 아래 가로 + 오른쪽 세로 조합
        ybar = 6 if not has_jong else 5
        hline(ybar, 1, 5)
        vline(3, ybar - 2, ybar - 1) if jung in ('ㅘ', 'ㅙ', 'ㅚ') else None
        vline(3, ybar + 1, ybar + 2) if jung in ('ㅝ', 'ㅞ', 'ㅟ') else None
        vline(6, 0, bottom)
        if jung in ('ㅙ', 'ㅞ', 'ㅚ', 'ㅟ', 'ㅢ'):
            grid[(bottom) // 2][7] = INK


def paint_jong(grid, jong):
    if not jong:
        return
    # 겹받침은 대표(첫) 자음으로 근사(POC).
    key = jong if jong in JONG3 else jong[0]
    pat = JONG3.get(key, JONG3['ㅇ'])
    # 하단 3행(y=5..7)에 그대로 배치.
    for yy in range(3):
        row = pat[yy]
        for xx in range(6):
            if xx < len(row) and row[xx] == '#':
                grid[5 + yy][1 + xx] = INK


def glyph_for(ch):
    """한글 음절 1글자 -> 8x8 색인 2D 리스트. 한글 아니면 None."""
    code = ord(ch)
    if not (0xAC00 <= code <= 0xD7A3):
        return None
    s = code - 0xAC00
    cho = CHO[s // 588]
    jung = JUNG[(s % 588) // 28]
    jong = JONG[s % 28]
    has_jong = bool(jong)
    if jung in V_VERT:
        group = 'V'
    elif jung in V_HORIZ:
        group = 'H'
    else:
        group = 'M'
    g = blank()
    paint_cho(g, cho, group, has_jong)
    paint_jung(g, jung, has_jong)
    paint_jong(g, jong)
    return g


if __name__ == '__main__':
    import sys
    sys.path.insert(0, 'tools')
    import wsfont
    test = sys.argv[1] if len(sys.argv) > 1 else "한글패치랑그릿사밀레니엄테스트가나다라마바사아자차카타파하"
    glyphs = []
    for ch in test:
        g = glyph_for(ch)
        if g:
            glyphs.append(g)
    print(f"{len(glyphs)} syllables")
    for ch in test:
        g = glyph_for(ch)
        if g:
            print(ch)
            for row in g:
                print("  " + "".join(".·▒█"[v] for v in row))
    img = wsfont.render_glyphs(glyphs, cols=len(glyphs) if len(glyphs) < 20 else 20, scale=10)
    img.save("work/hangul_test.png")
    print("saved work/hangul_test.png")
