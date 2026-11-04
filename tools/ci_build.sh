#!/usr/bin/env bash
# NZHub build: apktool rebuild + injected classes4.dex + zipalign + sign.
# Runs on Linux (GitHub Actions) and under Git Bash on Windows.
# Usage: ci_build.sh <output.apk>   (env: KEYSTORE + KEYSTORE_PASSWORD for signing,
# otherwise a temporary debug key is generated so CI can still produce an APK)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$ROOT/tools"
PROJECT="$ROOT/apktool"
WORK="${WORK_DIR:-$ROOT/_build}"
ANDROID_JAR="${ANDROID_JAR:-$TOOLS/android.jar}"
R8_VERSION="${R8_VERSION:-8.5.4}"
OUT="${1:-$WORK/NZHub.apk}"

mkdir -p "$WORK"

resolve_build_tools() {
  if [ -n "${ANDROID_HOME:-}" ] && ls "$ANDROID_HOME"/build-tools/*/zipalign* >/dev/null 2>&1; then
    BT="$(ls -d "$ANDROID_HOME"/build-tools/* | sort -V | tail -1)"
    echo "   build-tools from SDK: $BT"
    return
  fi
  if [ -d "$TOOLS/bt" ]; then
    BT="$TOOLS/bt"
    echo "   build-tools from tools/bt"
    return
  fi
  echo "== downloading build-tools"
  local zip="$WORK/bt.zip"
  curl -fsSL -o "$zip" https://dl.google.com/android/repository/build-tools_r34-linux.zip
  mkdir -p "$WORK/bt"
  python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$zip" "$WORK/bt"
  BT="$(ls -d "$WORK"/bt/android-14 | head -1)"
}

resolve_build_tools
EXE=""
case "$(uname -s)" in
  Linux) ZIPALIGN="$BT/zipalign"; APKSIGNER="$BT/apksigner" ;;
  *) ZIPALIGN="$BT/zipalign.exe"; APKSIGNER="$BT/apksigner.bat" ;;
esac

echo "== r8"
if [ -f "$TOOLS/r8.jar" ]; then
  R8="$TOOLS/r8.jar"
  echo "   using tools/r8.jar"
else
  R8="$WORK/r8.jar"
  curl -fsSL -o "$R8" \
    "https://dl.google.com/dl/android/maven2/com/android/tools/r8/$R8_VERSION/r8-$R8_VERSION.jar"
fi

echo "== compiling injected classes"
rm -rf "$WORK/inject_out" "$WORK/inject_dex"
mkdir -p "$WORK/inject_out" "$WORK/inject_dex"
find "$TOOLS/inject/src" -name "*.java" > "$WORK/sources.txt"
javac -source 8 -target 8 -nowarn -bootclasspath "$ANDROID_JAR" \
  -d "$WORK/inject_out" "@$WORK/sources.txt" 2>/dev/null
find "$WORK/inject_out/com/nzboost" -name "*.class" > "$WORK/classes.txt"
mapfile -t CLASSES < "$WORK/classes.txt"
java -cp "$R8" com.android.tools.r8.D8 --min-api 24 --release \
  --output "$WORK/inject_dex" "${CLASSES[@]}"
cp "$WORK/inject_dex/classes.dex" "$WORK/classes4.dex"
echo "   classes4.dex: $(wc -c < "$WORK/classes4.dex") bytes"

echo "== apktool build"
java -jar "$TOOLS/apktool.jar" b "$PROJECT" -o "$WORK/nzhub-unsigned.apk"

echo "== injecting classes4.dex"
cp "$WORK/nzhub-unsigned.apk" "$WORK/injected.apk"
python3 - "$WORK/injected.apk" "$WORK/classes4.dex" <<'PY'
import sys, zipfile
apk, dex = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(apk, "a", zipfile.ZIP_DEFLATED) as zf:
    zf.write(dex, "classes4.dex")
PY

echo "== zipalign"
"$ZIPALIGN" -p -f 4 "$WORK/injected.apk" "$WORK/aligned.apk"

echo "== signing"
if [ -n "${KEYSTORE:-}" ] && [ -n "${KEYSTORE_PASSWORD:-}" ]; then
  KS="$KEYSTORE"
else
  KS="$WORK/temp.keystore"
  KEYSTORE_PASSWORD="${KEYSTORE_PASSWORD:-nzhub-temp}"
  keytool -genkeypair -keystore "$KS" -storepass "$KEYSTORE_PASSWORD" -keypass "$KEYSTORE_PASSWORD" \
    -alias nzhub -keyalg RSA -keysize 2048 -validity 10950 \
    -dname "CN=NZHub, OU=NZBoost, O=NZBoost, C=DE" >/dev/null 2>&1
  echo "   WARNING: using a throwaway key, the APK cannot update a release build"
fi
rm -f "$OUT"
"$APKSIGNER" sign --ks "$KS" --ks-pass "pass:$KEYSTORE_PASSWORD" \
  --key-pass "pass:$KEYSTORE_PASSWORD" --out "$OUT" "$WORK/aligned.apk"
"$APKSIGNER" verify "$OUT"
echo "OK: $OUT ($(wc -c < "$OUT") bytes)"
