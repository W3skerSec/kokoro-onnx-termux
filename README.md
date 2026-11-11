# Kokoro-82M ONNX para Android (Termux) 🇧🇷📱

Port oficial, corrigido e aprimorado do motor de síntese de voz neural **Kokoro-82M (StyleTTS2)** rodando **100% offline e localmente** no Termux (Android ARM64), com suporte completo à voz feminina brasileira **Dora (`pf_dora`)**, vozes masculinas (`pm_alex`, `pm_santa`), criação e desacoplamento de vozes personalizadas e pipeline de **Masterização de Estúdio (nível ElevenLabs)**.

---

## ⚡ Por que este Port foi Necessário? (Engenharia Reversa & Patches)

Ao tentar rodar o `kokoro-onnx` padrão no Termux / Android, múltiplos erros críticos de arquitetura impedem a execução:

1. **Incompatibilidade da Bionic libc com `dlinfo`**: O Android não implementa a função `dlinfo` presente na glibc GNU, causando crash imediato no carregador de bibliotecas do `phonemizer`.
2. **Crash de Binários Incompatíveis (`bad ELF magic`)**: O pacote `espeakng_loader` tenta carregar arquivos `.dylib` de macOS ou `.so` de x86_64. Nosso patch força o uso direto do binário nativo `libespeak-ng.so` compilado para ARM64 no próprio Termux.
3. **Avisos de Plataforma do ONNX Runtime**: Patcheado o arquivo `onnxruntime_validation.py` para reconhecer Android nativamente sem poluir o console com warnings.
4. **Dependência Oculta de Compilação Rust (`maturin` / `segments`)**: O backend padrão do phonemizer tenta compilar pacotes em Rust por mais de 20 minutos no celular. Patcheamos a importação para ser modular e tolerante a falhas.
5. **Restrição de Segurança do NumPy 2.x**: No Python moderno (3.14+), o `np.load` bloqueia arquivos binários com pickle sem o parâmetro explícito `allow_pickle=True`.

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

---

## 🎛️ Pipeline de Masterização de Estúdio (ElevenLabs Quality)

O modelo Kokoro originalmente exporta áudio em 24.000 Hz sem compressão de broadcast. Para elevar o nível ao padrão **ElevenLabs**, incluímos o comando `kokoro-master` e a flag `--master` que processam o áudio através de um pipeline profissional de 7 estágios em 48.000 Hz:

- **Upsampling Sinc (48 kHz / SOXR)**: Restaura a fidelidade acústica.
- **High-pass 70-80 Hz**: Elimina ruídos de baixa frequência e rumble.
- **EQ Paramétrico Multibanda**: Corpo vocal quente (200-240 Hz), clareza de presença (3.4-4 kHz) e abertura de ar (9.5-11 kHz).
- **Exciter Harmônico Psicoacústico (`aexciter`)**: Gera sobretons harmônicos naturais na faixa de 7 kHz a 18 kHz, devolvendo o brilho de microfones condensadores caros.
- **Dynamic Crystalizer & Compressor**: Suaviza transientes e equilibra sílabas sussurradas e tônicas.
- **Normalização EBU R128 (`loudnorm`)**: Padrão de broadcast internacional (-16 LUFS, -1.5 TP).

### Como Usar:
```bash
# 1. Fala direta com qualidade ElevenLabs Studio
kokoro-speak "Olá! Agora minha voz possui clareza de estúdio profissional!" --master

# 2. Masterizar usando a ferramenta dedicada kokoro-master
kokoro-master "Olá! Testando masterização com preset de rádio." -p radio
```

---

## 🎭 Novas Vozes Neurais Criadas

Criamos vetores acústicos personalizados utilizando a técnica de **desacoplamento de tensores** (dimensões 0..127 para timbre e identidade vocal; dimensões 128..255 para prosódia e ritmo linguístico em português):

| Voz | Descrição | Como Usar |
|---|---|---|
| **`dj_cara`** | Voz da DJ Cara (Non-Stop-Pop FM do GTA V) com sotaque britânico pop e português BR fluente | `kokoro-speak "Aqui é a Cara na Non Stop Pop FM!" -v dj_cara -m -p radio` |
| **`anime_natural`** | Voz feminina de anime doce e fofa (seiyuu), sem sotaque forçado ou caricato | `kokoro-speak "Senpai, você demorou tanto!" -v anime_natural -m -p anime` |
| **`anime_kawaii`** | Voz delicada estilo anime com prosódia brasileira pura | `kokoro-speak "Muito obrigada por cuidar de mim!" -v anime_kawaii -m` |
| **`anime_tsundere`** | Voz de anime enérgica e com atitude | `kokoro-speak "Baka! Não pense que fiz isso por você!" -v anime_tsundere -m` |

---

## 🎭 Atuação Expressiva Humana (Dynamic Volume, Pausas e Ritmo)

