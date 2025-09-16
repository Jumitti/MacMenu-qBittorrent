APP_PATH="dist/MMqBt.app"
DMG_NAME="MMqBt.dmg"
TEMP_DIR="temp_dmg"
VOLUME_NAME="MMqBt"

mkdir -p "$TEMP_DIR"

cp -R "$APP_PATH" "$TEMP_DIR/"
ln -s /Applications "$TEMP_DIR/Applications"

hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"

rm -rf "$TEMP_DIR"
