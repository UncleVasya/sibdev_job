import csv
import datetime
import random
from collections import defaultdict
from decimal import Decimal
from io import StringIO
from typing import List
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.response import Response

from app.deals import models
from app.deals.api import const
from app.deals.api.tests.common import Deal
from app.deals.api.tests.factories import (CustomerFactory, DealFactory,
                                           GemFactory)
from app.deals.api.tests.helpers import fake_decimal

fake = Faker()
Faker.seed(42)


@mock.patch('app.deals.api.views.cache.keys',
            mock.Mock(return_value=[]),
            create=True)
class DealsUploadViewTestCase(TestCase):
    """Кейс для проверки загрузки данных о сделках."""
    customers: List[str]
    gems: List[str]
    deals: List[Deal]

    url: str = reverse('deals:deals-upload')

    @classmethod
    def setUpTestData(cls):
        cls.customers = [fake.unique.name() for _ in range(20)]
        cls.gems = [f'gem-{i}' for i in range(20)]
        cls.deals = cls.generate_deals(cls.customers, cls.gems)

    @classmethod
    def generate_deals(cls,
                       customers: List[str],
                       gems: List[str],
                       num: int = 100) -> List[Deal]:
        """Генерирует список сделок по переданным покупателям и камням."""
        return [
            Deal(
                customer=random.choice(customers),
                gem=random.choice(gems),
                total=fake_decimal(),
                quantity=fake.pyint(min_value=1, max_value=100),
                date=fake.unique.date_time(tzinfo=datetime.timezone.utc),
            ) for _ in range(num)
        ]

    def upload_deals(self, deals: List[Deal]) -> Response:
        """Вспомогательный метод для загрузки файла со сделками."""
        data = self.build_csv_data(deals)
        return self.upload_csv_data(data)

    def build_csv_data(self, deals: List[Deal]) -> List[List]:
        """Переводит список сделок в формат, удобный для записи в csv."""
        csv_header = ['customer', 'item', 'total', 'quantity', 'date']
        return [
            csv_header,
            *(deal.to_list() for deal in deals)
        ]

    def upload_csv_data(self, data: List[List]):
        """Загружает данные в виде csv-файла."""
        f = StringIO()
        csv.writer(f).writerows(data)

        data = SimpleUploadedFile(content=f.getvalue().encode('utf-8'), name='deals.csv')
        return self.client.post(self.url, {'deals': data})

    def assert_data_from_deals(self, deals: List[Deal]):
        """
        Функция для проверки соответствия созданных объектов
        загруженным данным по сделкам.
        """
        customers = set(deal.customer for deal in deals)
        gems = set(deal.gem for deal in deals)

        # покупатели
        db_customers = models.Customer.objects.filter(username__in=customers)
        self.assertEqual(len(customers), len(db_customers))

        # камни
        db_gems = models.Gem.objects.filter(name__in=gems)
        self.assertEqual(len(gems), len(db_gems))

        # сделки
        db_deals = models.Deal.objects.filter(
            customer__in=db_customers,
            item__in=db_gems,
            date__in=[deal.date for deal in deals]
        ).select_related('customer', 'item')

        db_deals = [deal.to_list() for deal in db_deals]
        deals = [deal.to_list() for deal in deals]

        for deal in deals:
            self.assertIn(deal, db_deals)

    def test_deals_clean_upload_success(self, ):
        """Проверяет успешную загрузку файла со сделками на чистую базу."""
        models.Customer.objects.all().delete()
        models.Gem.objects.all().delete()
        models.Deal.objects.all().delete()

        response = self.upload_deals(self.deals)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_data_from_deals(self.deals)

    def test_deals_addition_success(self):
        """Проверяет успешную добавление сделок в уже заполненную базу."""
        self.upload_deals(self.deals)
        deals_count = models.Deal.objects.count()

        # добавим новые сделки и проверим общее кол-во записей
        deals = self.generate_deals(self.customers, self.gems, 10)
        self.upload_deals(deals)
        self.assert_data_from_deals(deals)
        self.assertEqual(
            deals_count + len(deals),
            models.Deal.objects.count()
        )

        # загрузим эти же сделки повторно и проверим,
        # что кол-во записей не поменялось
        self.upload_deals(deals)
        self.assert_data_from_deals(deals)
        self.assertEqual(
            deals_count + len(deals),
            models.Deal.objects.count()
        )

    def test_file_is_missing(self):
        """Обращение к api без указания файла."""
        response = self.client.post(self.url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['code'], 'file_missing')

    def test_file_is_empty(self):
        """Попытка загрузить пустой файл."""
        f = StringIO()
        data = SimpleUploadedFile(content=f.read(), name='deals.csv')

        response = self.client.post(self.url, {'deals': data})
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['code'], 'file_empty')

    def test_file_invalid_header(self):
        """Загрузка csv с неправильным названием столбца."""
        data = self.build_csv_data(self.deals)
        data[0][0] = 'Неправильное название столбца.'

        response = self.upload_csv_data(data)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['code'], 'file_corrupt_data')

    def test_file_invalid_data(self):
        """Загрузка csv с испорченными данными."""
        data = self.build_csv_data(self.deals)
        data[1][3] = 'Строка вместо числа.'

        response = self.upload_csv_data(data)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data['code'], 'file_corrupt_data')

    def test_cache_reset_on_new_data(self):
        """
        При загрузке новых данных сбрасывается кеш страниц.

        Проверяем, что:
        - ключи кеша ищутся по известному паттерну;
        - найденные ключи удаляются;
        """
        cache_key_pattern = f'*{const.top_customers_cache_key_prefix}*'

        with (
            mock.patch('app.deals.api.views.cache.keys') as keys_mock,
            mock.patch('app.deals.api.views.cache.delete_many') as delete_mock
        ):
            found_keys = [f'cache-key-{i}' for i in range(5)]
            keys_mock.return_value = found_keys

            self.upload_deals(self.deals)

        keys_mock.assert_called_with(cache_key_pattern)
        delete_mock.assert_called_with(keys=found_keys)


