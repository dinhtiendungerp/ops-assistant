#!/usr/bin/env bash
# Build mot app AL bang dong lenh (xem memory build-al-bang-dong-lenh). Dung: bash tools/build_al.sh <thu muc app>
# Ra file .app trong <thu muc app>/out, ten lay tu app.json. In loi va canh bao dang AL0xxx.
set -euo pipefail
APP_DIR="$(cd "$1" && pwd -W)"
DOTNET="C:/Users/dungdt.NWV/AppData/Roaming/Code/User/globalStorage/ms-dotnettools.vscode-dotnet-runtime/.dotnet/10.0.12~x64~aspnetcore/dotnet.exe"
ALC="C:/Users/dungdt.NWV/.vscode/extensions/ms-dynamics-smb.al-18.0.2732683/bin/alc.dll"
NAME=$(python -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d['publisher']+'_'+d['name']+'_'+d['version']+'.app')" "$APP_DIR/app.json")
mkdir -p "$APP_DIR/out"
"$DOTNET" "$ALC" "/project:$APP_DIR" "/packagecachepath:$APP_DIR/.alpackages" "/out:$APP_DIR/out/$NAME" 2>&1 | grep -E "error|warning|Compilation ended" || true
ls -la "$APP_DIR/out/$NAME" 2>/dev/null && echo "BUILT $APP_DIR/out/$NAME"
