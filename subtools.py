"""
SubFinder subtitle tools
------------------------
- read_text()   : encoding auto-detect (utf-8 / utf-16 / cp1252 / latin-1)
- shift_srt()   : sob timestamp ek sathe aage/pichone sarano (sync fix)
- srt_to_vtt()  : .srt -> .vtt convert
- make_variant(): original file theke notun file baniye path dey
"""

import os
import re

TS = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})")

OPS = {
    "m5": ("-5s", -5.0), "m1": ("-1s", -1.0),
    "p1": ("+1s", 1.0), "p5": ("+5s", 5.0),
    "m05": ("-0.5s", -0.5), "p05": ("+0.5s", 0.5),
}


def read_text(path):
    raw = open(path, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _fmt(ms, sep):
    ms = max(0, int(ms))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{milli:03d}"


def shift_srt(text, seconds, sep=","):
    delta = int(round(seconds * 1000))

    def repl(m):
        h, mi, s, frac = m.groups()
        ms = ((int(h) * 60 + int(mi)) * 60 + int(s)) * 1000 + int(frac.ljust(3, "0")[:3])
        return _fmt(ms + delta, sep)

    out = []
    for line in text.splitlines():
        out.append(TS.sub(repl, line) if "-->" in line else line)
    return "\n".join(out) + "\n"


def srt_to_vtt(text):
    body = shift_srt(text, 0, sep=".")
    return "WEBVTT\n\n" + body


def make_variant(src_path, out_dir, op):
    """op: m5/m1/p1/p5/m05/p05/vtt -> (path, label)"""
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src_path))[0]
    text = read_text(src_path)
    if op == "vtt":
        path = os.path.join(out_dir, f"{stem}.vtt")
        data, label = srt_to_vtt(text), "VTT"
    elif op in OPS:
        label, secs = OPS[op]
        path = os.path.join(out_dir, f"{stem}.{op}.srt")
        data = shift_srt(text, secs)
    else:
        raise ValueError("unknown op")
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    return path, label
