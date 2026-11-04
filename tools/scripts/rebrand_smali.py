"""NZHub rebrand: exact-string replacements across apktool smali trees.

Rules are ordered: longer/more-specific strings first where they overlap.
Each rule reports its replacement count for verification.
"""
import pathlib
import sys

ROOT = pathlib.Path(r"C:\Users\nzboost\Documents\workspace\happ-src\apktool")
SMALI_DIRS = [ROOT / "smali", ROOT / "smali_classes2", ROOT / "smali_classes3"]

# (old, new) exact literal replacements inside file text
RULES = [
    # --- App ID literals (intents, headers, bundle ids) ---
    ('"su.happ.proxyutility.provider"', '"com.nzboost.nzhub.provider"'),
    ('"su.happ.proxyutility"', '"com.nzboost.nzhub"'),
    # --- Update config URLs (legacy release-file channel -> our repo) ---
    ('"https://raw.githubusercontent.com/Happ-proxy/happ-android/refs/heads/main/release"',
     '"https://raw.githubusercontent.com/sambukuper/nzhub/main/release"'),
    ('"https://cdn.jsdelivr.net/gh/Happ-proxy/happ-android@main/release"',
     '"https://cdn.jsdelivr.net/gh/sambukuper/nzhub@main/release"'),
    ('"https://pastebin.com/raw/vc3ficrq"',
     '"https://raw.githubusercontent.com/sambukuper/nzhub/main/release"'),
    # --- Subscription URL protection domain list (vendor into our repo) ---
    ('"https://cdn.jsdelivr.net/gh/Happ-proxy/app_domain@main/list.json"',
     '"https://cdn.jsdelivr.net/gh/sambukuper/nzhub@main/app_domain/list.json"'),
    ('"https://raw.githubusercontent.com/Happ-proxy/app_domain/refs/heads/main/list.json"',
     '"https://raw.githubusercontent.com/sambukuper/nzhub/main/app_domain/list.json"'),
    # --- Docs / FAQ / about links ---
    ('"https://ai-4docs.com/happ"', '"https://github.com/sambukuper/nzhub#readme"'),
    ('"https://www.happ.su/main/third-party-libraries"',
     '"https://github.com/sambukuper/nzhub/blob/main/NOTICE.md"'),
    ('"https://www.happ.su/main/terms-of-services"',
     '"https://github.com/sambukuper/nzhub/blob/main/PRIVACY.md"'),
    ('"https://www.happ.su/main/privacy-policy"',
     '"https://github.com/sambukuper/nzhub/blob/main/PRIVACY.md"'),
    ('"https://www.happ.su/main/ru/vacancies"',
     '"https://github.com/sambukuper/nzhub#readme"'),
    ('"https://www.happ.su/main/zh/faq"', '"https://github.com/sambukuper/nzhub#readme"'),
    ('"https://www.happ.su/main/ru/faq"', '"https://github.com/sambukuper/nzhub#readme"'),
    ('"https://www.happ.su/main/faq"', '"https://github.com/sambukuper/nzhub#readme"'),
    # --- TV app link ---
    ('"https://tv.happ.su.*"', '"https://github.com/sambukuper/nzhub.*"'),
    ('"https://tv.happ.su/"', '"https://github.com/sambukuper/nzhub"'),
    # --- Telegram support bot ---
    ('"t.me/happ_support_bot&start="', '"github.com/sambukuper/nzhub/issues"'),
    ('"t.me/happ_support_bot"', '"github.com/sambukuper/nzhub/issues"'),
    # --- Sentry DSN (init call also removed from HappApplication) ---
    ('"https://dc4747c4eb1f380d72dd79917ed695c7@o312638.ingest.us.sentry.io/4507922783731712"', '""'),
    # --- Connectivity check: consolidate on non-branded endpoint ---
    ('"https://check.happ.su/files/data.result"', '"https://mathh.app/files/data.result"'),
    # --- Telemetry / install beacons -> unroutable loopback (instant refusal) ---
    ('"https://time-ntp.com/v1report"', '"http://127.0.0.1:1/v1report"'),
    ('"https://ntp2-sync.com/v1install?id="', '"http://127.0.0.1:1/v1install?id="'),
    ('"https://time-ntp.com/v1install?id="', '"http://127.0.0.1:1/v1install?id="'),
    ('"https://ntp2-sync.com/v1sendtv/"', '"http://127.0.0.1:1/v1sendtv/"'),
    ('"https://ntp2-sync.com/v1remotepush?token="', '"http://127.0.0.1:1/v1remotepush?token="'),
    ('"https://ntp2-sync.com"', '"http://127.0.0.1:1"'),
    ('"https://time-ntp.com"', '"http://127.0.0.1:1"'),
    ('"https://check.happ.su"', '"http://127.0.0.1:1"'),
]


def main() -> None:
    counts = [0] * len(RULES)
    files_touched = 0
    for d in SMALI_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*.smali"):
            text = p.read_text(encoding="utf-8", errors="surrogateescape")
            new = text
            for i, (old, repl) in enumerate(RULES):
                if old in new:
                    counts[i] += new.count(old)
                    new = new.replace(old, repl)
            if new != text:
                p.write_text(new, encoding="utf-8", errors="surrogateescape")
                files_touched += 1
    for (old, _), c in zip(RULES, counts):
        if c:
            print(f"{c:4d}x  {old[:90]}")
    print(f"\n{files_touched} smali files modified")
    # leftovers check
    leftovers = 0
    for d in SMALI_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*.smali"):
            t = p.read_text(encoding="utf-8", errors="surrogateescape")
            for bad in ("happ.su", "happ_support_bot", "ai-4docs", "sentry.io/45", "Happ-proxy/happ-android", "Happ-proxy/app_domain", "time-ntp.com", "ntp2-sync.com"):
                if bad in t:
                    print(f"LEFTOVER {bad!r} in {p}")
                    leftovers += 1
    print(f"leftovers: {leftovers}")


if __name__ == "__main__":
    sys.exit(main())
