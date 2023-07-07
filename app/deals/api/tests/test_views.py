import csv
import datetime
import random
from io import StringIO
from typing import List
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.response import Response

from app.deals import models
from app.deals.api.tests.common import Deal
from app.deals.api.tests.helpers import fake_decimal

fake = Faker()
Faker.seed(42)


@mock.patch('app.deals.api.views.cache.keys',
            mock.Mock(return_value=[]),
            create=True)
class DealsUploadTestCase(TestCase):
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
                       num: int = 10) -> List[Deal]:
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
