"""NZHub rebrand: user-visible string sweep across all Android resource values.

Only touches text content of <string> and <item> elements in strings.xml /
arrays.xml files under apktool/res/values* — never element names or attribute
values, and never public.xml / ids.
"""
import pathlib
import re

ROOT = pathlib.Path(r"C:\Users\nzboost\Documents\workspace\happ-src\apktool\res")

REPL = [
    # URLs first (before word replacements can mangle them)
    ("https://www.happ.su/main/faq", "https://github.com/sambukuper/nzhub#readme"),
    ("https://www.happ.su/main/privacy-policy", "https://github.com/sambukuper/nzhub/blob/main/PRIVACY.md"),
    ("https://www.happ.su/main/terms-of-services", "https://github.com/sambukuper/nzhub/blob/main/PRIVACY.md"),
    ("https://www.happ.su/main/third-party-libraries", "https://github.com/sambukuper/nzhub/blob/main/NOTICE.md"),
    ("https://www.happ.su", "https://github.com/sambukuper/nzhub"),
    ("https://happ.su", "https://github.com/sambukuper/nzhub"),
    ("happ.su", "github.com/sambukuper/nzhub"),
    ("t.me/happ_support_bot", "github.com/sambukuper/nzhub"),
    ("t.me/happ", "github.com/sambukuper/nzhub"),
    # Word replacements (keep happ:// scheme intact via lookbehind-free split)
    ("Happ", "NZHub"),
    ("HAPP", "NZHUB"),
]

WORD_HAPP = re.compile(r"(?<![A-Za-z0-9_])happ(?![A-Za-z0-9_])")


def fix_text(txt: str) -> str:
    for a, b in REPL:
        txt = txt.replace(a, b)
    # standalone lowercase 'happ' words (but not inside happ:// scheme)
    def sub(m):
        start = m.start()
        return "NZHub" if txt[max(0, start - 7):start] != "happ://" + txt[start:start] else m.group(0)
    return WORD_HAPP.sub("NZHub", txt)


TAG = re.compile(r"(<(?:string|item)\b[^>]*>)(.*?)(</(?:string|item)>)", re.S)


def main() -> None:
    touched = 0
    for p in ROOT.rglob("strings.xml"):
        t = p.read_text(encoding="utf-8", errors="surrogateescape")

        def repl_tag(m):
            return m.group(1) + fix_text(m.group(2)) + m.group(3)

        n = TAG.sub(repl_tag, t)
        # app_name exact override (in case value lacked the word 'Happ')
        n = re.sub(r'(<string name="app_name">).*?(</string>)', r"\g<1>NZHub\g<2>", n, flags=re.S)
        if n != t:
            p.write_text(n, encoding="utf-8", errors="surrogateescape")
            touched += 1
    for p in ROOT.rglob("arrays.xml"):
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        n = TAG.sub(lambda m: m.group(1) + fix_text(m.group(2)) + m.group(3), t)
        if n != t:
            p.write_text(n, encoding="utf-8", errors="surrogateescape")
            touched += 1
    print(f"{touched} resource files updated")

    # verify
    bad = []
    for p in ROOT.rglob("*.xml"):
        if p.name in ("public.xml",):
            continue
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        for m in re.finditer(r">([^<]*[Hh]app[^<]*)<", t):
            s = m.group(1)
            if "happ://" in s or "su.happ" in s:
                continue
            bad.append((str(p.relative_to(ROOT)), s[:80]))
    print(f"remaining visible 'happ' texts: {len(bad)}")
    for f, s in bad[:20]:
        print(" ", f, "|", s)


if __name__ == "__main__":
    main()
