#!/usr/bin/env bash
# =============================================================================
# AutoDoc — Build do pacote .deb (PyInstaller + dpkg-deb)
#
# Uso:
#   ./packaging/build_deb.sh
#
# Requisitos: python3 com as dependências do app, PyInstaller e dpkg-deb.
# O runtime Python inteiro vai embutido; o Tesseract vem por Depends do apt.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
APP="autodoc-ctk"
DISPLAY_NAME="AutoDoc"
ARCH="${ARCH:-$(dpkg --print-architecture)}"
VERSION="$("$PYTHON" -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
MAINTAINER="Adriano Anthony <adrianoanthonymma16@gmail.com>"

BUILD="$ROOT/build"
PYI_DIST="$BUILD/pyinstaller"
PYI_WORK="$BUILD/pyinstaller-work"
STAGE="$BUILD/deb/${APP}_${VERSION}_${ARCH}"
OUT="$ROOT/dist/${APP}_${VERSION}_${ARCH}.deb"

echo "==> AutoDoc ${VERSION} (${ARCH})"

if ! command -v dpkg-deb >/dev/null; then
    echo "ERRO: dpkg-deb não encontrado." >&2
    exit 1
fi

if ! "$PYTHON" -c "import PyInstaller" >/dev/null 2>&1; then
    echo "ERRO: PyInstaller não encontrado no Python usado ($PYTHON)." >&2
    echo "Instale com: $PYTHON -m pip install pyinstaller" >&2
    exit 1
fi

echo "==> [1/4] Empacotando aplicação com PyInstaller"
rm -rf "$PYI_DIST" "$PYI_WORK" "$STAGE"
"$PYTHON" -m PyInstaller \
    --noconfirm --clean --onedir --windowed \
    --name "$DISPLAY_NAME" \
    --paths src \
    --add-data "$ROOT/assets:assets" \
    --add-data "$ROOT/icon.png:." \
    --hidden-import PIL._tkinter_finder \
    --collect-all customtkinter \
    --collect-all ttkbootstrap \
    --collect-all openpyxl \
    --collect-all pypdfium2 \
    --add-data "$ROOT/packaging/pyinstaller-docx-parts.keep:docx/parts" \
    --distpath "$PYI_DIST" \
    --workpath "$PYI_WORK" \
    --specpath "$BUILD" \
    run_ctk.py

echo "==> [2/4] Montando árvore Debian"
mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/opt/$APP" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps"

cp -a "$PYI_DIST/$DISPLAY_NAME/." "$STAGE/opt/$APP/"
cp "$ROOT/packaging/autodoc.desktop" "$STAGE/usr/share/applications/$APP.desktop"
cp "$ROOT/icon.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/$APP.png"
cp "$ROOT/LICENSE.txt" "$STAGE/opt/$APP/LICENSE.txt"

cat > "$STAGE/usr/bin/$APP" <<EOF
#!/bin/sh
exec /opt/$APP/$DISPLAY_NAME "\$@"
EOF
chmod 0755 "$STAGE/usr/bin/$APP"

echo "==> [3/4] Gerando metadados do pacote"
SIZE_KB="$(du -sk "$STAGE/opt/$APP" | cut -f1)"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: $APP
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $SIZE_KB
Depends: tesseract-ocr, tesseract-ocr-por
Recommends: fonts-inter, zenity
Homepage: https://github.com/adrianoanthonymma16-boop/autodoc
Description: Preenchimento automático de documentos ODT/DOCX com OCR
 AutoDoc preenche modelos ODT e DOCX a partir de documentos digitalizados,
 usando OCR offline (Tesseract). Inclui mapeamento visual de campos,
 biblioteca de modelos, validação de CPF/data/e-mail e histórico de geração.
 .
 O runtime Python é embutido no pacote; o Tesseract é instalado pelo apt.
EOF

cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
    command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
fi
exit 0
EOF

cat > "$STAGE/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
    command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
fi
exit 0
EOF

chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
find "$STAGE/opt/$APP" -type d -exec chmod 0755 {} +
find "$STAGE/opt/$APP" -type f -exec chmod 0644 {} +
chmod 0755 "$STAGE/opt/$APP/$DISPLAY_NAME"

echo "==> [4/4] Gerando o .deb"
mkdir -p "$ROOT/dist"
dpkg-deb --root-owner-group -Zxz --build "$STAGE" "$OUT" >/dev/null

echo ""
echo "Pacote gerado: $OUT"
echo "Tamanho: $(du -h "$OUT" | cut -f1)"
