#!/bin/bash

# Build Script für Python zu Windows EXE
# Verwendung: ./build.sh [APP_NAME]
# Beispiel: ./build.sh "MeineTolle App"

# Standard App-Name falls keiner angegeben wird
DEFAULT_APP_NAME="Bestellungen"

# App-Name aus erstem Parameter oder Standard verwenden
APP_NAME="${1:-$DEFAULT_APP_NAME}"

echo "🔧 Baue Python Projekt zu Windows EXE..."
echo "📱 App-Name: $APP_NAME"

# Prüfe ob PyInstaller installiert ist
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller ist nicht installiert. Installiere es mit:"
    echo "pip install pyinstaller"
    exit 1
fi

# Prüfe ob main.py existiert
if [ ! -f "main.py" ]; then
    echo "❌ main.py nicht gefunden!"
    exit 1
fi

# Prüfe ob config.json existiert
if [ ! -f "config.json" ]; then
    echo "❌ config.json nicht gefunden!"
    exit 1
fi

# Erstelle dist und build Verzeichnisse falls sie nicht existieren
mkdir -p dist build

# Lösche alte Builds
echo "🧹 Lösche alte Builds..."
rm -rf dist/*
rm -rf build/*
rm -f *.spec

# Baue die EXE
echo "🏗️  Erstelle Windows EXE..."
pyinstaller \
    --onefile \
    --noconsole \
    --add-data "config.json:." \
    --name "$APP_NAME" \
    --clean \
    --noconfirm \
    main.py

# Prüfe ob Build erfolgreich war
if [ -f "dist/$APP_NAME.exe" ]; then
    echo "✅ Build erfolgreich!"
    echo "📁 EXE-Datei: $(pwd)/dist/$APP_NAME.exe"
    echo "📏 Dateigröße: $(du -h "dist/$APP_NAME.exe" | cut -f1)"

    # Zeige Inhalt des dist Ordners
    echo ""
    echo "📋 Inhalt des dist/ Ordners:"
    ls -lh dist/
else
    echo "❌ Build fehlgeschlagen!"
    echo "Prüfe die Ausgabe oben für Fehlermeldungen."
    exit 1
fi

echo ""
echo "🎉 Fertig! Du kannst die EXE-Datei jetzt auf Windows-Systemen ausführen."
