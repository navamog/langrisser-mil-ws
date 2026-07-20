#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate.py - 랑그릿사 밀레니엄 WS 한글 번역 엔진 (전체 번역용)
==============================================================
확정된 폰트 매핑(code_to_slot)과 자유 코드 풀(0x4B0~)을 이용해,
한글 음절을 자유 코드에 배정·글리프 기록하고, 텍스트 문자열을 한글 코드로 교체한다.

- 문장부호는 기존 코드를 재사용(글리프 슬롯 절약).
- 각 문자열은 원본 코드 수에 맞춰 공백 패딩(원본 길이 초과 시 오류).
- 한글 음절 수는 자유 코드 풀(~840개)로 충분.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wsfont
from hangulttf import glyph16   # 실제 TTF(새굴림) 렌더 — 조합형 버그/둔탁함 해결
from krnames import NAMES


def _load(mod, name):
    try:
        m = __import__(mod)
        return getattr(m, name)
    except Exception as e:
        print(f"  (skip {mod}.{name}: {e})")
        return {}


STORY1 = _load('krstory1', 'STORY1')
DESC = _load('krdesc', 'DESC')
CRAWL = _load('krcrawl', 'CRAWL')
SC1 = _load('krsc1', 'SC1')
# 병렬 에이전트 번역 모듈(krst_*): {오프셋: "한글"}
_STORY_NAMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'tail', 'ui2', 'desc2', 'gap1', 'gap2']
_STORY_NAMES += [f'r{i}' for i in range(13)]  # 홀수정렬 누락 대사 재번역(1925개)
_STORY_NAMES += ['rx', 'ry', 'rz']  # 완화필터 누락(나레이션/시나리오명/한자많은대사)
STORY_MODS = {m: _load(f'krst_{m}', 'T') for m in _STORY_NAMES}

SRC = "랑그릿사 밀레니엄 WS - The Last Century.ws"
OUT = "랑그릿사_밀레니엄_한글.ws"

# 기존 코드 재사용할 문장부호/숫자/기호 (원본 폰트 글리프)
PUNCT = {
    '「': 0x143, '」': 0x144, '…': 0x2b, '、': 0x27, '。': 0x28,
    '！': 0x2a, '？': 0x29, '・': 0x2c, '／': 0x26, '·': 0x2c,
    '（': 0x30c, '）': 0x30d, '＋': 0x25, '－': 0x493, '：': 0x190,
    # ASCII 부호 → 게임 코드(정규화)
    '!': 0x2a, '?': 0x29, '(': 0x30c, ')': 0x30d, '.': 0x28, ',': 0x27,
    ':': 0x190, '+': 0x25, '-': 0x493, '/': 0x26, ' ': None,
    '—': 0x2e, '―': 0x2e, '～': 0x2e, '─': 0x2e, 'ー': 0x2e,
}
PUNCT.update({str(i): i + 1 for i in range(10)})            # 폰트 숫자 '0'->0x1 … '9'->0xa
PUNCT.update({chr(ord('A') + i): 0xb + i for i in range(26)})  # 폰트 대문자 A=0xb … Z=0x24
del PUNCT[' ']


KR_HARD_END = 0x7FC  # 폰트영역(파일 0~0x20000, 슬롯 0~0x7FF) 상 렌더 가능한 최대 코드


class KRFont:
    """한글 음절 -> 자유 코드 배정 + 글리프 기록.
    1차 풀(0x4B0~0x7FC) 소진 시, reclaim 풀(번역 후 미참조 저코드=일본어 한자 슬롯)로 확장."""
    def __init__(self, rom, reclaim=None):
        self.rom = rom
        self.next = wsfont.KR_CODE_START
        self.map = {}
        self.reclaim = list(reclaim or [])   # 재활용 저코드(정렬)
        self.ri = 0
        self.reclaimed_used = 0
        # 공백(blank) 글리프 미리 배정
        self.space = self._alloc_blank()

    def _next_code(self):
        """다음 렌더 가능한 코드 하나 반환(1차 풀 우선, 이후 reclaim)."""
        if self.next <= KR_HARD_END:
            c = self.next; self.next += 1
            return c
        # 1차 풀 소진 -> reclaim 풀 사용
        assert self.ri < len(self.reclaim), "코드 풀 완전 소진(reclaim 부족)"
        c = self.reclaim[self.ri]; self.ri += 1; self.reclaimed_used += 1
        return c

    def _alloc_blank(self):
        code = self._next_code()
        wsfont.write_glyph16(self.rom, code, [[1] * 16 for _ in range(16)])
        return code

    def code(self, ch):
        if ch == ' ':
            return self.space
        if ch in PUNCT and PUNCT[ch] is not None:
            return PUNCT[ch]
        if ch in self.map:
            return self.map[ch]
        g = glyph16(ch)
        if g is None:
            print(f"  ⚠ 미매핑 문자 {ch!r} -> 공백 대체")
            return self.space
        code = self._next_code()
        wsfont.write_glyph16(self.rom, code, g)
        self.map[ch] = code
        return code


