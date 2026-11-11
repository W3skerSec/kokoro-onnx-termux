import os
import sys
import pathlib

def patch_file(path, old, new):
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if new in content:
        print(f"Already patched: {path}")
        return True
    if old not in content:
        print(f"Warning: target string not found in {path}")
        return False
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully patched: {path}")
    return True

# Locate active site-packages containing phonemizer and kokoro_onnx
candidates = [p for p in sys.path if "site-packages" in p]
site_pkg = None
for c in candidates:
    if os.path.exists(os.path.join(c, "phonemizer")):
        site_pkg = c
        break

if not site_pkg:
    print("Error: phonemizer not found in site-packages!")
    sys.exit(1)

print(f"Target site-packages: {site_pkg}")

# 1. Patch phonemizer api.py for dlinfo bypass
api_file = os.path.join(site_pkg, "phonemizer/backend/espeak/api.py")
patch_file(
    api_file,
    "if sys.platform != 'win32':\n    # cause a crash on Windows\n    import dlinfo",
    "if sys.platform != 'win32':\n    # cause a crash on Windows\n    try:\n        import dlinfo\n    except (ImportError, AttributeError, OSError):\n        dlinfo = None"
)

# 2. Patch phonemizer backends/__init__.py
backends_file = os.path.join(site_pkg, "phonemizer/backend/__init__.py")
old_backends = """from .espeak.espeak import EspeakBackend
from .espeak.mbrola import EspeakMbrolaBackend
from .festival.festival import FestivalBackend
from .segments import SegmentsBackend


BACKENDS = {b.name(): b for b in (
    EspeakBackend, FestivalBackend, SegmentsBackend, EspeakMbrolaBackend)}"""

new_backends = """try:
    from .espeak.espeak import EspeakBackend
except ImportError:
    EspeakBackend = None

try:
    from .espeak.mbrola import EspeakMbrolaBackend
except ImportError:
    EspeakMbrolaBackend = None

try:
    from .festival.festival import FestivalBackend
except ImportError:
    FestivalBackend = None

try:
    from .segments import SegmentsBackend
except ImportError:
    SegmentsBackend = None

BACKENDS = {b.name(): b for b in (
    EspeakBackend, FestivalBackend, SegmentsBackend, EspeakMbrolaBackend) if b is not None}"""
patch_file(backends_file, old_backends, new_backends)

# 3. Patch kokoro_onnx/__init__.py (NumPy 2.x allow_pickle and INT8 float speed input)
kokoro_init = os.path.join(site_pkg, "kokoro_onnx/__init__.py")
patch_file(
    kokoro_init,
    "self.voices: np.ndarray = np.load(voices_path)",
    "self.voices: np.ndarray = np.load(voices_path, allow_pickle=True)"
)
patch_file(
    kokoro_init,
    '"speed": np.array([speed], dtype=np.int32),',
    '"speed": np.array([speed], dtype=np.float32),'
)

# 4. Patch kokoro_onnx/tokenizer.py (Direct Termux espeak-ng paths, zero bad ELF magic error)
tok_file = os.path.join(site_pkg, "kokoro_onnx/tokenizer.py")
old_tok = """        if not espeak_config:
            espeak_config = EspeakConfig()
        if not espeak_config.data_path:
            espeak_config.data_path = espeakng_loader.get_data_path()
        if not espeak_config.lib_path:
            espeak_config.lib_path = espeakng_loader.get_library_path()"""