Sistemas de TTS comuns soam robóticos porque mantêm volume fixo e pausas mecânicas constantes (~150ms). O módulo [`kokoro_actor.py`](file:///data/data/com.termux/files/home/kokoro-onnx-termux/kokoro_actor.py) introduz um **motor de atuação expressiva** que simula a fala de um ser humano real:

- **Variações Dinâmicas de Volume (Gain Curve)**: Frases afirmativas/exclamações recebem projeção vocal mais alta (+18%), enquanto reticências e comentários sarcásticos reduzem o volume (-12%), criando o efeito intimista de estúdio.
- **Modulação de Velocidade por Intenção**: Frases empolgadas aceleram sutilmente (1.07x), enquanto reflexões e ironias desaceleram (0.93x).
- **Pausas Respiratórias Naturais**:
  - `!` ➔ Pausa curta de fôlego enérgico (220ms).
  - `?` ➔ Pausa inquisitiva (320ms).
  - `...` ➔ Hesitação dramática / reflexiva humana (480ms).
  - `,` ➔ Separação natural de oração (180ms).
- **Tags de Controle Humano**:
  - `[sussurro]` ou `[whisper]` ➔ Volume mais baixo e cadência lenta.
  - `[energia]` ou `[energy]` ➔ Volume projetado e ritmo rápido.
  - `[pausa=0.5]` ➔ Pausa personalizada em segundos.

### Exemplo de Atuação:
```bash
kokoro-speak "Aqui é a Cara na Non Stop Pop FM! Vocês estão prontos para dançar? ... Eu espero que sim, porque em Los Santos... ninguém tem desculpa para ficar parado!" -v dj_cara -m -p radio
```

---

## 🧬 Criando Suas Próprias Vozes (`kokoro-blend`)

Você pode misturar qualquer combinação das 54 vozes nativas do Kokoro para criar novas identidades:

```bash
# Ver todos os presets disponíveis
kokoro-blend --list-presets

# Gerar uma voz customizada misturando timbres
kokoro-blend --timbre "jf_tebukuro:0.5,af_heart:0.5" --prosody "pf_dora" --name "minha_voz"
```

---

## 📖 Dicionário Fonético Inteligente & Auto-Aprendizado (`kokoro-dict`)

O Kokoro conta com um dicionário fonético integrado que traduz termos em inglês, gírias da cultura pop, games e tecnologia para a pronúncia correta no Brasil (ex: *Non Stop Pop FM* vira *nón stóp póp éfie-emi*, *Dj* vira *didjei*, *GTA V* vira *gêtêá cinco*, *Download* vira *daunlôudi*).

Além disso, o motor possui **detecção automática de palavras estrangeiras/desconhecidas**: sempre que você falar uma palavra fora do vocabulário, ela é automaticamente capturada para revisão!

### Comandos do Dicionário:
```bash
# 1. Listar todas as palavras e pronúncias cadastradas
kokoro-dict --list

# 2. Ver palavras que você falou e que o sistema detectou como pendentes de ajuste
kokoro-dict --pending

# 3. Adicionar ou corrigir manualmente uma palavra no seu dicionário
kokoro-dict --add "Palavra" "fonética"
# Exemplo: kokoro-dict --add "Cyberpunk" "saiberpânqui"

# 4. Gerar relatório formatado para enviar à IA/assistente com as palavras pendentes
kokoro-dict --instructions

# 5. Testar como uma frase será pronunciada
kokoro-dict --test "Aqui é a Dj Cara na Non Stop Pop FM!"
```

---

## 🗣️ Guia de Comandos do Terminal

### Síntese Simples:
```bash
kokoro-speak "Olá! Estou falando 100% offline direto do Termux!"
```

### Síntese com Masterização de Estúdio:
```bash
kokoro-speak "Áudio com masterização e voz da Dora." -v pf_dora -m
```

### Voz da DJ do GTA V:
```bash
kokoro-speak "Você está curtindo Non-Stop-Pop FM!" -v dj_cara -m -p radio
```

### Listar Vozes:
```bash
kokoro-speak --list-voices
```

---

## 🇧🇷 Vozes Nativas do Banco Suportadas

| ID da Voz | Gênero | Descrição |
|---|---|---|
| **`pf_dora`** | 🚺 Feminino | Jovem, suave, entonação conversacional de estúdio (24.000 Hz) |
| **`pm_alex`** | 🚹 Masculino | Tom firme e claro |
| **`pm_santa`** | 🚹 Masculino | Tom encorpado e grave |
| **`bf_emma`**, **`bf_alice`** | 🚺 Britânico | Vozes britânicas ideais para blends de rádio |
| **`jf_tebukuro`**, **`jf_gongitsune`** | 🚺 Japonês | Vozes seiyuu ideais para blends de anime |

---

## 🛡️ Licença
Distribuído sob a licença Apache 2.0. Baseado no modelo Kokoro-82M de hexgrad e kokoro-onnx de thewh1teagle.
