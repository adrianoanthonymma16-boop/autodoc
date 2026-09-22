#!/bin/bash
# Instalador de Dependências - AutoDoc

echo "=========================================="
echo "  Instalando dependências do AutoDoc"
echo "=========================================="

# Detecta a distribuição
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Erro: Não foi possível detectar o sistema"
    exit 1
fi

echo "Sistema detectado: $OS"

# Instala dependências do sistema
case $OS in
    ubuntu|debian)
        echo "Instalando pacotes para Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
        ;;
    *)
        echo "Distribuição não suportada automaticamente."
        echo "Instale manualmente: python3, pip, tk, tesseract, zenity, makeself"
        ;;
esac

# Instala dependências Python e valida cada import (fail-fast)
echo "Instalando dependências Python..."
for dep in "Pillow:PIL" "opencv-python:cv2" "pytesseract:pytesseract" "pypdfium2:pypdfium2" "python-docx:docx" "lxml:lxml" "ttkbootstrap:ttkbootstrap" "customtkinter:customtkinter"; do
    pkg="${dep%%:*}"; mod="${dep##*:}"
    if python3 -c "import $mod" 2>/dev/null; then
        echo "OK: $mod já instalado."
        continue
    fi
    echo "Instalando $pkg..."
    pip3 install --break-system-packages "$pkg" || { echo "ERRO: falha ao instalar $pkg"; exit 1; }
    python3 -c "import $mod" 2>/dev/null || { echo "ERRO: $pkg instalado mas não importável ($mod)"; exit 1; }
    echo "OK: $mod instalado."
done

echo "=========================================="
echo "  Instalação concluída!"
echo "  Execute: python3 run.py"
echo "=========================================="
