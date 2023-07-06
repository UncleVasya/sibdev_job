from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal
from sibdev_job import const


class Customer(models.Model):
    """Модель покупателя"""
    username = models.CharField(max_length=255)
    gems = models.ManyToManyField(
        to='Gem',
        related_name='customers',
        through='Deal'
    )

    def __str__(self):
        return self.username


class Gem(models.Model):
    """Модель драгоценного камня"""
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Deal(models.Model):
    """Модель сделки"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='deals',
    )
    item = models.ForeignKey(
        Gem,
        on_delete=models.CASCADE,
        related_name='deals',
    )
    quantity = models.PositiveIntegerField()
    total_cost = models.DecimalField(
        decimal_places=2,
        max_digits=const.decimal_max_digits,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateTimeField()
