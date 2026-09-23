"""Сервисы на хосте, PostgreSQL/Redis/RabbitMQ из compose.dev.yaml."""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ["catalog", "inventory", "rental", "customers", "billing", "maintenance", "auth"]


def main():
    config = dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    processes = []
    jobs = [
        (
            s,
            [
                sys.executable,
                "-m",
                "uvicorn",
                f"{s}_service.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(p),
            ],
        )
        for p, s in enumerate(SERVICES, 8001)
    ]
    jobs += [(s, [sys.executable, "-m", f"{s}_service.worker"]) for s in ("rental", "inventory", "billing")]
    jobs += [("customers", [sys.executable, "-m", "customers_service.grpc_server"])]
    try:
        for name, command in jobs:
            env = {**os.environ, **config}
            env.update(
                {
                    "PYTHONPATH": os.pathsep.join(
                        [str(ROOT / "services" / name / "src"), str(ROOT / "packages/runtime/src")]
                    ),
                    "DATABASE_URL": f"postgresql+psycopg://{name}:{config['POSTGRES_PASSWORD']}@127.0.0.1:15432/{name}",
                    "REDIS_URL": "redis://127.0.0.1:16379/0",
                    "RABBITMQ_URL": f"amqp://rental:{config['RABBITMQ_PASSWORD']}@127.0.0.1:15673/",
                    "JWT_PUBLIC_KEY_PATH": str(ROOT / ".secrets/public.pem"),
                    "JWT_PRIVATE_KEY_PATH": str(ROOT / ".secrets/private.pem"),
                    "CUSTOMERS_GRPC_ADDRESS": "127.0.0.1:50051",
                    "GRPC_BIND_ADDRESS": "127.0.0.1:50051",
                }
            )
            processes.append(subprocess.Popen(command, env=env, cwd=ROOT))
        print("Swagger: http://localhost:8001/docs … http://localhost:8007/docs", flush=True)
        while True:
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("Один из процессов завершился; проверьте вывод выше")
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
