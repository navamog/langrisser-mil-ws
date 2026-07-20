#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wstext.py - WonderSwan 16비트 '타일코드' 텍스트 코덱
===================================================

역공학 결론:
  이 게임의 텍스트는 16비트 리틀엔디언 '타일 인덱스 코드'의 나열이다.
  코드 C 는 폰트 타일 C, 즉 ROM 오프셋 C*16 의 8x8 글리프를 가리킨다.
  => 일본어 읽기 = 각 코드의 폰트 타일 렌더.
  => 한글 삽입 = 코드를 삽입한 한글 타일 인덱스(0x1400+)로 교체.

이 모듈:
  - decode_codes(rom, off, n)         : 16비트 코드 n개 읽기
  - render_codes(rom, codes)          : 코드열 -> 글리프 띠 PNG (읽기용)
  - encode_korean(text, kr_map)       : 한글 문자열 -> 16비트 코드 bytes
  - write_codes(rom, off, codes)      : 코드열을 ROM에 기록(문자열 재작성)
"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__))
import wsfont


def decode_codes(rom, off, n):
    return list(struct.unpack_from("<%dH" % n, rom, off))


def render_codes(rom, codes, scale=6, pal=(40, 120, 200, 255), per_row=32):
    from PIL import Image
    rows = (len(codes) + per_row - 1) // per_row
    img = Image.new('RGB', (per_row * 8 * scale, rows * 8 * scale), (20, 20, 30))
    for i, cd in enumerate(codes):
        toff = cd * wsfont.TILE_BYTES
        if toff + 16 > len(rom):
            continue
        g = wsfont.decode_tile(rom, toff)
        t = Image.new('L', (8, 8)); p = t.load()
        for y in range(8):
            for x in range(8):
                p[x, y] = pal[g[y][x]]
        rx = (i % per_row) * 8 * scale
        ry = (i // per_row) * 8 * scale
        img.paste(t.resize((8 * scale, 8 * scale), Image.NEAREST).convert('RGB'), (rx, ry))
    return img


def encode_korean(text, kr_map, space_code=0x0000):
    """한글 문자열 -> 16비트 코드 bytes. kr_map: {음절: 타일인덱스}."""
    out = bytearray()
    for ch in text:
        if ch == ' ':
            code = space_code
        elif ch in kr_map:
            code = kr_map[ch]
        else:
            raise KeyError(f"'{ch}' 이(가) kr_map에 없음 - inject_font.py CORPUS에 추가 필요")
        out += struct.pack("<H", code)
    return bytes(out)


def write_codes(rom, off, code_bytes):
    rom[off:off + len(code_bytes)] = code_bytes


def load_kr_map(path="work/kr_map.json"):
    d = json.load(open(path, encoding="utf-8"))
    return {ch: idx for ch, idx in d["map"].items()}
