#!/bin/bash

APP_NAME="MMqBt"
MAIN_SCRIPT="macmenuqbt/core.py"
ICON_FILE="icon.icns"
REQUIREMENTS_FILE="requirements.txt"

HIDDEN_IMPORTS=""
if [ -f "$REQUIREMENTS_FILE" ]; then
    while read -r pkg || [ -n "$pkg" ]; do
        [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue

        case "$pkg" in
            python-telegram-bot*) module="telegram" module="telegram.ext" ;;
            Pillow*) module="PIL" ;;
            *) module="$pkg" ;;
        esac

        HIDDEN_IMPORTS+=" --hidden-import=$module"
    done < "$REQUIREMENTS_FILE"
fi

echo "Hidden imports détectés: $HIDDEN_IMPORTS"

pyinstaller \
  --name "$APP_NAME" \
  --windowed \
  --onefile \
  --icon="$ICON_FILE" \
  --add-data "macmenuqbt/icon/*:macmenuqbt/icon" \
  $HIDDEN_IMPORTS "$MAIN_SCRIPT" -y

SPEC_FILE="${APP_NAME}.spec"

if [ ! -f "$SPEC_FILE" ]; then
    echo "Erreur : $SPEC_FILE n'existe pas"
    exit 1
fi

perl -0777 -i.bak -pe 's/(app = BUNDLE\([^\)]*)\)/$1    info_plist={\n        '\''LSUIElement'\'' : True\n    }\n)/s' "$SPEC_FILE"

echo "$SPEC_FILE modifié, info_plist ajouté."

pyinstaller "$SPEC_FILE" -y

echo "Build terminé : dist/$APP_NAME.app"