def string_len(rom, off):
    """오프셋의 문자열(연속 글리프 코드) 길이."""
    n = 0
    while True:
        v = struct.unpack_from("<H", rom, off + n * 2)[0]
        if 1 <= v <= 0x500:
            n += 1
        else:
            break
    return n


def condense(text, n):
    """번역이 원본칸(n)을 넘으면 손실을 최소화해 압축:
    1) 오른쪽부터 공백 제거(전각 유지 기조는 넘치는 줄에만 예외)
    2) 그래도 넘치면 …… -> … 축약."""
    if len(text) <= n:
        return text
    t = text
    while len(t) > n and ' ' in t:
        idx = t.rfind(' '); t = t[:idx] + t[idx + 1:]
    while len(t) > n and '……' in t:
        t = t.replace('……', '…', 1)
    return t


def apply(rom, krf, off, text):
    """text(한글/부호)를 off 위치에 기록. 원본 길이에 맞춰 공백 패딩."""
    n = string_len(rom, off)
    text = condense(text, n)
    chars = list(text)
    if len(chars) > n:
        print(f"  ⚠ {hex(off)}: '{text}'({len(chars)}) > 원본칸({n}) -> 자름")
        chars = chars[:n]
    chars += [' '] * (n - len(chars))
    codes = [krf.code(c) for c in chars]
    struct.pack_into("<%dH" % n, rom, off, *codes)


# ============ 번역 데이터 ============
# UI (확정 오프셋)
UI = {
    0xEBD02: "새게임", 0xEBD0C: "로드", 0xEBD14: "설정",       # 타이틀
    0xEBA52: "저장", 0xEBA5A: "로드", 0xEBA62: "시나리오정보",
    0xEBA70: "지휘관목록", 0xEBA7C: "설정", 0xEBA88: "페이즈종료",
    0xEBB14: "예", 0xEBB1A: "아니오",
    # 전투 유닛/아이템 메뉴 (정확 파싱)
    0xEBD80: "아이템", 0xEBD8A: "지휘관배치", 0xEBD96: "저장",
    0xEBD9E: "로드", 0xEBDA6: "출격", 0xEBDAC: "지휘관선택",
    0xEBDBA: "소지금", 0xEBDCA: "결정", 0xEBDD4: "돈이부족해요。",
    0xEBDFE: "아이템구입", 0xEBE14: "아이템판매",
    0xEBE30: "구입합니다。", 0xEBE3E: "판매합니다。",
    0xEBE84: "반지선택", 0xEBE92: "팔찌선택", 0xEBEA0: "기타선택",
    0xEBEEC: "마법선택",
    0xEBD76: "용병배속",     # 傭兵配属 (전투 유닛메뉴 첫줄)
    0xEC0CC: "소지금",       # 所持金 (상점 헤더)
    0xEBEDE: "출격합니다。",  # 出撃します。 (출격 확인 메시지)
    0xECBA2: "애",           # 愛 (캐릭터메이킹 가치관: 용기/애/지혜, 1코드)
}

# 인트로 シオン 장면 (0xA3006~)
INTRO = {
    0xA3006: "「위험해…놈들을",
    0xA301C: "얕잡아봤어。",
    0xA3034: "이대로면",
    0xA3042: "잡히고만다…。",
    0xA305A: "아마배안의것을",
    0xA306E: "캐물으러올거야…。",
    0xA308C: "…어쩔수없어。",
    0xA309C: "도망칠수밖에없네…！",
    0xA30C4: "「윽！위험해！",
    0xA30D6: "도망치려한다！",
    0xA30F4: "「놓칠까보냐！",
    0xA3114: "「시온、왜그래？",
    0xA312A: "아직망설이나？",
    0xA3140: "넌지금껏무엇을",
    0xA3158: "위해검을익혔느냐？",
    0xA317C: "「시온님、당신이",
    0xA3192: "여행을떠나…힘을",
    0xA31AC: "시험하고싶어했던",
    0xA31C2: "것을알고있었습니다。",
    0xA31E0: "만약그마음이",
    0xA31F4: "진심이아니라면…",
    0xA320E: "아무말않겠어요。",
    0xA3224: "당장돌아가세요。",
    0xA3246: "「…돌아가라고…？",
}


