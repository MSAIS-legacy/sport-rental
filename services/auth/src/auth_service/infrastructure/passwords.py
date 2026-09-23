from argon2 import PasswordHasher
from argon2.exceptions import VerificationError


class ArgonHasher:
    def __init__(self):
        self.hasher = PasswordHasher()

    def hash(self, password):
        return self.hasher.hash(password)

    def verify(self, password_hash, password):
        try:
            return self.hasher.verify(password_hash, password)
        except VerificationError:
            return False
