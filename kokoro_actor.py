#!/data/data/com.termux/files/usr/bin/python3
"""
Kokoro Actor Engine - Motor de Prosódia Expressiva e Atuação Humana
Permite dinâmicas naturais de fala:
- Variação de volume (crescendo / decrescendo / intimista)
- Modulação de velocidade e entonação por pontuação (!, ?, ...)
- Pausas respiratórias e dramáticas humanas (substituindo a cadência mecânica plana)
- Suporte a tags expressivas: [pausa=X], [sussurro], [energia]
"""

import os
import sys
import re
import numpy as np
import kokoro_phonetics

SAMPLE_RATE = 24000

def parse_acting_beats(text: str) -> list[dict]:
    """
    Divide o texto em beats expressivos respeitando pontuações e tags especiais.
    """
    # 1. Tratamento de tags explícitas
    text = re.sub(r'\[(pausa|pause)=([0-9.]+)\]', r' <PAUSE:\2> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(sussurro|whisper)\]', r' <WHISPER> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(energia|energy|grito)\]', r' <ENERGY> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(rush|adrenalina|rapido)\]', r' <RUSH> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(tedio|ironia|sarcasmo)\]', r' <CHILL> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(analitica|foco|alerta)\]', r' <ANALYTIC> ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[(direta|calma)\]', r' <DIRECT> ', text, flags=re.IGNORECASE)

    # 2. Divide por limites oracionais expressivos (. ! ? … ou ...)
    raw_parts = re.split(r'([.!?…]+|\.\.\.)', text)
    clauses = []
    for i in range(0, len(raw_parts) - 1, 2):
        c = raw_parts[i].strip()
        p = raw_parts[i+1].strip()
        if c:
            clauses.append((c, p))
    if len(raw_parts) % 2 == 1 and raw_parts[-1].strip():
        clauses.append((raw_parts[-1].strip(), '.'))

    beats = []
    current_modifier = "normal"

    for clause, punct in clauses:
        # Detecta tags embutidas
        if "<WHISPER>" in clause:
            current_modifier = "whisper"
            clause = clause.replace("<WHISPER>", "").strip()
        elif "<ENERGY>" in clause:
            current_modifier = "energy"
            clause = clause.replace("<ENERGY>", "").strip()
        elif "<RUSH>" in clause:
            current_modifier = "rush"
            clause = clause.replace("<RUSH>", "").strip()
        elif "<CHILL>" in clause:
            current_modifier = "chill"
            clause = clause.replace("<CHILL>", "").strip()
        elif "<ANALYTIC>" in clause:
            current_modifier = "analytic"
            clause = clause.replace("<ANALYTIC>", "").strip()
        elif "<DIRECT>" in clause:
            current_modifier = "direct"
            clause = clause.replace("<DIRECT>", "").strip()

        # Checa pausas customizadas
        custom_pause = None
        pause_match = re.search(r'<PAUSE:([0-9.]+)>', clause)
        if pause_match:
            custom_pause = float(pause_match.group(1))
            clause = re.sub(r'<PAUSE:[0-9.]+>', '', clause).strip()

        if not clause:
            if custom_pause is not None:
                beats.append({"type": "pause", "duration": custom_pause})
            continue

        # Regras de prosódia humana baseadas no contexto e pontuação
        if current_modifier == "whisper":
            speed = 0.90
            vol = 0.75
            pause_s = 0.40
            current_modifier = "normal"
        elif current_modifier == "energy":
            speed = 1.10
            vol = 1.25
            pause_s = 0.22
            current_modifier = "normal"
        elif current_modifier == "rush":
            # Movimento forte / Adrenalina: fala rápido, frases curtas e cortadas
            speed = 1.15
            vol = 1.20
            pause_s = 0.16
            current_modifier = "normal"
        elif current_modifier == "chill":
            # Tédio sofisticado / Ironia: cadência aveludada, arrastada e sarcástica
            speed = 0.88
            vol = 0.82
            pause_s = 0.55
            current_modifier = "normal"
        elif current_modifier == "analytic":
            # Armadilha detectada / Analítica: fala devagar, calculada, precisa
            speed = 0.94
            vol = 1.05
            pause_s = 0.35
            current_modifier = "normal"
        elif current_modifier == "direct":
            # Usuário ansioso: pausa longa antes e frase direta sem suavizar
            speed = 0.98
            vol = 1.02
            pause_s = 0.60
            current_modifier = "normal"
        elif '!' in punct:
            # Exclamação: Enérgica, ágil e projetada
            speed = 1.07
            vol = 1.18
            pause_s = 0.22
        elif '?' in punct:
            # Pergunta: Modulação atenta e pausa de resposta
            speed = 1.00
            vol = 1.05
            pause_s = 0.32
        elif '..' in punct or '…' in punct:
            # Reticências: Hesitação dramática, sarcasmo ou pensamento reflexivo
            speed = 0.93
            vol = 0.88
            pause_s = 0.48
        else:
            # Ponto final: Tom narrativo padrão
            speed = 1.02
            vol = 1.00
            pause_s = 0.28

        if custom_pause is not None:
            pause_s = custom_pause

        beats.append({
            "type": "speech",
            "text": clause + punct,
            "speed": speed,
            "vol": vol,
            "pause": pause_s
        })

    return beats

def synthesize_acting(kokoro_engine, text: str, voice, lang: str = "pt-br") -> tuple[np.ndarray, int]:
    """
    Sintetiza o texto aplicando o motor de atuação humana.
    """
    beats = parse_acting_beats(text)
    audio_segments = []

    for idx, beat in enumerate(beats):
        if beat["type"] == "pause":
            pause_samples = int(SAMPLE_RATE * beat["duration"])
            audio_segments.append(np.zeros(pause_samples, dtype=np.float32))
            continue

        raw_text = beat["text"]
        if lang.lower().startswith("pt"):
            clean_text = kokoro_phonetics.normalize_text_ptbr(raw_text)
        else:
            clean_text = raw_text

        # Sintetiza com a velocidade dinâmica do beat
        samples, _ = kokoro_engine.create(clean_text, voice=voice, speed=beat["speed"], lang=lang)
        
        # Aplica dinâmica de ganho de volume (acting volume curve)
        samples = samples * beat["vol"]
        audio_segments.append(samples)

        # Insere a pausa humana correspondente
        pause_samples = int(SAMPLE_RATE * beat["pause"])
        if pause_samples > 0:
            audio_segments.append(np.zeros(pause_samples, dtype=np.float32))

    if not audio_segments:
        return np.zeros(SAMPLE_RATE, dtype=np.float32), SAMPLE_RATE

    full_audio = np.concatenate(audio_segments)
    return full_audio, SAMPLE_RATE