INPLACE = {0xd3:'지',0xd4:'휘',0xd5:'범',0xd6:'위',0xd7:'수',0xd8:'정',
           0xd9:'이',0xda:'동',0xdb:'공',0xdc:'격',0xdd:'마',0xde:'법',
           0xdf:'회',0xe0:'복',0xe1:'정',0xe2:'보',0xe3:'대',0xe4:'기',
           0xe5:'관',0xe6:'일',0xe7:'람',0xe8:'종',0xe9:'료'}


def compute_reclaim(rom, translated_offsets):
    """번역 후에도 렌더될 수 있는 저코드(일본어 한자/가나 슬롯) 중,
    '미번역 텍스트가 참조하지 않는' 코드만 골라 재활용 풀로 반환.
    보수적: 원본 ROM의 모든 텍스트열(코드 1~0x7f9, len>=2)을 훑어,
    번역대상이 아닌 문자열의 코드는 전부 keep(보존). 데이터표도 보존(안전측)."""
    keep = set()
    # 원본 텍스트열 스캔
    n = len(rom)
    i = 0
    while i < n - 1:
        v = struct.unpack_from("<H", rom, i)[0]
        if 1 <= v <= 0x7f9:
            start = i; codes = []
            while i < n - 1:
                v = struct.unpack_from("<H", rom, i)[0]
                if 1 <= v <= 0x7f9:
                    codes.append(v); i += 2
                else:
                    break
            if len(codes) >= 2 and start not in translated_offsets:
                keep.update(codes)
        else:
            i += 2
    # 항상 보존: PUNCT 재사용 코드, 숫자/영문, INPLACE 한자음 슬롯
    keep.update(c for c in PUNCT.values() if c is not None)
    keep.update(INPLACE.keys())
    # 재활용 후보: 0x25~0x4AF(가나/한자 슬롯) 중 keep 아닌 것
    reclaim = [c for c in range(0x25, wsfont.KR_CODE_START) if c not in keep]
    return reclaim, len(keep)


def main():
    rom = wsfont.load_rom(SRC)
    tables = [("UI", UI), ("INTRO", INTRO), ("NAMES", NAMES),
              ("STORY1", STORY1), ("DESC", DESC), ("CRAWL", CRAWL), ("SC1", SC1)]
    tables += [(f"STORY_{m}", t) for m, t in STORY_MODS.items()]
    # 병합(뒤 테이블이 중복 오프셋 덮어씀)
    merged = {}
    for name, tbl in tables:
        merged.update(tbl)
    # 자동 압축으로도 안 맞는 극단 짧은 칸 수동 오버라이드
    OVERRIDE = {0xa4ce0: "인걸。"}  # なの。(3칸)
    merged.update(OVERRIDE)
    # 재활용 풀 계산(원본 rom 기준, 아직 미기록 상태)
    reclaim, nkeep = compute_reclaim(rom, set(merged.keys()))
    print(f"번역대상 오프셋: {len(merged)}개 / 보존코드(keep): {nkeep}개 / 재활용 후보: {len(reclaim)}개")

    krf = KRFont(rom, reclaim=reclaim)
    # UI 한자 in-place(코드예산 0): 상태창/명령 한자 -> 한글 한자음
    for code, ch in INPLACE.items():
        wsfont.write_glyph16(rom, code, glyph16(ch))
    # 스크립트 영역(0xA0000~0xC8200)은 유효 레코드 시작에만 기록(팬텀/오정렬 방지)
    import records
    starts = records.valid_starts(bytes(rom))
    skipped = 0
    for off, text in merged.items():
        if records.SCRIPT_S <= off < records.SCRIPT_E and off not in starts:
            skipped += 1
            continue
        apply(rom, krf, off, text)
    if skipped:
        print(f"  (팬텀/오정렬 오프셋 {skipped}개 스킵)")
    o, nw = wsfont.fix_checksum(rom)
    wsfont.save_rom(rom, OUT)
    prim = min(krf.next - 1, KR_HARD_END)
    print(f"번역 문자열: {len(merged)}개")
    print(f"한글 음절 배정: {len(krf.map)}개")
    print(f"  1차 풀 사용: 0x{wsfont.KR_CODE_START:x}~0x{prim:x}, 재활용 사용: {krf.reclaimed_used}개")
    print(f"  재활용 잔여: {len(krf.reclaim) - krf.ri}개")
    print(f"체크섬 {o:#06x} -> {nw:#06x}\n산출: {OUT}")


if __name__ == '__main__':
    main()
