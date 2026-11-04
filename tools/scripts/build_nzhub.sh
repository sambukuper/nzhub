#!/usr/bin/env bash
# NZHub build: apktool rebuild + classes4.dex injection + zipalign + sign.
# Usage: build_nzhub.sh [output.apk] [--no-compile]
set -euo pipefail

REPO="C:/Users/nzboost/Documents/workspace/happ-src"
TOOLS="C:/Users/nzboost/Documents/workspace/tools"
APKTOOL="$TOOLS/apktool.jar"
BT="$TOOLS/bt/android-14"
INJECT="$TOOLS/inject"
OUT="${1:-$TOOLS/NZHub-1.0.0.apk}"
KEYSTORE="$TOOLS/nzhub.keystore"
KSPASS="nzhub123"

compile_inject() {
  echo "== compiling injected classes"
  rm -rf "$INJECT/out" "$INJECT/dexout"
  mkdir -p "$INJECT/out" "$INJECT/dexout"
  find "$INJECT/src" -name "*.java" > "$INJECT/sources.txt"
  javac -source 8 -target 8 \
    -bootclasspath "$TOOLS/platform/android-34/android.jar" \
    -d "$INJECT/out" @"$INJECT/sources.txt" 2>&1 | grep -v "bootstrap class path\|source value 8\|target value 8\|obsolete options" || true
  local classes=()
  while IFS= read -r f; do classes+=("$f"); done < <(find "$INJECT/out/com/nzboost" -name "*.class")
  java -cp "$TOOLS/r8.jar" com.android.tools.r8.D8 --min-api 24 --release \
    --output "$INJECT/dexout" "${classes[@]}"
  cp "$INJECT/dexout/classes.dex" "$INJECT/classes4.dex"
  echo "   classes4.dex: $(stat -c%s "$INJECT/classes4.dex") bytes"
}

[ "${2:-}" != "--no-compile" ] && compile_inject

echo "== apktool build"
java -jar "$APKTOOL" b "$REPO/apktool" -o "$TOOLS/nzhub-unsigned.apk" 2>&1 | tail -2

echo "== injecting classes4.dex"
cd "$TOOLS"
rm -f injected.apk
cp nzhub-unsigned.apk injected.apk
mkdir -p classes4_inject
cp -f "$INJECT/classes4.dex" classes4_inject/classes4.dex
# `zip` is not installed on this box; python appends the dex into the existing archive.
python -c "import zipfile,sys; zf=zipfile.ZipFile(sys.argv[1],'a',zipfile.ZIP_DEFLATED); zf.write(sys.argv[2],'classes4.dex'); zf.close()" injected.apk classes4_inject/classes4.dex

echo "== zipalign"
rm -f aligned.apk
"$BT/zipalign.exe" -p -f 4 injected.apk aligned.apk

echo "== keystore"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -keystore "$KEYSTORE" -storepass "$KSPASS" -keypass "$KSPASS" \
    -alias nzhub -keyalg RSA -keysize 2048 -validity 10950 \
    -dname "CN=NZHub, OU=NZBoost, O=NZBoost, C=NZ"
fi

echo "== signing"
rm -f "$OUT"
"$BT/apksigner.bat" sign --ks "$KEYSTORE" --ks-pass "pass:$KSPASS" \
  --key-pass "pass:$KSPASS" --out "$OUT" aligned.apk
"$BT/apksigner.bat" verify "$OUT" && echo "OK: $OUT"
