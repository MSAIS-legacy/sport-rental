class DomainError(Exception):
    """Нарушение бизнес-правила."""


class Conflict(DomainError):
    """Операция конфликтует с текущим состоянием."""


class NotFound(Exception):
    """Агрегат не найден."""
