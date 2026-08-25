#!/bin/bash
# Rebuild the universal WKWebView helper committed next to this script.
#
# macos.zip is assembled on a Linux server, which cannot cross-compile macOS
# binaries — so the built artifact is committed to git alongside its source.
# After changing wta_webview.m, re-run this on any Mac with Xcode Command
# Line Tools and commit the result:
#
#   ./build.sh && git add wta_webview && git commit
set -euo pipefail
cd "$(dirname "$0")"

clang -arch arm64 -arch x86_64 -mmacosx-version-min=11.0 -Os -Wall \
  -framework Cocoa -framework WebKit \
  -o wta_webview wta_webview.m
strip wta_webview
# Ad-hoc signature: required for exec on Apple Silicon, no identity needed.
codesign --sign - --force --timestamp=none wta_webview
codesign --verify --strict wta_webview

file wta_webview
ls -lh wta_webview
