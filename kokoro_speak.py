#!/usr/bin/env python3
import os
import sys
import argparse
import time
import soundfile as sf
import subprocess

MODEL_DIR = os.path.expanduser("~/.kokoro")
DEFAULT_MODEL = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
DEFAULT_VOICES = os.path.join(MODEL_DIR, "voices-v1.0.bin")

def main():
    parser = argparse.ArgumentParser(description="Kokoro-82M TTS Local para Termux (Android)")
    parser.add_argument("text", nargs="?", default="", help="Texto a ser sintetizado")
    parser.add_argument("-v", "--voice", default="pf_dora", help="Voz (padrão: pf_dora [feminina brasileira])")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="Velocidade da fala (padrão: 1.0)")
    parser.add_argument("-l", "--lang", default="pt-br", help="Idioma (padrão: pt-br)")
    parser.add_argument("-o", "--output", default="/sdcard/Download/fala_kokoro.wav", help="Arquivo de saída WAV")
    parser.add_argument("--play", action="store_true", default=True, help="Tocar áudio automaticamente no alto-falante")
    parser.add_argument("--no-play", dest="play", action="store_false", help="Não tocar áudio")
    parser.add_argument("--list-voices", action="store_true", help="Listar vozes disponíveis")
    
    args = parser.parse_args()

    # Fallback to local files if ~/.kokoro not populated yet
    model_path = DEFAULT_MODEL
    voices_path = DEFAULT_VOICES
    if not os.path.exists(model_path):
        alt_model = "/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx"
        if os.path.exists(alt_model):
            model_path = alt_model
    if not os.path.exists(voices_path):
        alt_voices = "/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"
        if os.path.exists(alt_voices):
            voices_path = alt_voices

    import kokoro_onnx
    kokoro = kokoro_onnx.Kokoro(model_path=model_path, voices_path=voices_path)

    if args.list_voices:
        voices = kokoro.get_voices()
        print("="*50)
        print("VOZES DISPONÍVEIS NO KOKORO-82M:")
        print("="*50)
        pt_voices = [v for v in voices if v.startswith("p")]
        print(f"🇧🇷 Português do Brasil: {pt_voices}")
        print(f"Total de vozes suportadas: {len(voices)}")
        return

    text = args.text.strip()
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Erro: Nenhum texto informado. Exemplo:")
            print('  kokoro-speak "Olá, tudo bem?" -v pf_dora')
            return

    print(f"🤖 [Kokoro TTS] Sintetizando com a voz '{args.voice}' ({args.lang})...")
    t0 = time.time()
    samples, sr = kokoro.create(text, voice=args.voice, speed=args.speed, lang=args.lang)
    dt = time.time() - t0
    dur = len(samples) / sr
    speedup = dur / dt if dt > 0 else 0
    print(f" -> Áudio de {dur:.2f}s gerado em {dt:.2f}s ({speedup:.1f}x tempo real) a {sr}Hz!")

    sf.write(args.output, samples, sr)
    print(f" -> Salvo em: {args.output}")

    if args.play:
        print("🔊 Tocando no alto-falante...")
        subprocess.run(["termux-media-player", "play", args.output], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
