#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys
import time
import soundfile as sf
import subprocess

def test():
    print("==================================================")
    print("   TESTE ACÚSTICO KOKORO-82M (VOZ BRASILEIRA DORA)")
    print("==================================================")
    import kokoro_onnx

    model_dir = os.path.expanduser("~/.kokoro")
    model_path = os.path.join(model_dir, "kokoro-v1.0.onnx")
    voices_path = os.path.join(model_dir, "voices-v1.0.bin")

    if not os.path.exists(model_path):
        model_path = "/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx"
    if not os.path.exists(voices_path):
        voices_path = "/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"

    print(f"• Modelo: {model_path}")
    print(f"• Vozes:  {voices_path}")
    
    t0 = time.time()
    kokoro = kokoro_onnx.Kokoro(model_path=model_path, voices_path=voices_path)
    print(f"• Inicializado em: {time.time()-t0:.2f}s")

    frase = "Olá! Eu sou a Dora, voz feminina brasileira rodando com inteligência artificial cem por cento local no seu Termux!"
    print(f"\nSintetizando: \"{frase}\"...")

    t1 = time.time()
    samples, sr = kokoro.create(frase, voice="pf_dora", speed=1.0, lang="pt-br")
    dt = time.time() - t1
    dur = len(samples) / sr
    print(f"• Duração: {dur:.2f}s")
    print(f"• Tempo de geração: {dt:.2f}s")
    print(f"• Frequência: {sr} Hz (Studio Quality)")

    out = "/sdcard/Download/teste_dora_termux.wav"
    sf.write(out, samples, sr)
    print(f"• Áudio gravado em: {out}")
    print("\nTocando áudio no alto-falante...")
    subprocess.run(["termux-media-player", "play", out])

if __name__ == "__main__":
    test()
