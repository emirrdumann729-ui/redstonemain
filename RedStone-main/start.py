"""Create the local Python environment and launch SPHEREview."""
from __future__ import annotations

import hashlib
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
MARKER = VENV / ".sphereview-requirements.sha256"


def _version(command: list[str]) -> tuple[int, int] | None:
    try:
        result = subprocess.run(command + ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10, check=True)
        major, minor = result.stdout.strip().split(".")[:2]
        return int(major), int(minor)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _python312() -> list[str]:
    if sys.version_info[:2] == (3, 12):
        return [sys.executable]
    candidates = ([["py", "-3.12"], ["python3.12"], ["python3"], ["python"]]
                 if os.name != "nt" else [["py", "-3.12"], ["python3.12"], ["python"]])
    for candidate in candidates:
        if _version(candidate) == (3, 12):
            return candidate
    raise RuntimeError(
        "Python 3.12 bulunamadı. Python 3.12'yi python.org/downloads/ adresinden kurup tekrar deneyin."
    )


def _venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _prepare_environment() -> Path:
    base_python = _python312()
    python = _venv_python()
    if not python.exists():
        print("İlk kurulum: yerel Python ortamı hazırlanıyor…", flush=True)
        subprocess.run(base_python + ["-m", "venv", str(VENV)], cwd=ROOT, check=True)

    digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    if not MARKER.exists() or MARKER.read_text(encoding="utf-8").strip() != digest:
        print("Gerekli paketler kuruluyor. İlk kurulum internet hızına bağlı olarak birkaç dakika sürebilir…",
              flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--prefer-binary",
                        "-r", str(REQUIREMENTS)], cwd=ROOT, check=True)
        MARKER.write_text(digest, encoding="utf-8")
    return python


def _available_port(first: int = 8000, last: int = 8020) -> int:
    for port in range(first, last + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("8000–8020 aralığında boş bir yerel bağlantı noktası bulunamadı.")


def _wait_until_ready(port: int, process: subprocess.Popen, timeout: float = 90) -> bool:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://127.0.0.1:{port}/api/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with opener.open(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.3)   # also between non-200 answers, so this never busy-loops
    return False


def _stop(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    process = None
    try:
        python = _prepare_environment()
        port = _available_port()
        url = f"http://127.0.0.1:{port}/"
        print(f"SPHEREview açılıyor: {url}\nKapatmak için bu pencereye dönüp Ctrl+C'ye basın.", flush=True)
        process = subprocess.Popen(
            [str(python), "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port),
             # Per-request access lines (every frame/tile request) only slow the console
             # down; warnings and errors are still printed.
             "--no-access-log",
             # Open NDJSON streams would otherwise keep Ctrl+C waiting indefinitely.
             "--timeout-graceful-shutdown", "3"],
            cwd=ROOT,
        )
        if not _wait_until_ready(port, process):
            code = process.poll()
            if code is None:
                _stop(process)
                raise RuntimeError("Sunucu 90 saniyede hazır olmadı. Üstteki hata mesajlarını kontrol edin.")
            raise RuntimeError(f"Sunucu {code} koduyla kapandı. Üstteki hata mesajlarını kontrol edin.")
        print(f"Hazır: {url}", flush=True)
        webbrowser.open(url)
        process.wait()
        return int(process.returncode or 0)
    except KeyboardInterrupt:
        _stop(process)
        print("\nSPHEREview kapatılıyor.")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        _stop(process)
        print(f"\nSPHEREview başlatılamadı: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
