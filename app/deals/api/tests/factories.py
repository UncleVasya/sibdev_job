import datetime

import factory

from app.deals import models
from app.deals.api.tests.helpers import fake_decimal


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Customer

    username = factory.Faker('name')


class GemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Gem

    name = factory.Sequence(lambda n: f'gem-{n}')


class DealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Deal

    customer = factory.SubFactory(CustomerFactory)
    item = factory.SubFactory(GemFactory)
    quantity = factory.Faker('pyint', min_value=1, max_value=100)
    total_cost = factory.LazyAttribute(lambda x: fake_decimal())
    date = factory.Faker('date_time', tzinfo=datetime.timezone.utc)
