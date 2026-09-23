"""Создание локальной конфигурации. Существующие секреты не перезаписываются."""

import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

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
    key_dir = ROOT / ".secrets"
    key_dir.mkdir(mode=0o700, exist_ok=True)
    if not (key_dir / "private.pem").exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private = key_dir / "private.pem"
        private.touch(mode=0o600)
        private.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
            )
        )
        (key_dir / "public.pem").write_bytes(
            key.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
    # Родительская папка 0700 защищает ключ на хосте; файл читается
    # непривилегированным пользователем контейнера через Docker secret.
    (key_dir / "private.pem").chmod(0o444)
    print("Локальная конфигурация готова: .env (не добавляйте в Git).")


if __name__ == "__main__":
    main()
