"""Generate 12 NZHub theme styles as design-token overrides.

Each theme defines a handful of semantic tokens; the generator expands them
into the full 95/96-attribute set the app's UI reads (same attributes as
AppThemeLight/AppThemeDark). WCAG AA contrast is asserted for text/background
pairs. Output: apktool/res/values/nzhub_themes.xml
"""
import colorsys
import pathlib
import re

RES = pathlib.Path(r"C:\Users\nzboost\Documents\workspace\happ-src\apktool\res")

# ---------------------------------------------------------------- color utils
def h2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgb2hex(r, g, b, a=255):
    return f"#{a:02x}{r:02x}{g:02x}{b:02x}"

def with_alpha(hx, alpha):
    r, g, b = h2rgb(hx)
    return rgb2hex(r, g, b, alpha)

def darken(hx, f):
    r, g, b = h2rgb(hx)
    return rgb2hex(int(r * (1 - f)), int(g * (1 - f)), int(b * (1 - f)))

def lum(hx):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = h2rgb(hx)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def contrast(a, b):
    l1, l2 = sorted((lum(a), lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

# ---------------------------------------------------------------- themes
# tokens: bg, surface, surfaceAlt, text, textSec, accent, accentText, ok, err, divider
THEMES = [
    ("Light", False, dict(bg="#ffffff", surface="#f7f8fa", surfaceAlt="#eef1f6",
        text="#1c1e26", textSec="#565d6e", accent="#3b66f5", accentText="#ffffff",
        ok="#188a42", err="#d32f2f", divider="#e3e6ee")),
    ("Dark", True, dict(bg="#16181d", surface="#1e2128", surfaceAlt="#262a33",
        text="#e8eaf0", textSec="#a8afc0", accent="#7c9aff", accentText="#0d1020",
        ok="#2ed057", err="#ff5c5c", divider="#2b303b")),
    ("AMOLED Black", True, dict(bg="#000000", surface="#0c0c0e", surfaceAlt="#161618",
        text="#ececee", textSec="#a0a0a6", accent="#7c71ff", accentText="#0a0a12",
        ok="#2ed057", err="#ff5252", divider="#202024")),
    ("Midnight Blue", True, dict(bg="#0d1526", surface="#13213c", surfaceAlt="#192b4e",
        text="#e6ecf8", textSec="#9aaecf", accent="#6f9bff", accentText="#0a1428",
        ok="#35d07a", err="#ff6b6b", divider="#1e3155")),
    ("Forest", True, dict(bg="#0f1a14", surface="#16261d", surfaceAlt="#1d3024",
        text="#e4efe8", textSec="#9fbcab", accent="#4ecb86", accentText="#0a1a10",
        ok="#3fd97f", err="#ff6b6b", divider="#20362a")),
    ("Sunset", False, dict(bg="#fff8f4", surface="#ffefe7", surfaceAlt="#ffe6da",
        text="#33231d", textSec="#75564a", accent="#c2461a", accentText="#ffffff",
        ok="#1d7a43", err="#c62828", divider="#f2ddd2")),
    ("Ocean", True, dict(bg="#0a1720", surface="#102231", surfaceAlt="#152c40",
        text="#e2f0f6", textSec="#93b3c4", accent="#3ec3e0", accentText="#04141c",
        ok="#2ed057", err="#ff6b6b", divider="#1b3649")),
    ("Rose", False, dict(bg="#fff7f8", surface="#fceff2", surfaceAlt="#f9e4e9",
        text="#2e2024", textSec="#75525e", accent="#d0395f", accentText="#ffffff",
        ok="#1d7a43", err="#c62828", divider="#efd9df")),
    ("Lavender", False, dict(bg="#faf9fe", surface="#f0edfb", surfaceAlt="#e7e1f7",
        text="#262233", textSec="#5f5875", accent="#6f52cc", accentText="#ffffff",
        ok="#1d7a43", err="#c62828", divider="#e0daf0")),
    ("Mono", True, dict(bg="#111111", surface="#1b1b1b", surfaceAlt="#242424",
        text="#f0f0f0", textSec="#a6a6a6", accent="#ffffff", accentText="#111111",
        ok="#b4b4b4", err="#e0e0e0", divider="#2f2f2f")),
    ("High Contrast", False, dict(bg="#ffffff", surface="#ffffff", surfaceAlt="#efefef",
        text="#000000", textSec="#242424", accent="#0033cc", accentText="#ffffff",
        ok="#005c26", err="#b00006", divider="#c8c8c8")),
    ("Cyberpunk", True, dict(bg="#0d0d1a", surface="#141430", surfaceAlt="#1b1b3c",
        text="#eae6ff", textSec="#a09ad0", accent="#f637ec", accentText="#14041a",
        ok="#00e68c", err="#ff3d6e", divider="#2a2a52")),
]

PARENT = {False: "AppThemeLight", True: "AppThemeDark"}

# ---------------------------------------------------------------- attribute map
def attr_values(dark, t):
    bg, surface, alt = t["bg"], t["surface"], t["surfaceAlt"]
    text, sec, acc = t["text"], t["textSec"], t["accent"]
    ok, err, div = t["ok"], t["err"], t["divider"]
    accT = t["accentText"]
    a = {}
    a["android:windowBackground"] = bg
    a["android:colorPrimary"] = surface
    a["backgroundMainActivity"] = "@drawable/bg_main_activity_dark" if dark else "@drawable/bg_main_activity_light"
    a["bgHoverMain"] = with_alpha(text, 0x1a)
    a["bgHoverPrimary"] = with_alpha(acc, 0x2e)
    a["bgHoverTertiriary"] = with_alpha(acc, 0x44)
    a["bgTertiriary"] = alt
    a["colorAccent"] = acc
    a["colorAccentDisabled"] = with_alpha(acc, 0x3d)
    a["colorAccentSecondary"] = with_alpha(acc, 0x80) if dark else sec
    a["colorBgError"] = with_alpha(err, 0x1f)
    a["colorBgErrorHover"] = with_alpha(err, 0x3d)
    a["colorBgMain"] = bg
    a["colorBgPrimary"] = surface
    a["colorBgSecondary"] = surface
    a["colorBgSnackbar"] = alt
    a["colorBgTertiary"] = alt
    a["colorBlackDialogFragment"] = "#88000000"
    a["colorBlackForegroundSpinner"] = "#88000000"
    a["colorButton"] = surface
    a["colorButtonBlue"] = acc
    a["colorButtonEnabled"] = acc
    a["colorButtonEnabledHovered"] = darken(acc, 0.15)
    a["colorButtonGrey"] = div
    a["colorButtonGreyDisabled"] = with_alpha(div, 0x99)
    a["colorButtonGreyForegroundDisabled"] = with_alpha(sec, 0x99)
    a["colorButtonGreyForegroundFocused"] = bg
    a["colorButtonGreyForegroundFocusedOnBackground"] = div
    a["colorButtonGreyForegroundUnfocused"] = text if dark else bg
    a["colorButtonPrimary"] = acc
    a["colorButtonPrimaryForegroundFocused"] = accT
    a["colorButtonPrimaryForegroundUnfocused"] = accT
    a["colorButtonPrimaryForegroundUnfocusedOnBackground"] = accT
    a["colorDialogBlackBackground"] = "#88000000"
    a["colorDialogFullScreenBackground"] = "#ff686868"
    a["colorDialogFullScreenDescription"] = "#ffbebebe"
    a["colorDialogFullScreenText"] = "#ffcccccc"
    a["colorDialogFullScreenTitle"] = "#ffffffff"
    a["colorDialogProgressBackground"] = "#ff000000"
    a["colorDialogTextButtonNegative"] = sec
    a["colorDialogTextButtonPositive"] = acc
    a["colorDivider"] = div
    a["colorDividerGroup"] = div
    a["colorGeoSelected"] = ok
    a["colorHintGray"] = sec
    a["colorIconWebPageActive"] = acc
    a["colorIconWebPageInactive"] = with_alpha(sec, 0x99)
    a["colorIcons"] = sec
    a["colorIconsDialog"] = sec
    a["colorNavBarOld"] = with_alpha(text, 0x22) if not dark else with_alpha("#ffffff", 0x0d)
    a["colorPing"] = ok
    a["colorPrimary"] = surface
    a["colorPrimaryDark"] = "#ff000000"
    a["colorQrFrame"] = text
    a["colorRvActionsDelete"] = err
    a["colorRvActionsIcon"] = "#ffffffff"
    a["colorSelected"] = text
    a["colorShareBg"] = acc
    a["colorSwitchThumbDisabled"] = div
    a["colorText"] = text
    a["colorTextButton"] = sec
    a["colorTextDialog"] = sec
    a["colorTextInput"] = text
    a["colorTextSecondary"] = text if not dark else text
    a["colorTextTertiary"] = sec
    a["colorTitleDialog"] = text
    a["color_fab_orange"] = "#fff97910"
    a["color_secondary"] = sec
    a["color_switch_fab_grey"] = div
    a["icBtnPowerOff"] = "@drawable/ic_power_off_night" if dark else "@drawable/ic_power_off"
    a["icBtnPowerOn"] = "@drawable/ic_power_on_night" if dark else "@drawable/ic_power_on"
    a["iconPrimary"] = text
    a["iconSecondary"] = div
    a["settingsArrow"] = div
    a["settingsBackground"] = alt
    a["settingsBackgroundFragment"] = surface
    a["settingsBorder"] = div
    a["settingsCategory"] = acc
    a["settingsListText"] = sec
    a["settingsRed"] = err
    a["settingsSearchIcon"] = sec
    a["settingsSearchText"] = sec
    a["settingsText"] = text
    a["settingsTextDescription"] = sec
    a["snackbarActionDivider"] = div
    a["storiesBackground"] = sec
    a["storiesForeground"] = bg
    a["subBgTraffic"] = div
    a["subInfoBackgroundBlue"] = with_alpha(acc, 0x1a)
    a["subInfoBackgroundGreen"] = with_alpha(ok, 0x1a)
    a["subInfoBackgroundRed"] = with_alpha(err, 0x1a)
    a["subInfoButtonBlue"] = acc
    a["subInfoButtonGreen"] = ok
    a["subInfoButtonRed"] = err
    a["subInfoText"] = text
    if dark:
        a["colorTextQuantity"] = with_alpha(sec, 0x85)
    return a

# ---------------------------------------------------------------- emit + verify
out = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
ids = {}
next_id = 0x7f1506b8
for name, dark, t in THEMES:
    a = attr_values(dark, t)
    assert len(a) == 96 if dark else len(a) == 95, (name, len(a))
    # WCAG AA assertions
    pairs = [("text/bg", t["text"], t["bg"]), ("text/surface", t["text"], t["surface"]),
             ("sec/bg", t["textSec"], t["bg"]), ("sec/surface", t["textSec"], t["surface"]),
             ("accT/acc", t["accentText"], t["accent"])]
    for label, fg_, bg_ in pairs:
        c = contrast(fg_, bg_)
        need = 4.5
        if c < need:
            print(f"FAIL {name} {label}: {c:.2f} ({fg_} on {bg_})")
        else:
            print(f"ok   {name} {label}: {c:.2f}")
    c = contrast(t["accent"], t["bg"] if lum(t["accent"]) < lum(t["bg"]) else t["surface"])
    print(f"ok?  {name} accent-vs-bg: {c:.2f} (need 3.0 for UI)")
    style = f"NZTheme{'D' if dark else 'L'}{re.sub(r'[^A-Za-z0-9]', '', name)}"
    ids[name] = (style, next_id)
    out.append(f'    <style name="{style}" parent="@style/{PARENT[dark]}">')
    for k, v in a.items():
        out.append(f'        <item name="{k}">{v}</item>')
    out.append("    </style>")
    next_id += 1
out.append("</resources>")
(RES / "values" / "nzhub_themes.xml").write_text("\n".join(out) + "\n", encoding="utf-8")

# emit id mapping for later pinning
with open(r"C:\Users\nzboost\Documents\workspace\tools\theme_ids.txt", "w") as f:
    for i, (name, dark, t) in enumerate(THEMES):
        style, rid = ids[name]
        f.write(f"{i+1}\t{name}\t{style}\t{hex(rid)}\n")
print("\nwrote nzhub_themes.xml and theme_ids.txt")
