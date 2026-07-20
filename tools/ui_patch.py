#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui_patch.py - 전투/시스템 UI + 대사 시작 한글화 (v3)
====================================================
(A) IN-PLACE: UI 한자(d3~e9) 글리프를 한글 한자음으로 교체 → 모든 곳 자동 한글화, 코드예산 0.
    지揮범위/수정/이동/공격/마법/회복/정보/대기/관/일람/종료 등.
(B) 문자열 코드 교체: katakana/hiragana 메뉴·대사는 안전 저코드(<=0x3c3)의 한글 글리프로.
게임 폰트 상한=0x4b3. 그 이하 코드만 사용.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
from hangul16 import glyph16 as kr_glyph16, to_tiles

SRC = "랑그릿사 밀레니엄 WS - The Last Century.ws"
OUT = "랑그릿사_밀레니엄_UI한글.ws"

# (A) IN-PLACE 한자 -> 한글 한자음
INPLACE = {
    0xd3:'지',0xd4:'휘',0xd5:'범',0xd6:'위',0xd7:'수',0xd8:'정',
    0xd9:'이',0xda:'동',0xdb:'공',0xdc:'격',0xdd:'마',0xde:'법',
    0xdf:'회',0xe0:'복',0xe1:'정',0xe2:'보',0xe3:'대',0xe4:'기',
    0xe5:'관',0xe6:'일',0xe7:'람',0xe8:'종',0xe9:'료',
}

# (B) 문자열 교체: (오프셋, [항목...]) 항목은 한글글자 or ('raw',코드)
S = '\x00'  # 공백 표시자
def kr(s): return list(s)
REPLACE = [
    # --- 타이틀 메뉴 ---
    (0xEBD02, kr("새게임")+[S]),                     # スタート
    (0xEBD0C, kr("로드")+[S]),                        # ロード
    (0xEBD14, ['설',('raw',0xd8)]+[S,S,S]),           # オプション -> 설정(정=d8 재사용)
    # --- 예/아니오 ---
    (0xEBB14, kr("예")+[S]),                          # はい
    (0xEBB1A, kr("아니오")),                          # いいえ
    # --- 대사 시험 번역 (인트로 シオン 장면) ---
    (0xA3006, [('raw',0x143),'위','험','해',('raw',0x2b),'놈','들','이',S,S]),   # 「まずい…。やつらの -> 「위험해…놈들이
    (0xA3114, [('raw',0x143),'시','온',('raw',0x27),'왜','그','래',('raw',0x29),S,S]),  # 「シオン、どうした？ -> 「시온、왜그래？
]
# in-place 자동 한글화: 전투명령(이동/공격/…), 상태창(지휘범위/수정), 지휘관일람(0xEBA70),
#   フェイズ終了->종료 등은 d3~e9 글리프 교체로 이미 커버(코드예산 0).
# 전투 시스템 메뉴(セーブ/シナリオ情報 등 카타카나)는 예산상 이번 버전에선 미포함(대사 우선).

FREE_CODES = [0x29b,0x348,0x34b,0x351,0x353,0x358,0x359,0x35a,0x35b,0x366,
              0x367,0x369,0x36b,0x36d,0x36e,0x378,0x379,0x37a,0x3af,0x3b5,
              0x3b6,0x3c3]


def write_glyph(rom, code, ch):
    g = kr_glyph16(ch) if ch != ' ' else [[1]*16 for _ in range(16)]
    tiles = to_tiles(g)
    base = (code-1)*4
    for k,t in enumerate(tiles): wsfont.write_tile(rom, base+k, t)


def main():
    rom = wsfont.load_rom(SRC)
    for code,ch in INPLACE.items(): write_glyph(rom, code, ch)
    print(f"in-place 한자->한글음: {len(INPLACE)}개")

    # 필요한 한글 음절 수집(문자만; raw/공백 제외)
    syl=[]; seen=set()
    for off,items in REPLACE:
        for it in items:
            if isinstance(it,str) and it!=S and it not in seen:
                seen.add(it); syl.append(it)
    syl.append(' ')  # 공백
    assert len(syl)<=len(FREE_CODES), f"{len(syl)}>{len(FREE_CODES)}: {''.join(syl)}"
    code_of={}
    for ch,code in zip(syl,FREE_CODES):
        write_glyph(rom,code,ch); code_of[ch]=code
    space=code_of[' ']
    print(f"free-code 한글: {len(syl)-1}음절 + 공백 -> 코드 <=0x{FREE_CODES[len(syl)-1]:x}")

    for off,items in REPLACE:
        codes=[]
        for it in items:
            if it==S: codes.append(space)
            elif isinstance(it,tuple): codes.append(it[1])
            else: codes.append(code_of[it])
        struct.pack_into("<%dH"%len(codes),rom,off,*codes)

    o,nw=wsfont.fix_checksum(rom); wsfont.save_rom(rom,OUT)
    print(f"교체 문자열: {len(REPLACE)}개\n체크섬 {o:#06x}->{nw:#06x}\n산출: {OUT}")


if __name__=='__main__':
    main()
