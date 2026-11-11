#!/data/data/com.termux/files/usr/bin/python3
"""
Módulo de Dicionário Fonético e Normalização PT-BR para Kokoro TTS
- Substituição fonética inteligente (prioridade por tamanho de termo)
- Detecção e registro automático de palavras fora do vocabulário (OOV / estrangeiras)
- CLI para visualização, adição e geração de relatórios de correção futura
"""

import os
import sys
import json
import re
import datetime
import argparse

USER_DIR = os.path.expanduser("~/.kokoro")
DEFAULT_DICT_PATH = os.path.join(os.path.dirname(__file__), "data", "phonetic_dict.json")
USER_DICT_PATH = os.path.join(USER_DIR, "phonetic_dict.json")
PENDING_WORDS_PATH = os.path.join(USER_DIR, "pending_words.json")

# Palavras comuns em português que têm letras como k/w/y ou padrões normais
COMMON_PT_WORDS = {
    "que", "para", "com", "não", "uma", "mais", "por", "como", "mas",
    "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "quando",
    "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até",
    "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus",
    "quem", "nas", "me", "esse", "eles", "você", "essa", "num", "nem",
    "suas", "meu", "às", "minha", "têm", "numa", "pelos", "elas", "havia",
    "seja", "qual", "será", "nós", "tenho", "lhe", "deles", "essas", "esses",
    "pelas", "este", "dele", "tu", "te", "vocês", "vos", "lhes", "meus",
    "minhas", "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos",
    "nossas", "dela", "delas", "esta", "estes", "estas", "aquele", "aquela",
    "aqueles", "aquelas", "isto", "aquilo", "estou", "está", "estamos",
    "estão", "estive", "esteve", "estivemos", "estiveram", "estava", "estávamos",
    "estavam", "sou", "somos", "são", "era", "éramos", "eram", "fui", "fomos",
    "foram", "aqui", "agora", "hoje", "ontem", "sempre", "nunca", "talvez"
}

