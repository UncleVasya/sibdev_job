from decimal import Decimal

from faker import Faker

fake = Faker()
Faker.seed(420)


def fake_decimal(right_digits=2, min_value=0.1, max_value=10000) -> Decimal:
    """Генерирует случайное число типа Decimal."""
    num = fake.pyfloat(min_value=min_value, max_value=max_value)
    return Decimal(f'{num:.{right_digits}f}')
