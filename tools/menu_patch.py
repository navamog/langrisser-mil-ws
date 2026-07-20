#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu_patch.py - 메인 메뉴(スタート/ロード/オプション)를 한글로 교체
=================================================================

역공학 결과:
  - 텍스트 폰트 = 16x16 (글자당 8x8 타일 4개, row-major TL,TR,BL,BR).
    글자 code C -> 타일 base = (C-1)*4  (ROM 오프셋 (C-1)*64).
  - 메뉴 텍스트는 비압축 16비트 LE 코드로 ROM 0xEBD02~ 에 저장. 구분자 0xffff/0xfffe.
      0xEBD02 スタート = [3f 42 2e 46]
      0xEBD0C ロード   = [5d 2e 6f]
      0xEBD14 オプション= [37 77 3e 81 60]

패치:
  1) 16x16 한글 글리프(공백,새,게,임,로,드,설,정)를 빈 공간(타일 0x1400~)에 4타일씩 기록.
  2) 각 글리프 code = 타일base/4 + 1.
  3) 메뉴 코드열을 한글 code로 교체(코드 수 유지, 남는 칸은 공백).
  4) 체크섬 재계산 -> 산출 ROM.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
from hangul16 import glyph16, to_tiles

SRC = "랑그릿사 밀레니엄 WS - The Last Century.ws"
OUT = "랑그릿사_밀레니엄_한글메뉴POC.ws"

# 삽입할 글리프: 순서대로 TILE_BASE부터 4타일씩
GLYPHS = [' ', '새', '게', '임', '로', '드', '설', '정']
# 빈 공간(0x1400=code0x501+)은 게임 폰트 렌더러가 못 읽을 수 있어,
# 확실히 접근되는 기존 한자 글리프 영역(타일 0x400 = code 0x101+)을 덮어쓴다.
TILE_BASE = 0x400   # code 0x101~ (기존 한자 闘敵行… 자리)


def code_for(index):
    tile_base = TILE_BASE + index * 4
    return tile_base // 4 + 1, tile_base


def main():
    rom = wsfont.load_rom(SRC)

    codemap = {}
    for i, ch in enumerate(GLYPHS):
        g = glyph16(ch)
        tiles = to_tiles(g)          # [TL,TR,BL,BR]
        code, tb = code_for(i)
        for k, tile in enumerate(tiles):
            wsfont.write_tile(rom, tb + k, tile)
        codemap[ch] = code
    print("글리프 코드:", {c: hex(v) for c, v in codemap.items()})

    S = codemap
    # (오프셋, 원본코드수, 새 코드열) — 코드 수는 원본과 동일(남는 칸 공백)
    repl = [
        (0xEBD02, 4, [S['새'], S['게'], S['임'], S[' ']]),        # スタート -> 새게임
        (0xEBD0C, 3, [S['로'], S['드'], S[' ']]),                  # ロード   -> 로드
        (0xEBD14, 5, [S['설'], S['정'], S[' '], S[' '], S[' ']]),  # オプション-> 설정
    ]
    for off, n, codes in repl:
        assert len(codes) == n
        old = struct.unpack_from("<%dH" % n, rom, off)
        for j, c in enumerate(codes):
            struct.pack_into("<H", rom, off + j * 2, c)
        print(f"  {hex(off)}: {[hex(x) for x in old]} -> {[hex(x) for x in codes]}")

    old, new = wsfont.fix_checksum(rom)
    wsfont.save_rom(rom, OUT)
    print(f"체크섬 {old:#06x} -> {new:#06x}")
    print("산출:", OUT)


if __name__ == '__main__':
    main()
