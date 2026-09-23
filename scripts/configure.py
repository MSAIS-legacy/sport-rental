"""Создание локальной конфигурации. Существующие секреты не перезаписываются."""

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = ROOT / ".env"
    if not env.exists():
        content = "\n".join(
            f"{key}={secrets.token_hex(24)}"
            for key in ["POSTGRES_PASSWORD", "RABBITMQ_PASSWORD", "INTERNAL_RPC_TOKEN", "ADMIN_PASSWORD"]
        )
        env.touch(mode=0o600)
        env.write_text(content + "\nADMIN_USERNAME=admin\n")
    print("Локальная конфигурация готова: .env (не добавляйте в Git).")


if __name__ == "__main__":
    main()
