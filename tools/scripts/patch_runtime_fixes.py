import io, os, re, shutil, sys

REPO = r"C:/Users/nzboost/Documents/workspace/happ-src"
TOOLS = r"C:/Users/nzboost/Documents/workspace/tools"
APK = os.path.join(REPO, "apktool")


def read(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


# 1. drop the obfuscated-class stubs; injected code no longer references them
stubs = os.path.join(TOOLS, "inject", "stubs")
for root, dirs, files in os.walk(stubs):
    for fn in files:
        os.remove(os.path.join(root, fn))
print("stubs cleared")

# 2. BaseActivity: give ThemeManager/NZ an application context before setTheme
ba = os.path.join(APK, "smali_classes2", "su", "happ", "proxyutility", "ui", "BaseActivity.smali")
s = read(ba)
old = "    invoke-static {p1}, Lcom/nzboost/nzhub/theme/ThemeManager;->themeResourceId(Landroid/content/res/Resources;)I"
new = ("    invoke-static {p0}, Lcom/nzboost/nzhub/theme/ThemeManager;->attach(Landroid/content/Context;)V\n\n"
       "    invoke-static {p1}, Lcom/nzboost/nzhub/theme/ThemeManager;->themeResourceId(Landroid/content/res/Resources;)I")
assert s.count(old) == 1, "baseactivity hook count %d" % s.count(old)
write(ba, s.replace(old, new))
print("BaseActivity: attach() hook added")

# 3. MainViewModel: skip the FCM branch entirely. FirebaseInitProvider was deleted from
#    the manifest, so getInstance() throws and the catchall rethrows -> startup crash.
mv = os.path.join(APK, "smali_classes2", "su", "happ", "proxyutility", "feature", "main", "MainViewModel.smali")
lines = read(mv).split("\n")
hit = None
for i, ln in enumerate(lines):
    if "const-class p1, Lcom/google/firebase/messaging/FirebaseMessaging;" in ln:
        for j in range(i, max(i - 14, -1), -1):
            if lines[j].strip() == "if-eqz p1, :cond_4":
                hit = j
                break
        break
assert hit is not None, "FCM guard not found"
lines[hit] = "    goto :cond_4"
write(mv, "\n".join(lines))
print("MainViewModel: FCM branch bypassed at line %d" % (hit + 1))

# 4. FileProvider must be able to share the downloaded update from the external files dir
paths = os.path.join(APK, "res", "xml", "paths.xml")
s = read(paths)
if "external-files-path" not in s:
    s = s.replace("<cache-path", '<external-files-path name="nzhub_update_files" path="." />\n    <cache-path')
    write(paths, s)
print("paths.xml: external-files-path present")

# 5. build script: src-only javac (no stubs dir)
bs = os.path.join(TOOLS, "scripts", "build_nzhub.sh")
s = read(bs).replace('find "$INJECT/src" "$INJECT/stubs" -name "*.java"', 'find "$INJECT/src" -name "*.java"')
write(bs, s)
print("build script: stubs removed from javac sources")
