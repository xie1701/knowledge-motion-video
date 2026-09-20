#!/usr/bin/env python3
"""make_sfx.py — 用纯 stdlib 合成打包音效（纸张/笔尖/咔哒/嗖声），CC0 等效自产。

输出 wav 到 assets/sfx/。噪声合成音效质量足够做动效挂点提示音，
发布时在 manifest 里标注 "synthesized (bundled)"，用户可替换自己的音效。
"""
import math
import random
import struct
import sys
import wave
from pathlib import Path

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"


def _write(name: str, samples: list[float]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * 32767)))) for s in samples)
    with (OUT / name).open("wb") as f:
        with wave.open(f, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(data)
    print(f"  {name}  {len(samples)/SR:.2f}s")


def _env(n: int, a: float, r: float) -> list[float]:
    """attack/release 包络（比例）。"""
    na, nr = int(n * a), int(n * r)
    out = []
    for i in range(n):
        if i < na:
            out.append(i / max(1, na))
        elif i > n - nr:
            out.append((n - i) / max(1, nr))
        else:
            out.append(1.0)
    return out


def _noise(sec: float, amp: float, lp: float = 0.9, trem_f: float = 0.0, trem_d: float = 0.0,
           a: float = 0.08, r: float = 0.3, seed: int = 7) -> list[float]:
    rnd = random.Random(seed)
    n = int(SR * sec)
    out, y = [], 0.0
    for i in range(n):
        y += lp * ((rnd.random() * 2 - 1) - y)  # 一阶低通
        g = 1.0
        if trem_f:
            g *= 1.0 - trem_d * (0.5 + 0.5 * math.sin(2 * math.pi * trem_f * i / SR))
        out.append(y * amp * g * _env(n, a, r)[i])
    return out


def _peak(sec: float, amp: float, hp: float = 0.0, seed: int = 3) -> list[float]:
    rnd = random.Random(seed)
    n = int(SR * sec)
    out, prev = [], 0.0
    for i in range(n):
        x = rnd.random() * 2 - 1
        v = x - prev * hp
        prev = x
        out.append(v * amp * (1 - i / n) ** 2)
    return out


def paper_rustle() -> list[float]:
    return _noise(0.9, 0.55, lp=0.55, trem_f=9, trem_d=0.85, a=0.09, r=0.35)


def page_flip() -> list[float]:
    s = _noise(0.35, 0.5, lp=0.8, trem_f=16, trem_d=0.9, a=0.05, r=0.55)
    k = _peak(0.08, 0.25, hp=0.5)
    return s[:int(SR * 0.02)] + k + s[int(SR * 0.02) + len(k):]


def pen_scratch() -> list[float]:
    return _noise(0.5, 0.4, lp=0.92, trem_f=22, trem_d=0.8, a=0.05, r=0.4)


def click() -> list[float]:
    return _peak(0.12, 0.6, hp=0.6)


def whoosh() -> list[float]:
    return _noise(0.5, 0.8, lp=0.12, a=0.3, r=0.5)


if __name__ == "__main__":
    print("合成音效 →", OUT)
    _write("paper-rustle.wav", paper_rustle())
    _write("page-flip.wav", page_flip())
    _write("pen-scratch.wav", pen_scratch())
    _write("click.wav", click())
    _write("whoosh.wav", whoosh())
