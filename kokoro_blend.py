#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import warnings
import logging
import argparse
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("kokoro_onnx").setLevel(logging.ERROR)

import kokoro_onnx

HALF = 128  # 0..128: Timbre/Identidade vocal | 128..256: Prosódia/Ritmo linguístico

def parse_voice_spec(kokoro, spec_str):
    # Formato: "voz1:peso1,voz2:peso2" ou apenas "voz1"
    parts = spec_str.split(",")
    total_weight = 0.0
    accum = np.zeros((510, 1, 256), dtype=np.float32)
    for p in parts:
        if ":" in p:
            vname, weight_s = p.split(":")
            w = float(weight_s)
        else:
            vname = p
            w = 1.0
        vstyle = kokoro.get_voice_style(vname.strip())
        accum += w * vstyle
        total_weight += w
    if total_weight > 0:
        accum /= total_weight
    return accum

def main():
    parser = argparse.ArgumentParser(description="Kokoro Voice Blender: Crie vozes neurais personalizadas com desacoplamento de Timbre e Prosódia")
    parser.add_argument("--timbre", required=True, help="Voz(es) para a textura/timbre (ex: jf_tebukuro:0.7,af_bella:0.3)")
    parser.add_argument("--prosody", default="pf_dora", help="Voz para a prosódia/ritmo (padrão: pf_dora [pt-BR nativo])")
    parser.add_argument("--name", required=True, help="Nome para salvar a nova voz (ex: anime_waifu)")
    parser.add_argument("--test-text", default="Olá! Eu sou uma nova voz personalizada criada com desacoplamento neural!", help="Texto para teste acústico")
    parser.add_argument("--play", action="store_true", default=True, help="Tocar áudio de teste")
    
    args = parser.parse_args()

    model_dir = os.path.expanduser("~/.kokoro")
    fp32_model = "/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx"
    voices_path = "/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"

    kokoro = kokoro_onnx.Kokoro(model_path=fp32_model, voices_path=voices_path)

    print(f"🧬 Extraindo componentes acústicos...")
    timbre_tensor = parse_voice_spec(kokoro, args.timbre)
    prosody_tensor = parse_voice_spec(kokoro, args.prosody)

    # Monta a nova voz desacoplada
    nova_voz = np.copy(prosody_tensor)
    nova_voz[:, :, :HALF] = timbre_tensor[:, :, :HALF]
    nova_voz[:, :, HALF:] = prosody_tensor[:, :, HALF:]

    # Salva no diretório de vozes personalizadas
    custom_dir = os.path.join(model_dir, "custom_voices")
    os.makedirs(custom_dir, exist_ok=True)
    out_path = os.path.join(custom_dir, f"{args.name}.npy")
    np.save(out_path, nova_voz)
    print(f"✨ Nova voz salva com sucesso em: {out_path}")

    # Gera áudio de teste
    import soundfile as sf
    import subprocess
    print(f"🎙️ Sintetizando áudio de demonstração com '{args.name}'...")
    samples, sr = kokoro.create(args.test_text, voice=nova_voz, speed=1.05, lang="pt-br")
    test_out = f"/sdcard/Download/teste_{args.name}.wav"
    sf.write(test_out, samples, sr)
    print(f"💾 Áudio de teste salvo em: {test_out}")

    if args.play:
        print("🔊 Reproduzindo no alto-falante...")
        subprocess.run(["termux-media-player", "play", test_out])

if __name__ == "__main__":
    main()
