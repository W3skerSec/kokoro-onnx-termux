#!/data/data/com.termux/files/usr/bin/python3
"""
Kokoro Studio Mastering Pipeline (ElevenLabs-Level Audio Quality)
Aplica processamento de áudio profissional (EQ multibanda, exciter harmônico psicoacústico,
compressão dinâmica e normalização EBU R128) via ffmpeg no Android Termux.
"""

import os
import sys
import argparse
import subprocess
import tempfile
import time

PRESETS = {
    "studio": (
        "aresample=48000:resampler=soxr,"
        "highpass=f=70,"
        "equalizer=f=200:t=o:w=1.2:g=2.5,"
        "equalizer=f=3400:t=o:w=1.5:g=2.0,"
        "equalizer=f=9500:t=o:w=1.5:g=1.8,"
        "aexciter=level_in=1:level_out=1:amount=1.3:drive=1.8:freq=7000:ceil=17000,"
        "crystalizer=i=1.3,"
        "compand=attacks=0.015:decays=0.08:points=-80/-80|-45/-38|-27/-18|-15/-11|-5/-3|0/0:soft-knee=6:gain=1.8,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    ),
    "radio": (
        "aresample=48000:resampler=soxr,"
        "highpass=f=80,"
        "equalizer=f=220:t=o:w=1.2:g=2.0,"
        "equalizer=f=3800:t=o:w=1.4:g=3.0,"
        "equalizer=f=10000:t=o:w=1.5:g=2.0,"
        "aexciter=level_in=1:level_out=1:amount=1.5:drive=2.2:freq=6500:ceil=18000,"
        "crystalizer=i=1.4,"
        "compand=attacks=0.01:decays=0.06:points=-80/-80|-45/-36|-24/-15|-12/-8|-4/-2|0/0:soft-knee=6:gain=2.5,"
        "loudnorm=I=-14:TP=-1.0:LRA=7"
    ),
    "anime": (
        "rubberband=pitch=1.10:formant=shifted,"
        "aresample=48000:resampler=soxr,"
        "highpass=f=80,"
        "equalizer=f=240:t=o:w=1.0:g=1.5,"
        "equalizer=f=4000:t=o:w=1.5:g=2.5,"
        "equalizer=f=11000:t=o:w=1.5:g=2.0,"
        "aexciter=level_in=1:level_out=1:amount=1.6:drive=1.5:freq=7000:ceil=18000,"
        "crystalizer=i=1.2,"
        "compand=attacks=0.015:decays=0.08:points=-80/-80|-45/-38|-27/-18|-15/-11|-5/-3|0/0:soft-knee=6:gain=1.8,"
        "loudnorm=I=-16:TP=-1.5:LRA=8"
    ),
    "clean": (
        "aresample=48000:resampler=soxr,"
        "highpass=f=60,"
        "loudnorm=I=-16:TP=-1.5:LRA=10"
    )
}

def master_audio(input_wav: str, output_wav: str, preset: str = "studio") -> bool:
    """Aplica o filtro ffmpeg correspondente ao preset escolhido."""
    if preset not in PRESETS:
        preset = "studio"
    
    filter_chain = PRESETS[preset]
    cmd = [
        "ffmpeg", "-y", "-i", input_wav,
        "-af", filter_chain,
        "-ar", "48000",
        output_wav
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return res.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Kokoro Studio Mastering (ElevenLabs Quality)")
    parser.add_argument("text", nargs="?", default="", help="Texto para sintetizar e masterizar")
    parser.add_argument("-i", "--input", help="Arquivo WAV bruto para masterizar diretamente")
    parser.add_argument("-o", "--output", default="/sdcard/Download/fala_mastered.wav", help="Arquivo WAV final")
    parser.add_argument("-v", "--voice", default="pf_dora", help="Voz (pf_dora, dj_cara, anime_natural, etc)")
    parser.add_argument("-p", "--preset", choices=list(PRESETS.keys()), default="studio", help="Preset de masterização")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="Velocidade da fala")
    parser.add_argument("--no-play", action="store_true", help="Não tocar no alto-falante")
    
    args = parser.parse_args()

    # Modo 1: Apenas pós-processar arquivo de entrada existente
    if args.input:
        if not os.path.exists(args.input):
            print(f"Erro: Arquivo '{args.input}' não encontrado.")
            sys.exit(1)
        print(f"🎛️  [Kokoro Master] Masterizando '{args.input}' com preset '{args.preset}'...")
        t0 = time.time()
        ok = master_audio(args.input, args.output, preset=args.preset)
        if ok:
            print(f"✅ Concluído em {time.time()-t0:.2f}s! Salvo em: {args.output}")
            if not args.no_play:
                subprocess.run(["termux-media-player", "play", args.output], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print("❌ Erro ao executar masterização via ffmpeg.")
        return

    # Modo 2: Sintetizar texto e masterizar
    text = args.text.strip()
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Erro: Nenhum texto informado.")
            print('Exemplo: kokoro-master "Olá, agora estou em nível ElevenLabs!" -p studio')
            sys.exit(1)

    # Sintetizar para arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        raw_path = tmp.name

    try:
        # Se voz for dj_cara e preset for studio, sugerir preset radio
        preset = args.preset
        if args.voice == "dj_cara" and preset == "studio":
            preset = "radio"
        elif args.voice.startswith("anime") and preset == "studio":
            preset = "anime"

        print(f"🎙️  [1/2] Sintetizando com voz '{args.voice}'...")
        synth_cmd = [
            "kokoro-speak", text,
            "-v", args.voice,
            "-s", str(args.speed),
            "-o", raw_path,
            "--no-play"
        ]
        res = subprocess.run(synth_cmd)
        if res.returncode != 0:
            print("❌ Falha na síntese do áudio.")
            return

        print(f"🎛️  [2/2] Aplicando Masterização Studio de Alta Definição (Preset: {preset})...")
        t0 = time.time()
        ok = master_audio(raw_path, args.output, preset=preset)
        if ok:
            print(f"✨ [ElevenLabs-Grade] Áudio masterizado com sucesso em {time.time()-t0:.2f}s!")
            print(f"📁 Salvo em: {args.output}")
            if not args.no_play:
                print("🔊 Tocando no alto-falante...")
                subprocess.run(["termux-media-player", "play", args.output], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print("❌ Falha na etapa de masterização.")
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)

if __name__ == "__main__":
    main()