def load_phonetic_dict() -> dict:
    combined = {}
    # 1. Carrega o dicionário padrão se existir
    if os.path.exists(DEFAULT_DICT_PATH):
        try:
            with open(DEFAULT_DICT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                combined.update(data.get("substitutions", {}))
        except Exception:
            pass

    # 2. Sobrescreve com o dicionário do usuário em ~/.kokoro/phonetic_dict.json
    if os.path.exists(USER_DICT_PATH):
        try:
            with open(USER_DICT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                combined.update(data.get("substitutions", {}))
        except Exception:
            pass

    return combined

def save_user_dict(substitutions: dict):
    os.makedirs(USER_DIR, exist_ok=True)
    payload = {
        "_meta": {
            "description": "Dicionário Fonético Personalizado do Usuário",
            "updated_at": datetime.datetime.now().isoformat(),
            "language": "pt-br"
        },
        "substitutions": substitutions
    }
    with open(USER_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_pending_words() -> dict:
    if os.path.exists(PENDING_WORDS_PATH):
        try:
            with open(PENDING_WORDS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_pending_words(pending: dict):
    os.makedirs(USER_DIR, exist_ok=True)
    with open(PENDING_WORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)

def is_foreign_or_oov(word: str, current_dict: dict) -> bool:
    """Verifica se uma palavra pode ser estrangeira ou sigla não mapeada."""
    w_clean = re.sub(r'[^a-zA-ZÀ-ÿ]', '', word).strip()
    if not w_clean or len(w_clean) < 2:
        return False

    w_lower = w_clean.lower()
    if w_lower in COMMON_PT_WORDS:
        return False

    # Já está no dicionário fonético (como chave ou como valor fonético já aplicado)?
    for k, v in current_dict.items():
        if k.lower() == w_lower:
            return False
        # Se for parte de uma fonética já traduzida (ex: stóp, póp, didjei, etc)
        if w_lower in v.lower().split():
            return False

    # Critério 1: Contém k, w, y (típicas de palavras em inglês/estrangeiras)
    if re.search(r'[kwy]', w_lower):
        return True

    # Critério 2: Sigla em maiúsculas com 2 ou mais letras
    if w_clean.isupper() and len(w_clean) >= 2:
        return True

    # Critério 3: Padrões consonantais ingleses (ex: stop, track, pop, night, crash)
    if re.search(r'(ck|sh|th|ph|gh|ght|str|spr|sk|sp|st\b|p\b|t\b|k\b|d\b|g\b|b\b)', w_lower):
        # Apenas se não for terminação normal em pt (como r, s, z, l, m)
        if re.search(r'[ptkbdg]$', w_lower):
            return True
        if re.search(r'(ck|th|ph|gh)', w_lower):
            return True

    return False

def record_pending_words(text: str, current_dict: dict):
    """Detecta palavras potencialmente estrangeiras e registra em pending_words.json"""
    words = re.findall(r'\b[A-Za-zÀ-ÿ0-9_-]+\b', text)
    pending = load_pending_words()
    modified = False

    for w in words:
        if is_foreign_or_oov(w, current_dict):
            w_key = w.strip()
            # Ignora se já estiver no dicionário fonético
            if any(k.lower() == w_key.lower() for k in current_dict):
                continue
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if w_key not in pending:
                pending[w_key] = {
                    "word": w_key,
                    "count": 1,
                    "first_seen": now,
                    "last_seen": now,
                    "example_context": text.strip()[:150],
                    "status": "pending_review"
                }
                modified = True
            else:
                pending[w_key]["count"] += 1
                pending[w_key]["last_seen"] = now
                pending[w_key]["example_context"] = text.strip()[:150]
                modified = True

    if modified:
        save_pending_words(pending)

def normalize_text_ptbr(text: str) -> str:
    """Normaliza texto para pronúncia brasileira perfeita no Kokoro TTS."""
    if not text:
        return ""

    phonetic_dict = load_phonetic_dict()

    # 1. Tratar moedas, porcentagens e símbolos
    text = re.sub(r'R\$\s*(\d+)', r'\1 reais', text)
    text = re.sub(r'%', ' por cento', text)

    # 2. Registrar palavras desconhecidas/estrangeiras para revisão futura
    try:
        record_pending_words(text, phonetic_dict)
    except Exception:
        pass

    # 3. Substituições fonéticas por prioridade de tamanho (maiores primeiro)
    # Ex: "Non Stop Pop FM" deve ser substituído antes de "Pop" ou "FM"
    sorted_keys = sorted(phonetic_dict.keys(), key=len, reverse=True)
    for key in sorted_keys:
        repl = phonetic_dict[key]
        # Padrão com limites de palavra
        pattern = r'\b' + re.escape(key) + r'\b'
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 4. Limpeza de espaços antes de pontuação (ex: 'Cara , na' -> 'Cara, na')
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)
    # Remove espaços duplos
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Kokoro Dicionário Fonético PT-BR")
    parser.add_argument("--list", action="store_true", help="Listar todas as substituições fonéticas cadastradas")
    parser.add_argument("--pending", action="store_true", help="Listar palavras pendentes de revisão capturadas nas falas")
    parser.add_argument("--add", nargs=2, metavar=("TERMO", "FONETICA"), help="Adicionar nova pronúncia (ex: --add 'GTA' 'gêtêá')")
    parser.add_argument("--remove", metavar="TERMO", help="Remover termo do dicionário do usuário")
    parser.add_argument("--instructions", action="store_true", help="Gerar instruções formatadas com as palavras pendentes para enviar à IA")
    parser.add_argument("--test", metavar="TEXTO", help="Testar normalização fonética em uma frase")

    args = parser.parse_args()

    if args.list:
        d = load_phonetic_dict()
        print("="*65)
        print(f"📖 DICIONÁRIO FONÉTICO KOKORO ({len(d)} termos cadastrados):")
        print("="*65)
        for k in sorted(d.keys()):
            print(f"  • {k.ljust(22)} ➔  {d[k]}")
        return

    if args.pending:
        p = load_pending_words()
        print("="*65)
        print(f"🔍 PALAVRAS PENDENTES DE REVISÃO ({len(p)} detectadas):")
        print("="*65)
        if not p:
            print("  Nenhuma palavra pendente encontrada!")
            return
        for k, v in sorted(p.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  • {k} (usada {v['count']}x) | Última vez: {v['last_seen']}")
            print(f"    Contexto: \"{v['example_context']}\"")
        return

    if args.add:
        termo, fonetica = args.add
        user_dict = load_phonetic_dict()
        user_dict[termo] = fonetica
        save_user_dict(user_dict)
        # Remove de pending se estiver lá
        p = load_pending_words()
        if termo in p:
            del p[termo]
            save_pending_words(p)
        print(f"✅ Adicionado: '{termo}' ➔ '{fonetica}' no dicionário de ~/.kokoro/phonetic_dict.json")
        return

    if args.remove:
        termo = args.remove
        user_dict = load_phonetic_dict()
        if termo in user_dict:
            del user_dict[termo]
            save_user_dict(user_dict)
            print(f"🗑️ Termo '{termo}' removido do dicionário do usuário.")
        else:
            print(f"Termo '{termo}' não encontrado no dicionário.")
        return

    if args.instructions:
        p = load_pending_words()
        if not p:
            print("Nenhuma palavra pendente para gerar instruções.")
            return
        print("="*65)
        print("📋 INSTRUÇÕES PARA O ASSISTENTE (Copie e envie no chat):")
        print("="*65)
        print("Identifiquei as seguintes palavras com pronúncia potencialmente incorreta:")
        for k, v in sorted(p.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"- Termo: \"{k}\" | Contexto: \"{v['example_context']}\"")
        print("\nPor favor, adicione as pronúncias fonéticas adequadas ao dicionário kokoro-dict.")
        return

    if args.test:
        norm = normalize_text_ptbr(args.test)
        print(f"Original   : {args.test}")
        print(f"Normalizado: {norm}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
