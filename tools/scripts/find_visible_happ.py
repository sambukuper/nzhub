"""Scan smali for remaining user-visible 'Happ' string constants."""
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\nzboost\Documents\workspace\happ-src\apktool")
DIRS = [ROOT / "smali", ROOT / "smali_classes2", ROOT / "smali_classes3"]
SKIP_PREFIXES = ("Lsu/", "su.happ", "happ://", "happ_user")
PAT = re.compile(r'const-string[^"]*"([^"]*[Hh]app[^"]*)"')

for d in DIRS:
    if not d.is_dir():
        continue
    for p in d.rglob("*.smali"):
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        for m in PAT.finditer(t):
            s = m.group(1)
            if s.startswith(SKIP_PREFIXES) or "su.happ" in s:
                continue
            print("VISIBLE:", p.name, repr(s))
