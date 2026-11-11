#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "============================================================"
echo "   KOKORO-82M ONNX PARA TERMUX (ANDROID ARM64)"
echo "   Instalador Oficial com Correções Android Bionic / pt-BR"
echo "============================================================"

# 1. Dependências do Sistema Termux
echo "[1/5] Instalando dependências nativas do Termux..."
pkg update -y
pkg install -y python python-onnxruntime onnxruntime espeak ffmpeg termux-api

# 2. Dependências Python
echo "[2/5] Instalando pacotes Python necessários..."
pip install --upgrade pip
pip install soundfile colorlog phonemizer-fork kokoro-onnx --no-deps

# 3. Aplicar Patches para Android/Bionic e NumPy 2.x
echo "[3/5] Aplicando patches de compatibilidade Android Bionic / NumPy 2.x..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/patches/apply_patches.py"

# 4. Baixar Modelos Kokoro-82M e Vozes
MODEL_DIR="$HOME/.kokoro"
mkdir -p "$MODEL_DIR/custom_voices"

if [ ! -f "$MODEL_DIR/kokoro-v1.0.onnx" ]; then
    echo "[4/5] Baixando modelo neural de estúdio Kokoro-v1.0 (FP32 310MB - Áudio Cristalino)..."
    curl -L -o "$MODEL_DIR/kokoro-v1.0.onnx" \
        https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
fi

if [ ! -f "$MODEL_DIR/voices-v1.0.bin" ]; then
    echo "[4/5] Baixando banco de vozes neurais (voices-v1.0.bin)..."
    curl -L -o "$MODEL_DIR/voices-v1.0.bin" \
        https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
fi

# 5. Criar atalhos globais
echo "[5/5] Instalando comandos globais 'kokoro-speak' e 'kokoro-blend'..."
cp "$SCRIPT_DIR/kokoro_speak.py" "$PREFIX/bin/kokoro-speak"
cp "$SCRIPT_DIR/kokoro_blend.py" "$PREFIX/bin/kokoro-blend"
chmod +x "$PREFIX/bin/kokoro-speak" "$PREFIX/bin/kokoro-blend"

echo "============================================================"
echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "============================================================"
echo "Para testar, execute:"
echo '  kokoro-speak "Olá, eu sou a Dora, sua assistente virtual brasileira!"'
echo ""
echo "Para criar sua própria voz customizada (desacoplada):"
echo '  kokoro-blend --timbre "jf_tebukuro:0.6,af_heart:0.4" --prosody "pf_dora" --name "minha_voz"'
echo "============================================================"
