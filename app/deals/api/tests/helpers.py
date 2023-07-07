from decimal import Decimal

from faker import Faker

fake = Faker()
Faker.seed(42)


def fake_decimal(right_digits=2, min_value=0.01, max_value=10000) -> Decimal:
    """Генерирует случайное число типа Decimal."""
    num = fake.pyfloat(
        right_digits=right_digits,
        min_value=min_value,
        max_value=max_value
    )
    return Decimal(str(num))
