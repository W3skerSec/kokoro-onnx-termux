# Kokoro-82M ONNX para Android (Termux) 🇧🇷📱

Port oficial e corrigido do motor de síntese de voz neural **Kokoro-82M (StyleTTS2)** rodando **100% offline e localmente** no Termux (Android ARM64), com suporte completo à voz feminina brasileira **Dora (`pf_dora`)** e vozes masculinas (`pm_alex`, `pm_santa`), respeitando pausas, vírgulas, perguntas e entonação natural sem necessidade de conexões com a nuvem ou APIs pagas.

---

## ⚡ Por que este Port foi Necessário?

Ao tentar rodar o `kokoro-onnx` padrão no Termux / Android, múltiplos erros críticos de arquitetura impedem a execução:

1. **Incompatibilidade da Bionic libc com `dlinfo`**: O Android não implementa a função `dlinfo` presente na glibc GNU, causando crash imediato no carregador de bibliotecas do `phonemizer`.
2. **Crash de Binários Incompatíveis (`bad ELF magic`)**: O pacote `espeakng_loader` tenta carregar arquivos `.dylib` de macOS ou `.so` de x86_64, quebrando a execução no ARM64 do Android.
3. **Dependência Oculta de Compilação Rust (`maturin` / `segments`)**: O backend padrão do phonemizer tenta compilar pacotes em Rust por mais de 20 minutos no celular.
4. **Restrição de Segurança do NumPy 2.x**: No Python moderno (3.14+), o `np.load` bloqueia arquivos binários com pickle sem o parâmetro explícito `allow_pickle=True`.

**Este repositório fornece todos os patches automáticos e resolve a cadeia de dependências para utilizar o motor nativo `espeak-ng` e o runtime otimizado `onnxruntime` aarch64 do próprio Termux.**

---

## 🚀 Instalação Rápida (1 Comando)

No seu Termux, execute:

```bash
pkg install -y git
git clone https://github.com/W3skerSec/kokoro-onnx-termux.git
cd kokoro-onnx-termux
chmod +x install.sh
./install.sh
```

O script cuidará de:
- Instalar dependências nativas (`onnxruntime`, `python-onnxruntime`, `espeak`, `ffmpeg`).
- Aplicar os patches para o Android Bionic e NumPy 2.x.
- Baixar os pesos neurais do Kokoro-82M e o banco de vozes.
- Registrar o comando global `kokoro-speak` no seu sistema.

---

## 🗣️ Como Usar via Terminal

Após a instalação, o comando `kokoro-speak` estará disponível globalmente:

### 1. Falar uma frase com voz brasileira:
```bash
kokoro-speak "Olá! Tudo bem com você? Estou falando 100% offline direto do seu celular!"
```

### 2. Escolher outra voz ou velocidade:
```bash
kokoro-speak "Esta é uma fala com velocidade aumentada." -v pf_dora -s 1.2
```

### 3. Listar todas as 54 vozes disponíveis:
```bash
kokoro-speak --list-voices
```

### 4. Usar em Pipes / Scripts:
```bash
echo "Processamento concluído com sucesso." | kokoro-speak
```

---

## 🐍 Como Usar em Scripts Python

```python
import kokoro_onnx
import soundfile as sf
import subprocess

# Inicializa o modelo
kokoro = kokoro_onnx.Kokoro(
    model_path="/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx",
    voices_path="/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"
)

# Sintetiza com a voz feminina brasileira pf_dora
samples, sr = kokoro.create(
    "Olá! Esta é uma demonstração de síntese neural local.",
    voice="pf_dora",
    speed=1.0,
    lang="pt-br"
)

# Salva o arquivo de áudio
sf.write("/sdcard/Download/fala.wav", samples, sr)

# Reproduz no alto-falante do celular
subprocess.run(["termux-media-player", "play", "/sdcard/Download/fala.wav"])
```

---

## 🇧🇷 Vozes em Português do Brasil Suportadas

| ID da Voz | Gênero | Qualidade / Timbre |
|---|---|---|
| **`pf_dora`** | 🚺 Feminino | Jovem, suave, entonação conversacional de estúdio (24.000 Hz) |
| **`pm_alex`** | 🚹 Masculino | Tom firme e claro |
| **`pm_santa`** | 🚹 Masculino | Tom mais encorpado e grave |

---

## 🛡️ Licença
Distribuído sob a licença Apache 2.0. Baseado no modelo open-weights Kokoro-82M de hexgrad e kokoro-onnx de thewh1teagle.
