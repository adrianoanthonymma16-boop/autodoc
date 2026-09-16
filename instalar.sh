#!/usr/bin/env bash
# =============================================================================
# AutoDoc 4.0 Premium — Instalador
# =============================================================================
set -e
APP_DIR="$(dirname "$(realpath "$0")")"
APP_NAME="AutoDoc"
VERSAO=$(grep -oP 'VERSAO = "\K[^"]+' "$APP_DIR/src/config.py" || echo "4.0")

echo "== AutoDoc v$VERSAO — Instalando =="

# dependências pip (sem sudo, user)
echo "[1/4] Verificando dependências..."
python3 -m pip install --user --quiet customtkinter pillow opencv-python pytesseract pypdfium2 python-docx 2>&1 | tail -n 5 || true
# heic opcional
python3 -m pip install --user --quiet pyheif 2>&1 | tail -n 2 || echo "pyheif opcional falhou (ok)"

# permissões
chmod +x "$APP_DIR/run_ctk.py" "$APP_DIR/iniciar_ctk.sh" "$APP_DIR/desinstalar_ctk.sh" "$APP_DIR/instalar.sh" 2>/dev/null || true

# desktop entry premium
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/autodoc-ctk.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AutoDoc
Comment=AutoDoc v$VERSAO - Premium Modular | Preenche ODT/DOCX com OCR
Exec=bash "$APP_DIR/iniciar_ctk.sh"
Icon=$APP_DIR/icon.png
Terminal=false
Categories=Office;Utility;
StartupNotify=true
Keywords=autodoc;ocr;docx;odt;documentos;
EOF
chmod +x "$DESKTOP_DIR/autodoc-ctk.desktop"

# remove entrada obsoleta
if [ -f "$DESKTOP_DIR/autodoc.desktop" ]; then
  rm -f "$DESKTOP_DIR/autodoc.desktop"
  echo "Entrada obsoleta autodoc.desktop removida"
fi

# atalho na área de trabalho (se existir)
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESK" ]; then
  cp "$DESKTOP_DIR/autodoc-ctk.desktop" "$DESK/autodoc-ctk.desktop" 2>/dev/null || true
  chmod +x "$DESK/autodoc-ctk.desktop" 2>/dev/null || true
fi

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "✅ Instalado! v$VERSAO Premium"
echo "   Exec: $APP_DIR/iniciar_ctk.sh"
echo "   Desktop: $DESKTOP_DIR/autodoc-ctk.desktop"
echo "   Testes: python3 /tmp/test_autodoc.py"
