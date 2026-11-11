#!/data/data/com.termux/files/usr/bin/python3
"""
Kokoro Actor Engine v2 - Atuação Humana e Prosódia Expressiva
- Parsing robusto de tags sem colisão de regex ([pausa=X], [rush], [tedio], etc)
- Cadência aveludada, magnética e sem pressa (0.80x a 0.95x)
- Pausas respiratórias e dramáticas generosas (0.25s a 0.80s)
- Crossfade suave de 20ms entre orações para evitar saltos ou cortes mecânicos
"""

import os
import sys
import re
import numpy as np
import kokoro_phonetics

SAMPLE_RATE = 24000

def parse_acting_beats(text: str) -> list[dict]:
    """
    Tokeniza o texto em beats de fala e pausas sem quebrar floats ou pontuações.
    """
    # 1. Extração segura de tags especiais [tag] ou [tag=valor]
    token_pattern = re.compile(
        r'\[(pausa|pause)=([0-9.]+)\]|'
        r'\[(rush|adrenalina|rapido)\]|'
        r'\[(tedio|ironia|sarcasmo)\]|'
        r'\[(analitica|foco|alerta)\]|'
        r'\[(direta|calma)\]|'
        r'\[(sussurro|whisper)\]|'
        r'\[(energia|energy)\]',
        re.IGNORECASE
    )

    # Divide o texto preservando as tags
    tokens = []
    last_idx = 0
    for match in token_pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            chunk = text[last_idx:start].strip()
            if chunk:
                tokens.append(("text", chunk))
        matched_str = match.group(0).lower()
        if "pausa=" in matched_str or "pause=" in matched_str:
            dur = float(match.group(2))
            tokens.append(("pause", dur))
        elif any(k in matched_str for k in ["rush", "adrenalina", "rapido"]):
            tokens.append(("mod", "rush"))
        elif any(k in matched_str for k in ["tedio", "ironia", "sarcasmo"]):
            tokens.append(("mod", "tedio"))
        elif any(k in matched_str for k in ["analitica", "foco", "alerta"]):
            tokens.append(("mod", "analitica"))
        elif any(k in matched_str for k in ["direta", "calma"]):
            tokens.append(("mod", "direta"))
        elif any(k in matched_str for k in ["sussurro", "whisper"]):
            tokens.append(("mod", "sussurro"))
        elif any(k in matched_str for k in ["energia", "energy"]):
            tokens.append(("mod", "energia"))
        last_idx = end

    if last_idx < len(text):
        chunk = text[last_idx:].strip()
        if chunk:
            tokens.append(("text", chunk))

    # 2. Converte tokens em beats oracionais
    beats = []
    current_mod = "normal"

    for t_type, t_val in tokens:
        if t_type == "pause":
            beats.append({"type": "pause", "duration": t_val})
        elif t_type == "mod":
            current_mod = t_val
        elif t_type == "text":
            # Divide orações por pontuação final (. ! ? … ou ...)
            clauses = re.split(r'([.!?…]+|\.\.\.)', t_val)
            for i in range(0, len(clauses) - 1, 2):
                c = clauses[i].strip()
                p = clauses[i+1].strip()
                if not c:
                    continue
                
                # Configuração de cadência aveludada e humana
                if current_mod == "rush":
                    speed = 0.96      # Ágil e enérgico, mas articulado e sem atropelar
                    vol = 1.15
                    pause_s = 0.28
                elif current_mod == "tedio":
                    speed = 0.82      # Tédio sofisticado, arrastado e irônico
                    vol = 0.85
                    pause_s = 0.65
                elif current_mod == "analitica":
                    speed = 0.86      # Preciso, pausado e cirúrgico
                    vol = 1.00
                    pause_s = 0.45
                elif current_mod == "direta":
                    speed = 0.88      # Confiante, aveludado e direto
                    vol = 1.05
                    pause_s = 0.55
                elif current_mod == "sussurro":
                    speed = 0.80
                    vol = 0.75
                    pause_s = 0.50
                elif current_mod == "energia":
                    speed = 0.98
                    vol = 1.20
                    pause_s = 0.30
                else:
                    # Modo normal: cadência baseada na pontuação
                    if '!' in p:
                        speed = 0.94
                        vol = 1.12
                        pause_s = 0.35
                    elif '?' in p:
                        speed = 0.88
                        vol = 1.02
                        pause_s = 0.45
                    elif '..' in p or '…' in p:
                        speed = 0.82    # Reticências: pausa dramática e reflexão lenta
                        vol = 0.85
                        pause_s = 0.70
                    else:
                        speed = 0.88    # Cadência relaxada padrão de rádio noturna
                        vol = 1.00
                        pause_s = 0.40

                beats.append({
                    "type": "speech",
                    "text": c + p,
                    "speed": speed,
                    "vol": vol,
                    "pause": pause_s
                })
                # Reseta o modificador após uma oração completa
                current_mod = "normal"

            if len(clauses) % 2 == 1 and clauses[-1].strip():
                c = clauses[-1].strip()
                beats.append({
                    "type": "speech",
                    "text": c + ".",
                    "speed": 0.88,
                    "vol": 1.00,
                    "pause": 0.45
                })

    return beats

def synthesize_acting(kokoro_engine, text: str, voice, lang: str = "pt-br") -> tuple[np.ndarray, int]:
    """
    Sintetiza cada beat com sua dinâmica e costura com pausas suaves.
    """
    beats = parse_acting_beats(text)
    audio_segments = []

    for beat in beats:
        if beat["type"] == "pause":
            pause_samples = int(SAMPLE_RATE * beat["duration"])
            audio_segments.append(np.zeros(pause_samples, dtype=np.float32))
            continue

        raw_text = beat["text"]
        if lang.lower().startswith("pt"):
            clean_text = kokoro_phonetics.normalize_text_ptbr(raw_text)
        else:
            clean_text = raw_text

        # Sintetiza com a velocidade deliberada e aveludada do beat
        samples, _ = kokoro_engine.create(clean_text, voice=voice, speed=beat["speed"], lang=lang)
        
        # Aplica a dinâmica de ganho
        samples = samples * beat["vol"]
        
        # Micro fade-in e fade-out (5ms) para eliminar cliques
        fade_len = min(120, len(samples))
        fade_curve = np.linspace(0, 1, fade_len, dtype=np.float32)
        samples[:fade_len] *= fade_curve
        samples[-fade_len:] *= fade_curve[::-1]

        audio_segments.append(samples)

        # Insere a pausa humana correspondente
        pause_samples = int(SAMPLE_RATE * beat["pause"])
        if pause_samples > 0:
            audio_segments.append(np.zeros(pause_samples, dtype=np.float32))

    if not audio_segments:
        return np.zeros(SAMPLE_RATE, dtype=np.float32), SAMPLE_RATE

    full_audio = np.concatenate(audio_segments)
    return full_audio, SAMPLE_RATE
