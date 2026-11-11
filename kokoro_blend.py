#!/data/data/com.termux/files/usr/bin/python3
"""
Kokoro Voice Blender: Criação de vozes personalizadas com desacoplamento neural
(Dims 0..127: Timbre vocal | Dims 128..255: Prosódia/Entonação linguística)
"""

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

VOICE_PRESETS = {
    "cara_jdm": {
        "timbre": "bf_isabella:0.35,bf_emma:0.30,bm_fable:0.20,af_heart:0.15",
        "prosody": "pf_dora:0.75,bf_isabella:0.25",
        "desc": "DJ Cara (Underground JDM / Neon Noir) - Voz aveludada, confiante, provocativa e rouca",
        "test": "Luzes de neon, asfalto molhado... relaxa, chefe. Essa próxima faixa de Dark Phonk é simplesmente genial."
    },
    "dj_cara": {
        "timbre": "bf_emma:0.45,bf_alice:0.35,bf_lily:0.20",
        "prosody": "pf_dora:0.85,bf_emma:0.15",
        "desc": "DJ Cara (Non-Stop-Pop FM GTA V) - Sotaque britânico pop com português BR fluente",
        "test": "Aqui é a Cara na Non Stop Pop FM! Próxima faixa exclusiva na área, Los Santos não dorme essa noite!"
    },
    "anime_natural": {
        "timbre": "jf_tebukuro:0.40,af_heart:0.35,pf_dora:0.25",
        "prosody": "pf_dora:0.90,jf_gongitsune:0.10",
        "desc": "Anime Seiyuu Natural - Timbre doce e fofo de anime sem caricatura forçada",
        "test": "Senpai, você demorou tanto! Eu estava te esperando para a gente treinar juntos hoje!"
    },
    "anime_kawaii": {
        "timbre": "jf_tebukuro:0.60,af_heart:0.40",
        "prosody": "pf_dora:0.95,jf_tebukuro:0.05",
        "desc": "Anime Kawaii - Timbre delicado com prosódia brasileira pura",
        "test": "Muito obrigada por cuidar de mim! Prometo dar o meu melhor hoje!"
    },
    "anime_tsundere": {
        "timbre": "jf_nezumi:0.50,af_bella:0.50",
        "prosody": "pf_dora:0.80,jf_nezumi:0.20",
        "desc": "Anime Tsundere - Timbre enérgico com atitude",
        "test": "Baka! Não pense que eu fiz isso porque gosto de você, ouviu bem?!"
    }
}

def parse_voice_spec(kokoro, spec_str):
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

def build_voice(kokoro, timbre_spec, prosody_spec):
    timbre_tensor = parse_voice_spec(kokoro, timbre_spec)
    prosody_tensor = parse_voice_spec(kokoro, prosody_spec)
    nova_voz = np.copy(prosody_tensor)
    nova_voz[:, :, :HALF] = timbre_tensor[:, :, :HALF]
    nova_voz[:, :, HALF:] = prosody_tensor[:, :, HALF:]
    return nova_voz

def main():
    parser = argparse.ArgumentParser(description="Kokoro Voice Blender: Crie vozes personalizadas com desacoplamento neural")
    parser.add_argument("--preset", choices=list(VOICE_PRESETS.keys()), help="Criar voz a partir de preset consagrado")
    parser.add_argument("--list-presets", action="store_true", help="Listar todos os presets disponíveis")
    parser.add_argument("--timbre", help="Voz(es) para textura/timbre (ex: jf_tebukuro:0.7,af_bella:0.3)")
    parser.add_argument("--prosody", default="pf_dora", help="Voz para prosódia/ritmo (padrão: pf_dora)")
    parser.add_argument("--name", help="Nome do arquivo para salvar (.npy)")
    parser.add_argument("--test-text", help="Texto personalizado para teste")
    parser.add_argument("--no-play", action="store_true", help="Não tocar áudio de teste")
    
    args = parser.parse_args()

    if args.list_presets:
        print("="*60)
        print("PRESETS DE VOZES PRÉ-CONFIGURADAS:")
        print("="*60)
        for k, v in VOICE_PRESETS.items():
            print(f"🌟 {k.ljust(16)}: {v['desc']}")
        return

    model_dir = os.path.expanduser("~/.kokoro")
    fp32_model = "/data/data/com.termux/files/home/modelos_tts/kokoro/model.onnx"
    voices_path = "/data/data/com.termux/files/home/modelos_tts/kokoro/voices-v1.0.bin"

    kokoro = kokoro_onnx.Kokoro(model_path=fp32_model, voices_path=voices_path)

    if args.preset:
        p = VOICE_PRESETS[args.preset]
        name = args.name or args.preset
        timbre_spec = p["timbre"]
        prosody_spec = p["prosody"]
        test_text = args.test_text or p["test"]
        print(f"✨ Gerando preset '{args.preset}': {p['desc']}")
    else:
        if not args.timbre or not args.name:
            print("Erro: Informe --preset <nome> OU (--timbre <voz> e --name <nome>)")
            return
        name = args.name
        timbre_spec = args.timbre
        prosody_spec = args.prosody
        test_text = args.test_text or "Olá! Eu sou uma nova voz personalizada criada com desacoplamento neural!"

    print(f"🧬 Extraindo e desacoplando componentes acústicos...")
    nova_voz = build_voice(kokoro, timbre_spec, prosody_spec)

    custom_dir = os.path.join(model_dir, "custom_voices")
    os.makedirs(custom_dir, exist_ok=True)
    out_path = os.path.join(custom_dir, f"{name}.npy")
    np.save(out_path, nova_voz)
    print(f"💾 Nova voz salva com sucesso em: {out_path}")

    import soundfile as sf
    import subprocess
    print(f"🎙️ Sintetizando áudio de demonstração com '{name}'...")
    samples, sr = kokoro.create(test_text, voice=nova_voz, speed=1.05, lang="pt-br")
    test_out = f"/sdcard/Download/teste_{name}.wav"
    sf.write(test_out, samples, sr)
    print(f"📁 Áudio de teste salvo em: {test_out}")

    if not args.no_play:
        print("🔊 Reproduzindo no alto-falante...")
        subprocess.run(["termux-media-player", "play", test_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()