class TopCustomersViewTestCase(TestCase):
    """Кейс для страницы с данными о топовых покупателях."""
    customers: List[models.Customer]
    gems: List[models.Gem]

    url: str = reverse('deals:top-customers')

    @classmethod
    def setUpTestData(cls):
        cls.customers = [CustomerFactory() for _ in range(20)]
        cls.gems = [GemFactory() for _ in range(20)]

    def setUp(self):
        cache.clear()

    def test_customers_order(self):
        """
        Покупатели отротированы по сумме потраченных денег за все время.
        """
        models.Deal.objects.all().delete()

        money_spent = defaultdict(lambda: 0)

        # создадим одинаковые по суммам сделки
        for customer in self.customers:
            cost = Decimal(1000)
            DealFactory(
                customer=customer,
                item=random.choice(self.gems),
                total_cost=cost,
            )
            money_spent[customer.username] += cost

        # некоторым покупателям добавим еще сделки, записывая общую сумму
        additions = [500, 300, 350, 250, 650, 400]
        for i, customer in enumerate(self.customers[:12:2]):
            cost = Decimal(additions[i])
            DealFactory(
                customer=customer,
                item=random.choice(self.gems),
                total_cost=cost,
            )
            money_spent[customer.username] += cost

        # сортируем данные
        money_spent = sorted(money_spent.items(), key=lambda x: -x[1])

        response = self.client.get(self.url)
        data = response.json()['response']

        # проверяем ответ из api
        self.assertEqual(len(data), const.top_customers_limit)
        for customer, expected_data in zip(data, money_spent):
            self.assertEqual(customer['username'], expected_data[0])
            self.assertEqual(Decimal(customer['spent_money']), expected_data[1])

    def test_popular_gems_detection(self):
        """
        В списке камней ползователей должны быть только те камни,
        которые есть минимум у двоих топовых покупателей.
        """
        models.Deal.objects.all().delete()

        gems = [
            GemFactory(name='Сапфир'),
            GemFactory(name='Рубин'),
            GemFactory(name='Аквамарин'),
            GemFactory(name='Кирпич'),
            GemFactory(name='Изумруд'),
            GemFactory(name='Кварц'),
        ]

        # распределим камни по покупателям
        # 7 гномам, 3 эльфам и так далее :)
        for customer in self.customers[:7]:
            DealFactory(
                customer=customer,
                item=gems[0],
                total_cost=1000,
            )
        for customer in self.customers[:3]:
            DealFactory(
                customer=customer,
                item=gems[1],
                total_cost=1000,
            )
        # Аквамарин дадим одному из топов и больше никому.
        DealFactory(
            customer=self.customers[3],
            item=gems[2],
            total_cost=1,
        )
        # Кирпич дадим одному из топов и еще одному не-топу
        DealFactory(
            customer=self.customers[4],
            item=gems[3],
            total_cost=1,
        )
        DealFactory(
            customer=self.customers[7],
            item=gems[3],
            total_cost=1,
        )
        # Изумруд раздадим нескольким не-топам
        for customer in self.customers[7:10]:
            DealFactory(
                customer=customer,
                item=gems[4],
                total_cost=1,
            )
        # Кварц дадим двум топам
        for customer in self.customers[2:4]:
            DealFactory(
                customer=customer,
                item=gems[5],
                total_cost=1,
            )

        # что ожидаем увидеть в итоге
        expected_gems = [
            ['Сапфир', 'Рубин', 'Кварц'],
            ['Сапфир', 'Рубин'],
            ['Сапфир', 'Рубин'],
            ['Сапфир', 'Кварц'],
            ['Сапфир'],
        ]

        # проверяем ответ из api
        response = self.client.get(self.url, params={'limit': 5})
        data = response.json()['response']

        data = [customer['gems'] for customer in data]
        self.assertEqual(data, expected_gems)

    def test_page_cached(self):
        """Данные из api должны кешироваться."""
        models.Deal.objects.all().delete()

        # раздадим камни
        for gem in self.gems[:3]:
            for customer in self.customers[:5]:
                DealFactory(
                    customer=customer,
                    item=gem,
                )

        expected_data = [
            [gem.name for gem in self.gems[:3]]
        ] * 5

        # сверяем первое обращение к api
        response = self.client.get(self.url, params={'limit': 5})
        data = response.json()['response']
        data = [customer['gems'] for customer in data]

        self.assertEqual(data, expected_data)

        # очищаем данные в БД и проверяем, что ответ api не изменился
        models.Deal.objects.all().delete()

        response = self.client.get(self.url, params={'limit': 5})
        data = response.json()['response']
        data = [customer['gems'] for customer in data]

        self.assertEqual(data, expected_data)

        # очищаем кеш и проверяем, что в ответe api теперь свежие данные
        cache.clear()
        empty_data = [[]] * 5

        response = self.client.get(self.url, params={'limit': 5})
        data = response.json()['response']
        data = [customer['gems'] for customer in data]

        self.assertEqual(data, empty_data)
