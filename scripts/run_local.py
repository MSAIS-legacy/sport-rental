"""Запуск шести отдельных процессов. Остановка: Ctrl+C."""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ["catalog", "inventory", "rental", "customers", "billing", "maintenance"]


def main():
    processes = []
    try:
        for port, name in enumerate(SERVICES, 8001):
            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join(
                [str(ROOT / "services" / name / "src"), str(ROOT / "packages/runtime/src")]
            )
            env["DATABASE_PATH"] = str(ROOT / "data" / f"{name}.sqlite3")
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        f"{name}_service.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    env=env,
                    cwd=ROOT,
                )
            )
            print(f"{name}: http://localhost:{port}/docs", flush=True)
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(f"Сервис остановился: exit code {process.returncode}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
