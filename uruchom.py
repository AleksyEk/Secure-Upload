"""Przygotowanie zależności i uruchomienie aplikacji; tylko biblioteka standardowa."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def prepare_environment():
    if sys.version_info < (3, 12):
        raise RuntimeError("Wymagany jest Python 3.12 lub nowszy.")
    if not PYTHON.exists():
        print("Pierwsze uruchomienie: tworzenie srodowiska .venv...", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    check = """
import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
try:
    for line in Path(sys.argv[1]).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, expected = line.split('==', 1)
        if version(name) != expected:
            sys.exit(1)
except PackageNotFoundError:
    sys.exit(1)
"""
    result = subprocess.run([str(PYTHON), "-c", check, str(ROOT / "requirements.txt")], check=False)
    if result.returncode:
        print("Instalowanie bibliotek z requirements.txt (wymagany internet)...", flush=True)
        pip = subprocess.run([str(PYTHON), "-m", "pip", "--version"], capture_output=True)
        if pip.returncode:
            subprocess.run([str(PYTHON), "-m", "ensurepip", "--upgrade"], check=True)
        subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    print("Srodowisko gotowe.", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Przygotowanie i uruchomienie Secure Upload")
    parser.add_argument("--prepare-only", action="store_true", help="Zainstaluj zaleznosci bez uruchamiania serwera")
    args = parser.parse_args()
    try:
        prepare_environment()
        if args.prepare_only:
            return 0
        print("Uruchamianie aplikacji. Zatrzymanie: Ctrl+C w tym oknie.", flush=True)
        process = subprocess.Popen([str(PYTHON), str(ROOT / "app.py"), "--open-browser"], cwd=ROOT)
        try:
            return process.wait()
        except KeyboardInterrupt:
            print("\nZatrzymywanie aplikacji...", flush=True)
            # Na Windowsie Ctrl+C otrzymuje także proces serwera w tym samym oknie.
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            return 0
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()
    except KeyboardInterrupt:
        print("\nPrzerwano przygotowanie aplikacji.")
        return 1
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"Blad: {exc}", file=sys.stderr)
        print("Sprawdz instalacje Pythona, dostep do internetu i uprawnienia do katalogu projektu.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