new_tok = """        if not espeak_config:
            espeak_config = EspeakConfig()

        termux_lib = "/data/data/com.termux/files/usr/lib/libespeak-ng.so"
        termux_data = "/data/data/com.termux/files/usr/share/espeak-ng-data"
        if os.getenv("PHONEMIZER_ESPEAK_LIBRARY"):
            espeak_config.lib_path = os.getenv("PHONEMIZER_ESPEAK_LIBRARY")
        elif os.path.exists(termux_lib):
            espeak_config.lib_path = termux_lib

        if os.getenv("PHONEMIZER_ESPEAK_DATA_DIRECTORY"):
            espeak_config.data_path = os.getenv("PHONEMIZER_ESPEAK_DATA_DIRECTORY")
        elif os.path.exists(termux_data):
            espeak_config.data_path = termux_data

        if not espeak_config.data_path:
            espeak_config.data_path = espeakng_loader.get_data_path()
        if not espeak_config.lib_path:
            espeak_config.lib_path = espeakng_loader.get_library_path()"""
patch_file(tok_file, old_tok, new_tok)

# 5. Patch onnxruntime_validation.py (Suppress Android unsupported platform warning)
ort_valid = os.path.join(site_pkg, "onnxruntime/capi/onnxruntime_validation.py")
patch_file(
    ort_valid,
    'elif __my_system__ == "linux":',
    'elif __my_system__ in ["linux", "android"]:'
)

# 6. Patch kokoro_onnx/tokenizer.py (pt-BR Smart Text Normalizer: Dj -> didjei, FM, MC, GTA, moedas, etc)
old_norm = """    @staticmethod
    def normalize_text(text) -> str:
        return text.strip()"""

new_norm = """    @staticmethod
    def normalize_text(text, lang="en-us") -> str:
        text = text.strip()
        if lang.lower().startswith("pt"):
            import re
            text = re.sub(r'R[\\$]\s*(\d+)', r'\\1 reais', text)
            text = re.sub(r'%', ' por cento', text)
            pt_rules = [
                (r'\\b[Dd][Jj]\\b', 'didjei'),
                (r'\\b[Mm][Cc]\\b', 'emici'),
                (r'\\b[Ff][Mm]\\b', 'éfie-emi'),
                (r'\\bGTA\\s*V\\b', 'gêtêá cinco'),
                (r'\\bGTA\\s*IV\\b', 'gêtêá quatro'),
                (r'\\bGTA\\s*VI\\b', 'gêtêá seis'),
                (r'\\bGTA\\b', 'gêtêá'),
                (r'\\b[Ww][Ii]-?[Ff][Ii]\\b', 'uai-fai'),
                (r'\\b[Bb]luetooth\\b', 'blutúfi'),
                (r'\\b[Yy]ou[Tt]ube\\b', 'iutúbi'),
                (r'\\b[Ww]hats[Aa]pp\\b', 'uatizápi'),
                (r'\\b[Pp]laylist\\b', 'pleilísti'),
                (r'\\b[Pp]odcast\\b', 'podiquésti'),
                (r'\\b[Ff]eat\\.?\\b', 'fíti'),
                (r'\\b[Ff]t\\.?\\b', 'fíti'),
                (r'\\b[Vv]s\\.?\\b', 'vérsus'),
                (r'\\b[Rr]emix\\b', 'remícs'),
                (r'\\b[Ss]how\\b', 'chou'),
                (r'\\b[Ff]eedback\\b', 'fidibéqui'),
                (r'\\b[Ll]ive\\b', 'laivi'),
                (r'\\bDr\\.\\b', 'doutor'),
                (r'\\bDra\\.\\b', 'doutora'),
                (r'\\bSr\\.\\b', 'senhor'),
                (r'\\bSra\\.\\b', 'senhora'),
                (r'\\betc\\.\\b', 'etcétera'),
            ]
            for pattern, repl in pt_rules:
                text = re.sub(pattern, repl, text, flags=re.IGNORECASE if not pattern.startswith(r'\\b[A-Z]') else 0)
            text = re.sub(r'\\s+([,.:;?!])', r'\\1', text)
        return text.strip()"""
patch_file(tok_file, old_norm, new_norm)

patch_file(
    tok_file,
    "text = Tokenizer.normalize_text(text)",
    "text = Tokenizer.normalize_text(text, lang=lang)"
)

print("[OK] All Termux Bionic and Kokoro patches verified!")
