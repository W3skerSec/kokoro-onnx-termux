#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import warnings
import logging
import numpy as np

# 1. Silenciar UserWarning do onnxruntime no Android
warnings.filterwarnings("ignore", category=UserWarning)

# 2. Configurar bibliotecas nativas do Termux antes de qualquer import
termux_lib = "/data/data/com.termux/files/usr/lib/libespeak-ng.so"
termux_data = "/data/data/com.termux/files/usr/share/espeak-ng-data"
if os.path.exists(termux_lib):
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = termux_lib
if os.path.exists(termux_data):
    os.environ["PHONEMIZER_ESPEAK_DATA_DIRECTORY"] = termux_data

# 3. Silenciar logs internos verbosos
logging.getLogger("kokoro_onnx").setLevel(logging.ERROR)

import argparse
import time
import soundfile as sf
import subprocess

MODEL_DIR = os.path.expanduser("~/.kokoro")
DEFAULT_FP32 = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
DEFAULT_INT8 = os.path.join(MODEL_DIR, "kokoro-v1.0.int8.onnx")
DEFAULT_VOICES = os.path.join(MODEL_DIR, "voices-v1.0.bin")
CUSTOM_DIR = os.path.join(MODEL_DIR, "custom_voices")

def get_best_model():
    alt_fp32 = "/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx"
    if os.path.exists(alt_fp32):
        return alt_fp32
    if os.path.exists(DEFAULT_FP32):
        return DEFAULT_FP32
    if os.path.exists(DEFAULT_INT8):
        return DEFAULT_INT8
    alt_int8 = "/data/data/com.termux/files/home/modelos_tts/kokoro/kokoro-v1.0.int8.onnx"
    if os.path.exists(alt_int8):
        return alt_int8
    return alt_fp32

def get_best_voices():
    alt_voices = "/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"
    if os.path.exists(alt_voices):
        return alt_voices
    if os.path.exists(DEFAULT_VOICES):
        return DEFAULT_VOICES
    return alt_voices

def resolve_voice(voice_arg):
    # 1. Direct .npy file path
    if voice_arg.endswith(".npy") and os.path.exists(voice_arg):
        return np.load(voice_arg)
    # 2. Check custom_voices directory
    custom_path = os.path.join(CUSTOM_DIR, f"{voice_arg}.npy")
    if os.path.exists(custom_path):
        return np.load(custom_path)
    # 3. Otherwise return string name for standard voices.bin lookup
    return voice_arg

def main():
    parser = argparse.ArgumentParser(description="Kokoro-82M TTS Local para Termux (Android)")
    parser.add_argument("text", nargs="?", default="", help="Texto a ser sintetizado")
    parser.add_argument("-v", "--voice", default="pf_dora", help="Voz padrão ou customizada (.npy ou nome)")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="Velocidade da fala (padrão: 1.0)")
    parser.add_argument("-l", "--lang", default="pt-br", help="Idioma (padrão: pt-br)")
    parser.add_argument("-o", "--output", default="/sdcard/Download/fala_kokoro.wav", help="Arquivo de saída WAV")
    parser.add_argument("--play", action="store_true", default=True, help="Tocar áudio automaticamente no alto-falante")
    parser.add_argument("--no-play", dest="play", action="store_false", help="Não tocar áudio")
    parser.add_argument("-m", "--master", action="store_true", help="Aplicar pós-processamento de estúdio (ElevenLabs Quality)")
    parser.add_argument("-p", "--preset", default="studio", choices=["studio", "radio", "anime", "clean"], help="Preset de masterização")
    parser.add_argument("--act", dest="act", action="store_true", default=None, help="Ativar atuação humana expressiva (volume e pausas dinâmicas)")
    parser.add_argument("--no-act", dest="act", action="store_false", help="Desativar atuação expressiva")
    parser.add_argument("--list-voices", action="store_true", help="Listar vozes disponíveis")
    
    args = parser.parse_args()

    model_path = get_best_model()
    voices_path = get_best_voices()

    import kokoro_onnx
    kokoro = kokoro_onnx.Kokoro(model_path=model_path, voices_path=voices_path)

    if args.list_voices:
        voices = kokoro.get_voices()
        print("="*50)
        print("VOZES DISPONÍVEIS NO KOKORO-82M:")
        print("="*50)
        pt_voices = [v for v in voices if v.startswith("p")]
        print(f"🇧🇷 Português do Brasil: {pt_voices}")
        
        # Check custom voices
        if os.path.exists(CUSTOM_DIR):
            custom_list = [f.replace(".npy", "") for f in os.listdir(CUSTOM_DIR) if f.endswith(".npy")]
            if custom_list:
                print(f"🎨 Vozes Personalizadas Customizadas: {custom_list}")
                
        print(f"Total de vozes padrão suportadas: {len(voices)}")
        return

    text = args.text.strip()
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Erro: Nenhum texto informado. Exemplo:")
            print('  kokoro-speak "Olá, tudo bem?" -v pf_dora')
            return

    resolved_voice = resolve_voice(args.voice)
    voice_name = args.voice if isinstance(resolved_voice, str) else f"custom({args.voice})"

    # Normalização fonética inteligente e captura de termos desconhecidos
    if args.lang.lower().startswith("pt"):
        try:
            import kokoro_phonetics
            text = kokoro_phonetics.normalize_text_ptbr(text)
        except Exception:
            pass

    # Determina se deve usar atuação expressiva humana
    should_act = args.act
    if should_act is None:
        # Ativa automaticamente para dj_cara ou se o texto contiver pontuações expressivas
        if "dj_cara" in str(voice_name) or any(c in text for c in ["!", "?", "..."]):
            should_act = True
        else:
            should_act = False

    mode_str = " (Atuação Expressiva Humana)" if should_act else ""
    print(f"🤖 [Kokoro TTS] Sintetizando com a voz '{voice_name}' ({args.lang}){mode_str}...")
    t0 = time.time()

    if should_act:
        try:
            import kokoro_actor
            samples, sr = kokoro_actor.synthesize_acting(kokoro, text, voice=resolved_voice, lang=args.lang)
        except Exception as e:
            # Fallback caso ocorra qualquer imprevisto
            samples, sr = kokoro.create(text, voice=resolved_voice, speed=args.speed, lang=args.lang)
    else:
        samples, sr = kokoro.create(text, voice=resolved_voice, speed=args.speed, lang=args.lang)

    dt = time.time() - t0
    dur = len(samples) / sr
    speedup = dur / dt if dt > 0 else 0
    print(f" -> Áudio de {dur:.2f}s gerado em {dt:.2f}s ({speedup:.1f}x tempo real) a {sr}Hz!")

    if args.master:
        import tempfile
        from kokoro_master import master_audio
        preset = args.preset
        if "dj_cara" in str(voice_name) and preset == "studio":
            preset = "radio"
        elif "anime" in str(voice_name) and preset == "studio":
            preset = "anime"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_raw = tmp.name
        try:
            sf.write(tmp_raw, samples, sr)
            print(f"🎛️  [Mastering Studio] Aplicando masterização ElevenLabs ({preset})...")
            master_audio(tmp_raw, args.output, preset=preset)
            print(f"✨ Salvo em estúdio: {args.output}")
        finally:
            if os.path.exists(tmp_raw):
                os.remove(tmp_raw)
    else:
        sf.write(args.output, samples, sr)
        print(f" -> Salvo em: {args.output}")

    if args.play:
        print("🔊 Tocando no alto-falante...")
        subprocess.run(["termux-media-player", "play", args.output], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
