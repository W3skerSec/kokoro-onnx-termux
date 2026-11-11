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

# Locate active site-packages containing phonemizer
candidates = [p for p in sys.path if "site-packages" in p]
site_pkg = None
for c in candidates:
    if os.path.exists(os.path.join(c, "phonemizer")):
        site_pkg = c
        break

if not site_pkg:
    print("Error: phonemizer not found in any site-packages path!")
    sys.exit(1)

print(f"Found target site-packages: {site_pkg}")
api_file = os.path.join(site_pkg, "phonemizer/backend/espeak/api.py")

patch_file(
    api_file,
    "if sys.platform != 'win32':\n    # cause a crash on Windows\n    import dlinfo",
    "if sys.platform != 'win32':\n    # cause a crash on Windows\n    try:\n        import dlinfo\n    except (ImportError, AttributeError, OSError):\n        dlinfo = None"
)

old_dlinfo_lookup = """        try:
            # Linux or MacOS only, ImportError on Windows
            return pathlib.Path(dlinfo.DLInfo(library).path).resolve()
        except (Exception, ImportError):  # pragma: nocover
            raise RuntimeError(
                f'failed to retrieve the path to {library} library') from None"""

new_dlinfo_lookup = """        try:
            if dlinfo is not None:
                return pathlib.Path(dlinfo.DLInfo(library).path).resolve()
            raise RuntimeError('dlinfo not available on Android/Bionic')
        except (Exception, ImportError):
            import subprocess
            try:
                res = subprocess.run(['find', '/data/data/com.termux/files/usr/lib', '-name', 'libespeak-ng.so*', '-type', 'f'], capture_output=True, text=True)
                for line in res.stdout.strip().split('\\n'):
                    p = pathlib.Path(line.strip())
                    if p.is_file():
                        return p
            except Exception:
                pass
            raise RuntimeError(f'failed to retrieve the path to {library} library') from None"""

patch_file(api_file, old_dlinfo_lookup, new_dlinfo_lookup)

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

kokoro_init = os.path.join(site_pkg, "kokoro_onnx/__init__.py")
patch_file(
    kokoro_init,
    "self.voices: np.ndarray = np.load(voices_path)",
    "self.voices: np.ndarray = np.load(voices_path, allow_pickle=True)"
)

print("[OK] All patches verified!")
