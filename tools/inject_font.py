#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_font.py - 한글 글리프를 ROM 빈 공간에 삽입하고 체크섬 수정
=================================================================

- ROM `0x14000-0x20000` (0xFF로 비어 있음) 영역에 한글 8x8 타일 폰트를 기록.
- 사용할 음절 집합을 자동 수집(코퍼스) -> 각 음절에 타일 슬롯 부여.
- 음절 -> 타일인덱스 매핑(kr_map.json) 저장 (향후 텍스트 삽입 시 사용).
- WonderSwan 체크섬 재계산 -> 유효한 patched.ws 산출.
- 패치 ROM에서 삽입 영역을 다시 렌더 -> 왕복 검증 시트 저장.

이 스크립트는 "폰트 파이프라인"을 정적으로 완전 검증한다(에뮬레이터 불필요).
실제 인게임 표시는 스크립트 인코딩을 이 매핑으로 재작성하는 다음 단계에서 이뤄진다.
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
from hangul8x8 import glyph_for

SRC_ROM = "랑그릿사 밀레니엄 WS - The Last Century.ws"
OUT_ROM = "랑그릿사_밀레니엄_한글POC.ws"
FREE_START = 0x14000          # 0xFF로 비어있는 뱅크 시작
FREE_END = 0x20000            # 다음 데이터(그래픽) 전까지
KR_TILE_BASE = FREE_START // wsfont.TILE_BYTES   # 타일 인덱스 기준

# POC용 한글 코퍼스: 메뉴/시스템/스토리에서 흔한 용어 (일→한 직접)
CORPUS = [
    "새게임", "이어하기", "불러오기", "저장하기", "설정", "종료",
    "예", "아니오", "확인", "취소", "다음", "이전",
    "랑그릿사", "밀레니엄", "빛의", "후예",
    "레벨", "경험치", "체력", "마력", "공격", "방어", "이동", "지형",
    "보병", "기병", "궁병", "창병", "비병", "마법사", "승려", "군주",
    "공격하시겠습니까", "부대를", "선택하세요",
    "장", "전투", "준비", "출격", "승리", "패배",
    "무기", "방패", "갑옷", "물약", "아이템", "소지금",
    "말을", "걸다", "기다리다", "이야기", "왕국", "제국", "빛", "어둠",
    "한글패치", "테스트", "가나다라마바사아자차카타파하",
]


def collect_syllables(corpus):
    seen = []
    s = set()
    for line in corpus:
        for ch in line:
            if 0xAC00 <= ord(ch) <= 0xD7A3 and ch not in s:
                s.add(ch)
                seen.append(ch)
    return seen


def main():
    rom = wsfont.load_rom(SRC_ROM)
    syllables = collect_syllables(CORPUS)
    capacity = (FREE_END - FREE_START) // wsfont.TILE_BYTES
    assert len(syllables) <= capacity, f"{len(syllables)} > capacity {capacity}"

    # 인덱스 0 = 전용 빈칸(공백) 타일. 음절은 그 다음부터.
    BLANK = [[wsfont.__dict__.get('BG', 1)] * 8 for _ in range(8)]  # 전부 배경색(1)
    BLANK = [[1] * 8 for _ in range(8)]
    wsfont.write_tile(rom, KR_TILE_BASE, BLANK)
    space_code = KR_TILE_BASE

    kr_map = {}
    for i, ch in enumerate(syllables):
        g = glyph_for(ch)
        tile_index = KR_TILE_BASE + 1 + i
        wsfont.write_tile(rom, tile_index, g)
        kr_map[ch] = tile_index

    old, new = wsfont.fix_checksum(rom)
    wsfont.save_rom(rom, OUT_ROM)

    json.dump({"tile_base": KR_TILE_BASE,
               "free_start": FREE_START,
               "space_code": space_code,
               "count": len(syllables),
               "capacity": capacity,
               "map": {ch: kr_map[ch] for ch in syllables}},
              open("work/kr_map.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"삽입 음절 수 : {len(syllables)} / 용량 {capacity}")
    print(f"타일 인덱스   : {KR_TILE_BASE:#x} ~ {KR_TILE_BASE+len(syllables)-1:#x}")
    print(f"ROM 오프셋    : {FREE_START:#x} ~ {FREE_START+len(syllables)*16:#x}")
    print(f"체크섬        : {old:#06x} -> {new:#06x}")
    print(f"산출 ROM      : {OUT_ROM}")

    # 왕복 검증: 패치된 ROM을 다시 읽어 삽입 영역 렌더
    rom2 = wsfont.load_rom(OUT_ROM)
    n = len(syllables)
    cols = 24
    img = wsfont.render_sheet(rom2, KR_TILE_BASE, ((n + cols - 1)//cols)*cols,
                              cols=cols, scale=7)
    img.save("work/verify_kr_injected.png")
    print("검증 시트     : work/verify_kr_injected.png")

    # 원본 ROM에서 같은 영역은 전부 0xFF(빈칸)였음을 확인
    was_blank = all(b == 0xFF for b in
                    wsfont.load_rom(SRC_ROM)[FREE_START:FREE_START+n*16])
    print(f"삽입 전 빈영역 : {'OK(전부 0xFF)' if was_blank else '경고: 비어있지 않음'}")


if __name__ == '__main__':
    main()
